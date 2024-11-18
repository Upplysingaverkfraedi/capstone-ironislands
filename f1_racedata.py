import sqlite3
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import requests
from bs4 import BeautifulSoup

# Tengjast gagnagrunninum
print("Tengist gagnagrunninum...")
conn = sqlite3.connect('f1db.db')
cursor = conn.cursor()

cursor.execute('''DROP TABLE IF EXISTS f1_race_data''')

# Búa til töflu ef hún er ekki til
print("Býr til töflu í gagnagrunninum...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS f1_race_data (
    race_id INTEGER,
    driver_id TEXT,
    lap INTEGER,
    time_of_day TEXT,
    lap_time TEXT,
    avg_speed REAL,
    stops INTEGER,
    pit_stop_lap INTEGER,
    pit_stop_time TEXT,
    pit_stop_time_sum TEXT
)
''')

# Ökumennirnir sem við höfum áhuga á
drivers_of_interest = ['Lewis Hamilton', 'Max Verstappen']

# 'driver_id' mapping
driver_ids = {
    'Lewis Hamilton': 'lewis-hamilton',
    'Max Verstappen': 'max-verstappen'
}

race_mapping = {
    "Bahrain": 1036,
    "Emilia-Romagna": 1037,
    "Portugal": 1038,
    "Spain": 1039,
    "Monaco": 1040,
    "Azerbaijan": 1041,
    "France": 1042,
    "Styria": 1043,
    "Austria": 1044,
    "Great Britain": 1045,
    "Hungary": 1046,
    "Belgium": 1047,
    "Netherlands": 1048,
    "Italy": 1049,
    "Russia": 1050,
    "Turkey": 1051,
    "United States": 1052,
    "Mexico": 1053,
    "Brazil": 1054,
    "Qatar": 1055,
    "Saudi Arabia": 1056,
    "Abu Dhabi": 1057
}

race_webdriver_mapping = {
    "Bahrain": 1064,
    "Emilia-Romagna": 1065,
    "Portugal": 1066,
    "Spain": 1086,
    "Monaco": 1067,
    "Azerbaijan": 1068,
    "France": 1070,
    "Styria": 1092,
    "Austria": 1071,
    "Great Britain": 1072,
    "Hungary": 1073,
    "Belgium": 1074,
    "Netherlands": 1075,
    "Italy": 1076,
    "Russia": 1077,
    "Turkey": 1078,
    "United States": 1102,
    "Mexico": 1103,
    "Brazil": 1104,
    "Qatar": 1105,
    "Saudi Arabia": 1106,
    "Abu Dhabi": 1107
}
# Búa til tengingu milli þinna race_id og þeirra á vefsíðunni
def build_race_id_mapping(race_mapping, webdriver):
    print("Byggir upp race_id tengingu...")
    final_race_mapping = {}
    for race_name, user_race_id in race_mapping.items():
        for site_race_name, site_race_id in webdriver.items():
            if race_name.lower() == site_race_name.lower():
                final_race_mapping[user_race_id] = {
                    'website_race_id': site_race_id,
                    'race_name_formatted': race_name.replace(" ", "-").lower()
                }
                break
    return final_race_mapping


final_race_mapping = build_race_id_mapping(race_mapping, race_webdriver_mapping)

base_url = 'https://www.formula1.com'

# Setja upp Selenium með Chrome WebDriver
print("Setur upp Selenium...")
options = Options()
options.headless = True
driver = webdriver.Chrome(options=options)

for user_race_id, site_info in final_race_mapping.items():
    website_race_id = site_info['website_race_id']
    race_name_formatted = site_info['race_name_formatted']
    print(f"Fer í keppni með race_id {user_race_id} ({race_name_formatted})...")

    # 'Fastest Laps'
    fastest_laps_url = f'/en/results.html/2021/races/{website_race_id}/{race_name_formatted}/fastest-laps.html'
    full_url = base_url + fastest_laps_url
    print(f"Sækir 'Fastest Laps' töflu frá: {full_url}")
    
    driver.get(full_url)
    time.sleep(3)

    html_content = driver.page_source
    table_pattern = re.compile(r'<table class="f1-table f1-table-with-data w-full">(.+?)</table>', re.DOTALL)
    table_match = table_pattern.search(html_content)

    if table_match:
        print(f"Tafla fannst fyrir 'Fastest Laps' fyrir race_id {user_race_id}.")
        table_html = table_match.group(1)
        row_pattern = re.compile(r'<tr class="(.+?)">(.+?)</tr>', re.DOTALL)
        rows = row_pattern.findall(table_html)

        for row_class, row_html in rows:
            col_pattern = re.compile(r'<td.*?>(.*?)</td>', re.DOTALL)
            cols = col_pattern.findall(row_html)

            if len(cols) >= 6:
                driver_html = cols[2]
                driver_name_pattern = re.compile(r'<span class="max-desktop:hidden">(.+?)</span>.*?<span class="max-tablet:hidden">(.+?)</span>', re.DOTALL)
                driver_name_match = driver_name_pattern.search(driver_html)
                if driver_name_match:
                    first_name = driver_name_match.group(1).strip()
                    last_name = driver_name_match.group(2).strip()
                    driver_full_name = f"{first_name} {last_name}"
                else:
                    driver_full_name = re.sub('<[^<]+?>', '', driver_html).strip()

                if driver_full_name in drivers_of_interest:
                    print(f"Vinnur með gögn fyrir {driver_full_name}...")
                    lap = int(re.sub('<[^<]+?>', '', cols[4]).strip())
                    time_of_day = re.sub('<[^<]+?>', '', cols[5]).strip()
                    lap_time = re.sub('<[^<]+?>', '', cols[6]).strip()
                    avg_speed = float(re.sub('<[^<]+?>', '', cols[7]).strip())

                    cursor.execute('''
                        INSERT INTO f1_race_data (race_id, driver_id, lap, time_of_day, lap_time, avg_speed)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user_race_id, driver_ids[driver_full_name], lap, time_of_day, lap_time, avg_speed))
    else:
        print(f"Engin tafla fannst fyrir 'Fastest Laps' fyrir race_id {user_race_id}.")

    # 'Pit Stop Summary'
    pit_stop_url = f'/en/results.html/2021/races/{website_race_id}/{race_name_formatted}/pit-stop-summary.html'
    full_pit_stop_url = base_url + pit_stop_url
    print(f"Sækir 'Pit Stop Summary' töflu frá: {full_pit_stop_url}")

    driver.get(full_pit_stop_url)
    time.sleep(1)

    html_content = driver.page_source
    table_match = table_pattern.search(html_content)

    if table_match:
        print(f"Tafla fannst fyrir 'Pit Stop Summary' fyrir race_id {user_race_id}.")
        table_html = table_match.group(1)
        rows = row_pattern.findall(table_html)

        for row_class, row_html in rows:
            col_pattern = re.compile(r'<td.*?>(.*?)</td>', re.DOTALL)
            cols = col_pattern.findall(row_html)

            if len(cols) >= 8:
                driver_html = cols[2]
                driver_name_pattern = re.compile(r'<span class="max-desktop:hidden">(.+?)</span>.*?<span class="max-tablet:hidden">(.+?)</span>', re.DOTALL)
                driver_name_match = driver_name_pattern.search(driver_html)
                if driver_name_match:
                    first_name = driver_name_match.group(1).strip()
                    last_name = driver_name_match.group(2).strip()
                    driver_full_name = f"{first_name} {last_name}"
                else:
                    driver_full_name = re.sub('<[^<]+?>', '', driver_html).strip()

                if driver_full_name in drivers_of_interest:
                    stops = int(re.sub('<[^<]+?>', '', cols[0]).strip())
                    pit_stop_lap = int(re.sub('<[^<]+?>', '', cols[4]).strip())
                    pit_stop_time = re.sub('<[^<]+?>', '', cols[6]).strip()
                    pit_stop_time_sum = re.sub('<[^<]+?>', '', cols[7]).strip()

                    cursor.execute('''
                        UPDATE f1_race_data
                        SET stops = ?, pit_stop_lap = ?, pit_stop_time = ?, pit_stop_time_sum = ?
                        WHERE race_id = ? AND driver_id = ?
                    ''', (stops, pit_stop_lap, pit_stop_time, pit_stop_time_sum, user_race_id, driver_ids[driver_full_name]))
    else:
        print(f"Engin tafla fannst fyrir 'Pit Stop Summary' fyrir race_id {user_race_id}.")

print("Lýkur keyrslu og lokar tengingum.")
driver.quit()
conn.commit()
conn.close()
