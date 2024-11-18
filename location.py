import sqlite3
import pandas as pd
import requests
import time

# Tengist gagnagrunninum
DB_PATH = "f1db.db"

# Fáum lista yfir race_id, grand_prix_id og circuit_id
def get_race_data():
    print(f"Tenging við gagnagrunn: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT h.race_id, r.grand_prix_id, r.circuit_id
    FROM hamilton_verstappen_all_time_data AS h
    JOIN race AS r ON h.race_id = r.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    print(f"Fann {len(df)} raðir úr gagnagrunninum.")
    return df.drop_duplicates(subset=['race_id'])  # Fjarlægir tvítekningar

# Finna hnit með Nominatim API með villumeðhöndlun
def get_coordinates_nominatim(location_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location_name,  # Nafn staðarins sem þú vilt leita að
        "format": "json",     # JSON skilaformat
        "limit": 1,           # Takmörkun við eina niðurstöðu
        "addressdetails": 1   # Inniheldur upplýsingar um staðsetningu
    }
    
    headers = {
        "User-Agent": "CapstoneIronislands/1.0 (your_email@example.com)"  # Skiptu út með þínu nafn og netfangi
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Athugar fyrir HTTP villur (t.d. 404 eða 500)

        # Athugar hvort svarið er tómt eða inniheldur gögn
        if response.text.strip():  # Sannar ef textinn er ekki tómur
            data = response.json()  # Reynir að afkóða JSON gögnin
            if data:  # Athugar hvort JSON gögnin innihalda upplýsingar
                lat = data[0]["lat"]
                lon = data[0]["lon"]
                return float(lat), float(lon)
            else:
                print(f"No results found for location: {location_name}")
        else:
            print(f"Empty response for location: {location_name}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed for location: {location_name}. Error: {e}")

    return None, None

# Búa til nýja töflu með hnitum, eyða tilraunarför áður
def create_location_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Eyða taflunni ef hún er til
        cursor.execute("DROP TABLE IF EXISTS race_locations")
        # Búa til tafluna aftur með nýjum skilgreiningum
        cursor.execute("""
        CREATE TABLE race_locations (
            race_id INTEGER PRIMARY KEY,
            grand_prix_id TEXT,
            circuit_id TEXT,
            lat REAL,
            lon REAL
        )
        """)
        conn.commit()
        conn.close()
        print("race_locations taflan var búin til eða endurbyggð.")
    except sqlite3.Error as e:
        print(f"An error occurred while creating the table: {e}")

# Setur gögn í töfluna race_locations
def insert_location_data(race_id, grand_prix_id, circuit_id, lat, lon):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
        INSERT OR REPLACE INTO race_locations (race_id, grand_prix_id, circuit_id, lat, lon)
        VALUES (?, ?, ?, ?, ?)
        """, (race_id, grand_prix_id, circuit_id, lat, lon))
        conn.commit()
        conn.close()
        print(f"Successfully inserted/updated race_id {race_id}")
    except sqlite3.Error as e:
        print(f"An error occurred while inserting race_id {race_id}: {e}")

# Aðalforritið
def main():
    # Fáum öll gögn úr töflunni
    race_data = get_race_data()

    # Búa til nýju töfluna ef hún er ekki til, eða endurbyggja hana
    create_location_table()

    # Fara í gegnum hverja röð og finna hnit
    for index, row in race_data.iterrows():
        race_id = row['race_id']
        grand_prix_id = row['grand_prix_id']
        circuit_id = row['circuit_id']

        # Nota circuit_id til að fá hnit með OpenStreetMap Nominatim API
        lat, lon = get_coordinates_nominatim(circuit_id)

        if lat is not None and lon is not None:
            # Setja gögnin inn í nýju töfluna
            insert_location_data(race_id, grand_prix_id, circuit_id, lat, lon)
            print(f"Added race_id {race_id} for circuit {circuit_id} with lat: {lat}, lon: {lon}")
        else:
            print(f"Could not find coordinates for race_id {race_id}, circuit_id {circuit_id}")

        # Bæta við 1 sekúndu töf til að fylgja reglum OpenStreetMap
        time.sleep(1)

    print("Forritið hefur keyrt af sér.")

# Keyra forritið
if __name__ == "__main__":
    main()
