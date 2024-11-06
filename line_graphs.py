import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# Connect to the SQLite3 database
conn = sqlite3.connect('election_results.db')

# Fetch data for each state and generate a line graph
states_query = "SELECT DISTINCT state FROM results"
states = pd.read_sql_query(states_query, conn)['state'].tolist()

for state in states:
    query = '''
        SELECT timestamp, candidate, vote_count
        FROM results
        WHERE state = ?
        ORDER BY timestamp
    '''
    df = pd.read_sql_query(query, conn, params=(state,))
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    print(f"State: {state}")
    print(df.head())

    # Filter to include only "Donald Trump" and "Kamala Harris"
    df = df[df['candidate'].isin(['Donald Trump', 'Kamala Harris'])]

    # Pivot the data to have candidates as columns
    df_pivot = df.pivot(index='timestamp', columns='candidate', values='vote_count')

    # Remove columns with all NaN values
    df_pivot = df_pivot.dropna(axis=1, how='all')

    if not df_pivot.empty:
        print(f"Generating plot for {state} with data:")
        print(df_pivot.head())

        # Create figure and axis objects with fixed size
        plt.figure(figsize=(12, 8))
        ax = plt.gca()

        # Dictionary to store maximum values and corresponding timestamps for each candidate
        max_values = {}
        timestamp_99_8 = {}

        # First plot all lines
        for candidate in df_pivot.columns:
            color = "red" if candidate == "Donald Trump" else "blue"
            ax.plot(df_pivot.index, df_pivot[candidate], label=candidate, color=color)

            # Store maximum values and calculate 99.8% of the maximum
            max_value = df_pivot[candidate].max()
            threshold_value = 0.998 * max_value
            max_timestamp = df_pivot[candidate].idxmax()
            max_values[candidate] = (max_timestamp, max_value)
            
            # Find the timestamp where the vote count first reaches 99.8% of the maximum value
            timestamp_99_8[candidate] = df_pivot[df_pivot[candidate] >= threshold_value].index[0]

        # Determine the X-axis limits
        non_zero_start = df_pivot[(df_pivot != 0).any(axis=1)].index[0]
        x_min = non_zero_start - timedelta(hours=2)
        
        overall_max_timestamp_99_8 = max(timestamp_99_8.values())
        x_max = overall_max_timestamp_99_8 + timedelta(hours=3)
        
        ax.set_xlim([x_min, x_max])

        # Sort candidates by their maximum values
        sorted_candidates = sorted(max_values.items(), key=lambda x: x[1][1], reverse=True)

        # Difference annotation in the top right corner of the plot with color based on leader
        if len(sorted_candidates) >= 2:
            highest = sorted_candidates[0][1][1]
            second_highest = sorted_candidates[1][1][1]
            leader = sorted_candidates[0][0]  # Name of candidate with highest count
            diff = highest - second_highest

            # Set color based on who's leading
            face_color = "r" if leader == "Donald Trump" else "b"

            # Position difference annotation within plot bounds
            ax.annotate(f'Difference: {int(diff):,}',
                         xy=(0.98, 0.95),
                         xycoords='axes fraction',
                         ha='right',
                         va='top',
                         bbox=dict(boxstyle='round,pad=0.5', facecolor=face_color, alpha=0.5))

        # Use Seaborn to style the plot
        sns.set_style("whitegrid")
        sns.despine(left=True, bottom=True)

        # Set color palette (customize as needed)
        sns.set_palette("husl", n_colors=len(df_pivot.columns))

        # Other style customizations
        plt.grid(alpha=0.7)
        plt.xticks(rotation=45)
        plt.title(f'Vote Counts Over Time - {state}', fontsize=14, fontweight='bold')
        plt.xlabel('Timestamp (EST)', fontsize=12)
        plt.ylabel('Vote Count', fontsize=12)
        plt.legend(loc='upper left', fontsize=10)

        # Explicitly set linear scale for y-axis
        ax.set_yscale('linear')

        # Format x-axis to show full UTC timestamp
        plt.gcf().autofmt_xdate()
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d %I:%M %p EST', tz="EST"))

        # Add padding but limit it
        plt.tight_layout(pad=1.5)

        # Save the plot with reasonable DPI
        plt.savefig(f'images/{state}_vote_counts.svg', dpi=150, bbox_inches='tight', pad_inches=0.5)
        plt.close()

# Close the database connection
conn.close()

