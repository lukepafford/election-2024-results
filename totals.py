import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# Dictionary of electoral votes by state with full state names
electoral_votes = {
    'Alaska': 3, 'Alabama': 9, 'Arkansas': 6, 'Arizona': 11, 'California': 54,
    'Colorado': 10, 'Connecticut': 7, 'District of Columbia': 3, 'Delaware': 3,
    'Florida': 30, 'Georgia': 16, 'Hawaii': 4, 'Iowa': 6, 'Idaho': 4,
    'Illinois': 19, 'Indiana': 11, 'Kansas': 6, 'Kentucky': 8, 'Louisiana': 8,
    'Massachusetts': 11, 'Maryland': 10, 'Maine': 4, 'Michigan': 15,
    'Minnesota': 10, 'Missouri': 10, 'Mississippi': 6, 'Montana': 4,
    'North Carolina': 16, 'North Dakota': 3, 'Nebraska': 5, 'New Hampshire': 4,
    'New Jersey': 14, 'New Mexico': 5, 'Nevada': 6, 'New York': 28, 'Ohio': 17,
    'Oklahoma': 7, 'Oregon': 8, 'Pennsylvania': 19, 'Rhode Island': 4,
    'South Carolina': 9, 'South Dakota': 3, 'Tennessee': 11, 'Texas': 40,
    'Utah': 6, 'Virginia': 13, 'Vermont': 3, 'Washington': 12, 'Wisconsin': 10,
    'West Virginia': 4, 'Wyoming': 3
}

# Connect to the SQLite3 database
conn = sqlite3.connect('election_results.db')

# Get the latest total votes for main candidates
total_votes_query = '''
WITH LatestTimestamps AS (
    SELECT state, MAX(timestamp) as max_timestamp
    FROM results
    GROUP BY state
),
LatestResults AS (
    SELECT r.*
    FROM results r
    INNER JOIN LatestTimestamps lt 
        ON r.state = lt.state 
        AND r.timestamp = lt.max_timestamp
    WHERE r.candidate IN ('Donald Trump', 'Kamala Harris')
)
SELECT 
    COALESCE(candidate, 'Other') as candidate,
    SUM(vote_count) as total_votes,
    SUM(vote_count) * 100.0 / (SELECT SUM(vote_count) FROM LatestResults) as vote_percentage
FROM LatestResults
GROUP BY candidate
ORDER BY 
    CASE 
        WHEN candidate = 'Donald Trump' THEN 1
        WHEN candidate = 'Kamala Harris' THEN 2
        ELSE 3
    END
'''

# Get state winners for electoral vote calculation
state_winners_query = '''
WITH LatestTimestamps AS (
    SELECT state, MAX(timestamp) as max_timestamp
    FROM results
    GROUP BY state
),
LatestResults AS (
    SELECT r.*
    FROM results r
    INNER JOIN LatestTimestamps lt 
        ON r.state = lt.state 
        AND r.timestamp = lt.max_timestamp
    WHERE r.candidate IN ('Donald Trump', 'Kamala Harris')
)
SELECT 
    lr.state,
    lr.candidate,
    lr.vote_count,
    ROW_NUMBER() OVER (PARTITION BY lr.state ORDER BY lr.vote_count DESC) as rank
FROM LatestResults lr
'''

total_votes_df = pd.read_sql_query(total_votes_query, conn)
state_winners_df = pd.read_sql_query(state_winners_query, conn)

# Calculate electoral votes
winners = state_winners_df[state_winners_df['rank'] == 1]
electoral_totals = {
    'Donald Trump': 0,
    'Kamala Harris': 0
}

for _, row in winners.iterrows():
    if row['state'] in electoral_votes:
        electoral_totals[row['candidate']] += electoral_votes[row['state']]

# Calculate the "Other" votes from the percentages
latest_total_query = '''
WITH LatestTimestamps AS (
    SELECT state, MAX(timestamp) as max_timestamp
    FROM results
    GROUP BY state
)
SELECT 
    r.state,
    r.timestamp,
    r.candidate,
    r.vote_count,
    r.vote_pct
FROM results r
INNER JOIN LatestTimestamps lt 
    ON r.state = lt.state 
    AND r.timestamp = lt.max_timestamp
WHERE r.candidate IN ('Donald Trump', 'Kamala Harris')
'''

