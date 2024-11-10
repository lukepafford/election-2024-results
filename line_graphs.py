import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Connect to the SQLite3 database
conn = sqlite3.connect('election_results.db')


# Rest of the script for line graphs remains the same
states_query = "SELECT DISTINCT state FROM results"
states = pd.read_sql_query(states_query, conn)['state'].tolist()

for state in states:
    query = '''
        SELECT timestamp, candidate, vote_count, vote_pct
        FROM results
        WHERE state = ?
        ORDER BY timestamp
    '''
    df = pd.read_sql_query(query, conn, params=(state,))
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Filter to include only "Donald Trump" and "Kamala Harris"
    main_candidates_df = df[df['candidate'].isin(['Donald Trump', 'Kamala Harris'])]

    # Pivot the data to have candidates as columns for both vote counts and percentages
    votes_pivot = main_candidates_df.pivot(index='timestamp', 
                                         columns='candidate', 
                                         values='vote_count')
    pct_pivot = main_candidates_df.pivot(index='timestamp', 
                                       columns='candidate', 
                                       values='vote_pct')

    # Calculate "Other" percentage (100 - sum of main candidates)
    other_pct = 100 - pct_pivot.sum(axis=1)
    
    # Calculate "Other" vote count based on percentage
    total_votes = votes_pivot.sum(axis=1)
    other_votes = (other_pct * total_votes / 100)

    # Add "Other" to the vote counts
    votes_pivot['Other'] = other_votes

    if not votes_pivot.empty:
        plt.figure(figsize=(12, 8))
        ax = plt.gca()

        # Dictionary to store maximum values and corresponding timestamps for each candidate
        max_values = {}

        # Plot lines for each candidate
        for candidate in votes_pivot.columns:
            color = {"Donald Trump": "red", 
                    "Kamala Harris": "blue", 
                    "Other": "grey"}[candidate]
            
            ax.plot(votes_pivot.index, 
                   votes_pivot[candidate], 
                   label=candidate, 
                   color=color,
                   linestyle='-' if candidate != 'Other' else '--')

            # Store and annotate maximum values
            max_value = votes_pivot[candidate].max()
            max_timestamp = votes_pivot[candidate].idxmax()
            max_values[candidate] = (max_timestamp, max_value)

            # Annotate the maximum value on the plot
            ax.annotate(f'{int(max_value):,}', 
                       xy=(max_timestamp, max_value), 
                       xytext=(5, 5), 
                       textcoords='offset points', 
                       color=color, 
                       fontsize=10, 
                       fontweight='bold',
                       bbox=dict(facecolor='white', alpha=0.7))

        # Calculate and annotate the difference between top two main candidates
        main_candidates = ['Donald Trump', 'Kamala Harris']
        main_max_values = {k: v for k, v in max_values.items() if k in main_candidates}
        sorted_candidates = sorted(main_max_values.items(), key=lambda x: x[1][1], reverse=True)
        
        if len(sorted_candidates) >= 2:
            highest = sorted_candidates[0][1][1]
            second_highest = sorted_candidates[1][1][1]
            leader = sorted_candidates[0][0]
            diff = highest - second_highest

            face_color = "r" if leader == "Donald Trump" else "b"
            
            ax.annotate(f'Difference: {int(diff):,}',
                       xy=(1.05, 0.95),
                       xycoords='axes fraction',
                       ha='left',
                       va='top',
                       bbox=dict(boxstyle='round,pad=0.5', 
                                facecolor=face_color, 
                                alpha=0.5))

        # Style customizations
        sns.set_style("whitegrid")
        sns.despine(left=True, bottom=True)
        plt.grid(alpha=0.7)
        plt.xticks(rotation=45)
        ax.set_yscale('linear')
        plt.gcf().autofmt_xdate()
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d %I:%M %p EST', tz="EST"))

        plt.tight_layout(pad=1.5)

        # Save the plot
        plt.title(f'Vote Counts Over Time - {state}', fontsize=14, fontweight='bold')
        plt.xlabel('Timestamp (EST)', fontsize=12)
        plt.ylabel('Vote Count', fontsize=12)
        plt.legend(loc='upper left', fontsize=10)
        plt.savefig(f'images/{state}_vote_counts.svg', dpi=150, bbox_inches='tight', pad_inches=0.5)
        plt.close()

# Close the database connection
conn.close()
