import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

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

        # Dictionary to store maximum values for each candidate
        max_values = {}

        # First plot all lines
        for candidate in df_pivot.columns:
            color = "red" if candidate == "Donald Trump" else "blue"
            ax.plot(df_pivot.index, df_pivot[candidate], label=candidate, color=color)

            # Store maximum values
            max_value = df_pivot[candidate].max()
            max_timestamp = df_pivot[candidate].idxmax()
            max_values[candidate] = (max_timestamp, max_value)

        # Sort candidates by their maximum values
        sorted_candidates = sorted(max_values.items(), key=lambda x: x[1][1], reverse=True)

        # Ensure plot has enough height for annotations
        max_value_overall = max(v[1] for _, v in max_values.items())
        ax.set_ylim(0, max_value_overall * 1.15)  # Add 15% padding at top

        # Add annotations with smart positioning
        for i, (candidate, (max_timestamp, max_value)) in enumerate(sorted_candidates):
            # Default to right-side annotation
            ha = 'left'
            horiz_offset = 10
            vert_offset = max_value_overall * 0.02 * (i + 1)  # Scale offset with data

            # Only calculate position if we have multiple timestamps
            if len(df_pivot.index) > 1:
                time_position = (max_timestamp - df_pivot.index[0]).total_seconds()
                total_time = (df_pivot.index[-1] - df_pivot.index[0]).total_seconds()

                if total_time > 0 and time_position / total_time > 0.5:
                    # Point is in right half - place annotation to the left
                    ha = 'right'
                    horiz_offset = -10

            ax.annotate(f'↑ {int(max_value):,}',
                         xy=(max_timestamp, max_value),
                         xytext=(horiz_offset, 5),
                         textcoords='offset points',
                         ha=ha,
                         va='bottom')

        # Add difference annotation in the top right corner of the plot with color based on leader
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
