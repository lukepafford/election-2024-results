import json
import sqlite3
import requests
from datetime import datetime, timedelta

# Database setup
db_name = '/Users/lpafford/Documents/election-2024/election_results.db'
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS results (
        timestamp TEXT,
        state TEXT,
        candidate TEXT,
        vote_count INTEGER,
        vote_pct REAL,
        PRIMARY KEY (timestamp, state, candidate)
    )
''')
conn.commit()

# Fetch the JSON data from the URL
url = 'https://s3.amazonaws.com/graphics.axios.com/elex-results-2024/live/2024-11-05/results-president-state-latest.json'
response = requests.get(url)
data = response.json()

# Insert data into the SQLite3 database
for state_data in data:
    timestamp = state_data['lastUpdated']
    state = state_data['stateName']

    # Iterate over the candidates to get their vote counts and percentages
    for candidate in state_data['results'][0]['candidates']:
        if candidate['candidateId'] == "100008":
            continue
        print(candidate)
        candidate_name = f"{candidate['first']} {candidate['last']}"
        vote_count = candidate['voteCount']
        vote_pct = candidate['votePct']
        
        cursor.execute('''
            INSERT OR REPLACE INTO results (timestamp, state, candidate, vote_count, vote_pct)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, state, candidate_name, vote_count, vote_pct))

conn.commit()

# Close the database connection
conn.close()

