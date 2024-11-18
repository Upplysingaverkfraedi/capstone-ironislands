import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('/Users/haatlason/Documents/GitHub/sqlite-greyjoy/capstone-ironislands/f1db.db')
cursor = conn.cursor()

# Drop the existing tables if they exist
cursor.execute("DROP TABLE IF EXISTS hamilton_verstappen_race_data_2021")
cursor.execute("DROP TABLE IF EXISTS hamilton_verstappen_all_time_data")

# Part 1: Create the 2021 table with races where both Hamilton and Verstappen were present
# Step 1: Find race IDs for 2021 where both Lewis Hamilton and Max Verstappen were present
query = '''
    SELECT rd.race_id
    FROM race_data rd
    JOIN race r ON rd.race_id = r.id
    WHERE rd.driver_id IN ('lewis-hamilton', 'max-verstappen') AND r.year = 2021
    GROUP BY rd.race_id
    HAVING COUNT(DISTINCT rd.driver_id) = 2
'''
cursor.execute(query)
race_ids_with_both = [row[0] for row in cursor.fetchall()]

# Step 2: Retrieve records only for Hamilton and Verstappen in 2021 for those race IDs
if race_ids_with_both:
    query = f"""
        SELECT rd.*
        FROM race_data rd
        JOIN race r ON rd.race_id = r.id
        WHERE rd.race_id IN ({','.join(['?'] * len(race_ids_with_both))})
        AND rd.driver_id IN ('lewis-hamilton', 'max-verstappen')
        AND r.year = 2021
    """
    cursor.execute(query, race_ids_with_both)
    records_2021 = cursor.fetchall()

    # Create the 2021 target table and insert records
    cursor.execute('''
        CREATE TABLE hamilton_verstappen_race_data_2021 AS
        SELECT * FROM race_data WHERE 0;
    ''')

    # Insert the 2021 filtered records
    column_count = len(records_2021[0]) if records_2021 else 0
    placeholders = ', '.join(['?'] * column_count)

    if column_count > 0:
        cursor.executemany(f'INSERT INTO hamilton_verstappen_race_data_2021 VALUES ({placeholders})', records_2021)

# Part 2: Create the all-time table for all data of Hamilton and Verstappen
# Retrieve all records for Hamilton and Verstappen
cursor.execute("""
    SELECT * FROM race_data
    WHERE driver_id IN ('lewis-hamilton', 'max-verstappen')
""")
all_time_records = cursor.fetchall()

# Create the all-time data table and insert records
cursor.execute('''
    CREATE TABLE hamilton_verstappen_all_time_data AS
    SELECT * FROM race_data WHERE 0;
''')

# Insert all-time records
column_count_all_time = len(all_time_records[0]) if all_time_records else 0
placeholders_all_time = ', '.join(['?'] * column_count_all_time)

if column_count_all_time > 0:
    cursor.executemany(f'INSERT INTO hamilton_verstappen_all_time_data VALUES ({placeholders_all_time})',
                       all_time_records)

# Commit and close the connection
conn.commit()
conn.close()
