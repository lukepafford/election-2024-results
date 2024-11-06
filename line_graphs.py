import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
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

        # Plotting
        plt.figure(figsize=(10, 6))
        for candidate in df_pivot.columns:
            color = "red" if candidate == "Donald Trump" else "blue"
            plt.plot(df_pivot.index, df_pivot[candidate], label=candidate, color=color)

        # plt.style({"Donald Trump": "Red", "Kamala Harris": "Blue"})

        plt.title(f'Vote Counts Over Time - {state}')
        plt.xlabel('Timestamp')
        plt.ylabel('Vote Count')
        legend = plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the plot
        plt.savefig(f'{state}_vote_counts.png')
        plt.close()

# Close the database connection
conn.close()

