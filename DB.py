import sqlite3
import pandas as pd
import requests
from io import StringIO
import os

# Define the GitHub API URL for the "data" folder and the database name
github_api_url = "https://api.github.com/repos/EkremBayar/Formula-1-App/contents/data"
database_name = "formulan.db"  # Name of your SQLite database

# Connect to SQLite (or create it)
conn = sqlite3.connect(database_name)

# Get the list of CSV files from the GitHub API
response = requests.get(github_api_url)
response.raise_for_status()
files = response.json()

# Loop over all files in the "data" folder
for file in files:
    if file['name'].endswith('.csv'):
        # Construct the raw file URL
        file_url = file['download_url']
        table_name = os.path.splitext(file['name'])[0]  # Use filename without extension as table name

        # Read CSV data into DataFrame
        csv_response = requests.get(file_url)
        csv_response.raise_for_status()
        df = pd.read_csv(StringIO(csv_response.text))

        # Write DataFrame to SQLite table
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"Table '{table_name}' created successfully.")

# Close the database connection
conn.close()