latest_results = pd.read_sql_query(latest_total_query, conn)
total_votes_by_state = latest_results.groupby('state')['vote_count'].sum()
total_pct_by_state = latest_results.groupby('state')['vote_pct'].sum()
other_votes = sum((100 - pct) * total_votes / 100 
                 for pct, total_votes in zip(total_pct_by_state, total_votes_by_state))

# Create a new DataFrame with all three categories
final_data = pd.DataFrame({
    'candidate': ['Donald Trump', 'Kamala Harris', 'Other'],
    'total_votes': [
        total_votes_df[total_votes_df['candidate'] == 'Donald Trump']['total_votes'].iloc[0],
        total_votes_df[total_votes_df['candidate'] == 'Kamala Harris']['total_votes'].iloc[0],
        other_votes
    ]
})

# Calculate percentages
final_data['vote_percentage'] = (final_data['total_votes'] / final_data['total_votes'].sum()) * 100

# Create the total votes bar chart
plt.figure(figsize=(12, 8))
ax = plt.gca()

colors = {'Donald Trump': 'red', 'Kamala Harris': 'blue', 'Other': 'grey'}

# Create bars for vote counts
bars = ax.bar([i for i in range(len(final_data))], 
              final_data['total_votes'],
              color=[colors[c] for c in final_data['candidate']])

# Add value labels on the bars
for i, bar in enumerate(bars):
    vote_count = final_data.iloc[i]['total_votes']
    percentage = final_data.iloc[i]['vote_percentage']
    
    # Add vote count on top of the bar
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
            f'{int(vote_count):,}',
            ha='center', va='bottom')
    
    # Add percentage in the middle of the bar
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
            f'{percentage:.1f}%',
            ha='center', va='center',
            color='white', fontweight='bold')

plt.title('Latest Total Votes by Candidate Across All States', fontsize=14, fontweight='bold')
ax.set_ylabel('Total Vote Count')
ax.set_xticks([i for i in range(len(final_data))])
ax.set_xticklabels(final_data['candidate'], rotation=45)

plt.tight_layout()
plt.savefig('images/total_counts.svg', dpi=150, bbox_inches='tight', pad_inches=0.5)
plt.close()

# Print debugging information
print("\nState Winners:")
print(winners[['state', 'candidate', 'vote_count']])
print("\nElectoral Totals:")
print(electoral_totals)

# Create the electoral votes bar chart
plt.figure(figsize=(12, 8))
ax = plt.gca()

electoral_data = pd.DataFrame({
    'candidate': ['Donald Trump', 'Kamala Harris'],
    'electoral_votes': [electoral_totals['Donald Trump'], electoral_totals['Kamala Harris']]
})

# Create bars for electoral votes
bars = ax.bar([i for i in range(len(electoral_data))], 
              electoral_data['electoral_votes'],
              color=[colors[c] for c in electoral_data['candidate']])

# Add value labels on the bars
for i, bar in enumerate(bars):
    vote_count = electoral_data.iloc[i]['electoral_votes']
    
    # Add vote count on top of the bar
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
            f'{int(vote_count)}',
            ha='center', va='bottom')
    
    # Add percentage in the middle of the bar
    percentage = (vote_count / 538) * 100  # 538 is total electoral votes
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
            f'{percentage:.1f}%',
            ha='center', va='center',
            color='white', fontweight='bold')

plt.title('Electoral Votes by Candidate', fontsize=14, fontweight='bold')
ax.set_ylabel('Electoral Votes')
ax.set_xticks([i for i in range(len(electoral_data))])
ax.set_xticklabels(electoral_data['candidate'], rotation=45)

# Add a horizontal line at 270 (electoral votes needed to win)
plt.axhline(y=270, color='green', linestyle='--', alpha=0.5)
ax.text(len(electoral_data) - 0.5, 270, '270 votes needed to win', 
        ha='right', va='bottom', color='green')

plt.tight_layout()
plt.savefig('images/electoral_votes.svg', dpi=150, bbox_inches='tight', pad_inches=0.5)
plt.close()


# Close the database connection
conn.close()
