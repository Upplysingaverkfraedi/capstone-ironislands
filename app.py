import shiny
from shiny import App, render, ui
from pathlib import Path
from shiny.types import ImgData
import pandas as pd
import numpy as np
import sqlite3
from shinywidgets import output_widget, render_widget
import plotly.express as px
import plotly.graph_objects as go
import datetime

# Slóð að gagnagrunni
DB_PATH = 'f1db.db'
con = sqlite3.connect(DB_PATH)

# Settu Mapbox aðgangslykillinn þinn
mapbox_access_token = "pk.eyJ1IjoiYnJ5bmphcjgiLCJhIjoiY20zZzRxcGdtMDB0NDJtczZ1NWQwcGdqcyJ9.R0R4d1jbGxe9ZC0ydvT7gQ"
px.set_mapbox_access_token(mapbox_access_token)


# Stoðfall
def snake_to_title(snake_str):
    components = snake_str.split('_')
    return ' '.join(x.capitalize() for x in components)


# Þrífur tiltekna dálka í DataFrame
def clean_column_data(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"[-.,]", "", regex=True)
    return df


# Vörpun keppnisheita yfir í keppnisauðkenni
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


# Hleður gögn fyrir 2021 keppnistímabilið
def load_2021_season_data():
    # Staðgengill fyrir raunveruleg gögn frá 2021 tímabilinu
    # Fyrir sýnidæmi, notum sýnigögn
    data = pd.DataFrame({
        'Ökumaður': ['Lewis Hamilton', 'Max Verstappen'],
        'Sigur': [8, 10],
        'Verðlaunapallur': [17, 18],
        'Pól': [5, 10],
        'Stig': [387.5, 395.5]
    })
    return data


def get_race_comparison_data(race_id, race):
    query = f"""
    SELECT 
        race_id,
        type,
        position_display_order,
        position_number,
        driver_number,
        driver_id,
        constructor_id,
        engine_manufacturer_id,
        tyre_manufacturer_id,
        race_laps,
        race_time,
        race_gap,
        race_interval,
        race_points,
        race_qualification_position_number,
        race_grid_position_number,
        race_positions_gained,
        race_pit_stops,
        race_fastest_lap,
        race_driver_of_the_day,
        race_grand_slam
    FROM 
        hamilton_verstappen_race_data_2021
    WHERE 
        race_id = {race_id}
        AND type = 'RACE_RESULT'
        AND (driver_id = 'lewis-hamilton' OR driver_id = 'max-verstappen');
    """

    # Tengist gagnagrunninum og sækir gögn
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return None

    # Endurnefna 'position_display_order' í 'position_display_order'
    df.rename(columns={'position_display_order': 'position_display_order'}, inplace=True)

    # Skilgreina dálka sem þarf að þrífa
    columns_to_clean = [
        'position_display_order',
        'race_time',
        'race_gap',
        'race_interval',
        'race_positions_gained',
        'race_pit_stops',
        'race_fastest_lap',
        'race_driver_of_the_day',
        'race_grand_slam'
    ]

    # Þrífa tiltekna dálka
    df = clean_column_data(df, columns_to_clean)

    # Breyta öllum dálkanöfnum úr snake_case í Title Case með bilum
    df.rename(columns=lambda x: snake_to_title(x), inplace=True)

    # Undirbúa gögn fyrir höfuð-á-höfuð töflu
    hamilton_stats = df[df['Driver Id'] == 'lewis-hamilton'].iloc[0]
    verstappen_stats = df[df['Driver Id'] == 'max-verstappen'].iloc[0]

    # Útiloka 'Race Id' og 'Driver Id' dálka
    stats_columns = df.columns.drop(['Race Id', 'Driver Id']).tolist()

    # Breyta tölulegum gildum í strengi til að forðast birtingarvandamál
    hamilton_values = [str(hamilton_stats[col]) for col in stats_columns]
    verstappen_values = [str(verstappen_stats[col]) for col in stats_columns]

    # Búa til samanburðartöflu DataFrame
    comparison_data = {
        "Staða": stats_columns,
        "Lewis Hamilton": hamilton_values,
        "Max Verstappen": verstappen_values
    }
    comparison_df = pd.DataFrame(comparison_data)

    return comparison_df


# Allur-tími samanburður - fall og gagnavinnsla
def get_driver_stats(driver_id):
    conn = sqlite3.connect(DB_PATH)
    query = f"""
    SELECT 
        SUM(race_points) AS total_points,
        COUNT(CASE WHEN race_fastest_lap > 0 THEN 1 END) AS fastest_laps,
        SUM(race_positions_gained) AS positions_gained,
        SUM(race_driver_of_the_day) AS driver_of_the_day_awards,
        SUM(race_grand_slam) AS grand_slams
    FROM hamilton_verstappen_all_time_data
    WHERE driver_id = '{driver_id}'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.iloc[0]


def scale_to_log(data):
    data = data.copy()
    data = np.log(data + 1)  # Bæta 1 til að forðast log(0)
    data['total_points'] = data['total_points'] / 1.9
    data['grand_slams'] = data['grand_slams'] * 2
    data['driver_of_the_day_awards'] = data['driver_of_the_day_awards'] * 1.2
    data['fastest_laps'] = data['fastest_laps'] * 1.1
    data['grand_slams'] = data['grand_slams'] * 1.2
    data['positions_gained'] = data['positions_gained'] * 0.9
    return data


# Sækja tölfræði fyrir Hamilton og Verstappen
hamilton_original = get_driver_stats("lewis-hamilton")
verstappen_original = get_driver_stats("max-verstappen")

# Stilla gögn fyrir grafið
hamilton_values_scaled = scale_to_log(hamilton_original)
verstappen_values_scaled = scale_to_log(verstappen_original)

categories = ['Total Points', 'Fastest Laps', 'Positions Gained', 'Driver of the Day Awards', 'Grand Slams']
categoriesSpider = ['Total Points', 'Fastest Laps', 'Positions Gained', 'Driver of the Day Awards', 'Grand Slams']

# Finna vísitölur fyrir flokkana í categoriesSpider
indices = [categories.index(cat) for cat in categoriesSpider]


# Búa til kóngulógraf með stilltum gildum og upprunalegum hover texta
def create_spider_chart():
    categories = categoriesSpider

    fig = go.Figure()

    # Gögn fyrir Hamilton með sérsniðnum hover texta sem sýnir óstilluð gildi
    fig.add_trace(go.Scatterpolar(
        r=hamilton_values_scaled,
        theta=categories,
        fill='toself',
        name='Lewis Hamilton',
        hoverinfo='text',
        hovertext=[f'{cat}: {val}' for cat, val in zip(categories, hamilton_original)]
    ))

    # Gögn fyrir Verstappen með sérsniðnum hover texta sem sýnir óstilluð gildi
    fig.add_trace(go.Scatterpolar(
        r=verstappen_values_scaled,
        theta=categories,
        fill='toself',
        name='Max Verstappen',
        hoverinfo='text',
        hovertext=[f'{cat}: {val}' for cat, val in zip(categories, verstappen_original)]
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="#f9f9f9",  # Ljós bakgrunnur í polar plot
            angularaxis=dict(
                tickfont=dict(size=14, color="black"),  # Stærri og dekkri texti fyrir flokka
                linewidth=2,  # Dekkri línur fyrir flokka
                linecolor="black",  # Svartar línur frá miðju í flokka
                ticks='outside',  # Ticks utan á ásnum
                ticklen=5  # Lengd ticks
            ),
            radialaxis=dict(
                showticklabels=False,  # Fjarlægir tölur á radial ásnum
                gridcolor="lightgray",  # Minna áberandi netlínur
                gridwidth=0.8,  # Þynnri netlínur
                linecolor="gray",  # Minna áberandi radial ás
                linewidth=0.8  # Þynnri radial línur
            )
        ),
        showlegend=True,
        legend=dict(
            font=dict(size=12),
            orientation="h",
            yanchor="bottom",
            y=1.1,
            xanchor="center",
            x=0.5
        ),
        template="plotly_white"
    )

    return fig


def get_points_progression(driver_id):
    conn = sqlite3.connect(DB_PATH)
    query = f"""
    SELECT race_id, race_points
    FROM hamilton_verstappen_all_time_data
    WHERE driver_id = '{driver_id}'
    ORDER BY race_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    # Reikna uppsöfnuð stig
    df['cumulative_points'] = df['race_points'].cumsum()
    df['career_race'] = range(1, len(df) + 1)
    # Telja sigra (gera ráð fyrir að 25 eða fleiri stig séu sigur)
    wins = df[df['race_points'] >= 25].shape[0]
    return df, wins


# Sækja stigþróun fyrir Hamilton og Verstappen
hamilton_points_progression, hamilton_wins = get_points_progression("lewis-hamilton")
verstappen_points_progression, verstappen_wins = get_points_progression("max-verstappen")


def create_points_progression_chart(x_axis='career_race'):
    fig = go.Figure()

    # Gögn fyrir Hamilton
    fig.add_trace(go.Scatter(
        x=hamilton_points_progression[x_axis],
        y=hamilton_points_progression['cumulative_points'],
        mode='lines+markers',
        line=dict(shape='spline', smoothing=1.3, width=3, color='blue'),
        name='Lewis Hamilton',
        hoverinfo='text',
        hovertext=[f"Keppni {race}: {points} stig, Uppsöfnuð: {cumulative} stig"
                   for race, points, cumulative in zip(
                hamilton_points_progression[x_axis],
                hamilton_points_progression['race_points'],
                hamilton_points_progression['cumulative_points'])]
    ))

    # Merkja sigurkeppnir Hamilton
    hamilton_winning_races = hamilton_points_progression[hamilton_points_progression['race_points'] >= 25]
    fig.add_trace(go.Scatter(
        x=hamilton_winning_races[x_axis],
        y=hamilton_winning_races['cumulative_points'],
        mode='markers',
        marker=dict(color='gold', size=5, symbol='star'),
        name='Sigur Hamilton',
        hoverinfo='text',
        hovertext=[f"Keppni {race}: {points} stig, Uppsöfnuð: {cumulative} stig"
                   for race, points, cumulative in zip(
                hamilton_winning_races[x_axis],
                hamilton_winning_races['race_points'],
                hamilton_winning_races['cumulative_points'])]
    ))

    # Gögn fyrir Verstappen
    fig.add_trace(go.Scatter(
        x=verstappen_points_progression[x_axis],
        y=verstappen_points_progression['cumulative_points'],
        mode='lines+markers',
        line=dict(shape='spline', smoothing=1.3, width=3, color='red'),
        name='Max Verstappen',
        hoverinfo='text',
        hovertext=[f"Keppni {race}: {points} stig, Uppsöfnuð: {cumulative} stig"
                   for race, points, cumulative in zip(
                verstappen_points_progression[x_axis],
                verstappen_points_progression['race_points'],
                verstappen_points_progression['cumulative_points'])]
    ))

    # Merkja sigurkeppnir Verstappen
    verstappen_winning_races = verstappen_points_progression[verstappen_points_progression['race_points'] >= 25]
    fig.add_trace(go.Scatter(
        x=verstappen_winning_races[x_axis],
        y=verstappen_winning_races['cumulative_points'],
        mode='markers',
        marker=dict(color='silver', size=5, symbol='star'),
        name='Sigur Verstappen',
        hoverinfo='text',
        hovertext=[f"Keppni {race}: {points} stig, Uppsöfnuð: {cumulative} stig"
                   for race, points, cumulative in zip(
                verstappen_winning_races[x_axis],
                verstappen_winning_races['race_points'],
                verstappen_winning_races['cumulative_points'])]
    ))

    # Uppfærsla á útliti
    fig.update_layout(
        title="Stigaþróun Yfir Tíma með Merktum Sigurkeppnum",
        xaxis=dict(
            title="Keppnisnúmer á ferli" if x_axis == 'career_race' else "Keppnisauðkenni",
            showgrid=True
        ),
        yaxis=dict(
            title="Uppsöfnuð Stig",
            showgrid=True
        ),
        legend_title="Ökumaður",
        template="plotly_white",
        showlegend=True
    )

    return fig


def get_fastest_lap_data():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT race_id, driver_id, fastest_lap_time_millis
    FROM hamilton_verstappen_all_time_data
    WHERE fastest_lap_time_millis IS NOT NULL
    ORDER BY race_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def prepare_heatmap_data(df):
    # Nota pivot_table með mean til að meðhöndla afrit
    heatmap_data = df.pivot_table(
        index="driver_id",
        columns="race_id",
        values="fastest_lap_time_millis",
        aggfunc='mean'
    )
    heatmap_data = heatmap_data.fillna(0)
    return heatmap_data


def create_fastest_lap_heatmap():
    # Undirbúa gögn
    fastest_lap_data = get_fastest_lap_data()
    heatmap_data = prepare_heatmap_data(fastest_lap_data)
    drivers = heatmap_data.index.tolist()
    races = heatmap_data.columns.tolist()
    z_values = heatmap_data.values

    # Búa til hita kort
    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=races,
        y=drivers,
        colorscale='Plasma',
        colorbar=dict(title="Hraðasti Hringur (ms)")
    ))

    fig.update_layout(
        title=dict(text="Hraðasti Hringur per Keppni"),
        xaxis=dict(title="Keppnisauðkenni"),
        yaxis=dict(title="Ökumaður")
    )

    return fig


def get_location_and_performance_data():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        l.race_id,
        l.grand_prix_id, 
        l.circuit_id, 
        l.lat, 
        l.lon, 
        p.driver_id, 
        p.race_points 
    FROM race_locations AS l
    JOIN hamilton_verstappen_all_time_data AS p ON l.race_id = p.race_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    # Fylla upp í NaN gildi í race_points með 0
    df['race_points'] = df['race_points'].fillna(0)
    return df


def get_location_and_performance_data_2021():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        l.race_id,
        l.grand_prix_id, 
        l.circuit_id, 
        l.lat, 
        l.lon, 
        p.driver_id, 
        p.race_points 
    FROM race_locations AS l
    JOIN hamilton_verstappen_race_data_2021 AS p ON l.race_id = p.race_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    # Fylla upp í NaN gildi í race_points með 0
    df['race_points'] = df['race_points'].fillna(0)
    return df


location_performance_data = get_location_and_performance_data()
location_performance_data_2021 = get_location_and_performance_data_2021()


def get_average_points(data):
    avg_data = data.groupby(['circuit_id', 'lat', 'lon', 'driver_id']).race_points.mean().reset_index()
    avg_data.rename(columns={'race_points': 'avg_points'}, inplace=True)
    return avg_data


def create_performance_map(data):
    data = get_average_points(data)

    # Tryggja að gögn hafi ekki vantar gildi í nauðsynlegum dálkum
    data = data.dropna(subset=['lat', 'lon', 'avg_points'])

    fig = px.scatter_mapbox(
        data,
        lat="lat",
        lon="lon",
        color="driver_id",
        size="avg_points",
        hover_name="circuit_id",
        hover_data={
            "driver_id": True,
            "avg_points": True,
            "lat": False,
            "lon": False
        },
        title="Meðal Frammistaða eftir Staðsetningu fyrir Hamilton og Verstappen",
        labels={"driver_id": "Ökumaður", "avg_points": "Meðal Stig"},
        mapbox_style="light",
        zoom=1,
        height=600
    )

    # Uppfæra layout með réttum aðgangslykli
    fig.update_layout(mapbox_accesstoken=mapbox_access_token)
    return fig


def create_performance_map_with_race_points(data):
    # Fjarlægja línur með vantar breytur í nauðsynlegum dálkum
    data = data.dropna(subset=['lat', 'lon', 'race_points'])

    fig = px.scatter_mapbox(
        data,
        lat="lat",
        lon="lon",
        color="driver_id",
        size="race_points",
        hover_name="circuit_id",
        hover_data={
            "driver_id": True,
            "race_points": True,
            "lat": False,
            "lon": False
        },
        title="Stig í Keppni eftir Staðsetningu fyrir Hamilton og Verstappen",
        labels={"driver_id": "Ökumaður", "race_points": "Stig í Keppni"},
        mapbox_style="light",
        zoom=1,
        height=600
    )

    # Uppfæra layout með aðgangslykli og kortastíl
    fig.update_layout(mapbox_accesstoken=mapbox_access_token)
    return fig


# Búa til valmöguleika fyrir framleiðanda flokka
manufacturer_choices = {
    "Vélaframleiðandi": "engine_manufacturer_id",
    "Dekkjaframleiðandi": "tyre_manufacturer_id",
    "Lið": "constructor_id"
}


# Sækja upplýsingar um hringi og vegalengd úr gagnagrunninum
def get_race_details(race_name):
    race_id = race_mapping.get(race_name)
    if not race_id:
        return None

    query = f"""
    SELECT laps, distance
    FROM race
    WHERE id = {race_id}
    """
    conn = sqlite3.connect(DB_PATH)
    result = pd.read_sql_query(query, conn)
    conn.close()

    if result.empty:
        return None

    return result.iloc[0].to_dict()


def get_race_points(race_name):
    race_id = race_mapping.get(race_name)
    query = f"""
    SELECT driver_id, race_points
    FROM hamilton_verstappen_race_data_2021
    WHERE race_id = {race_id} AND type = 'RACE_RESULT'
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def convert_time_to_seconds(time_str):
    if time_str is None:
        return None
    try:
        t = datetime.datetime.strptime(time_str, "%H:%M:%S.%f")
        return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1e6
    except ValueError:
        return None


def convert_lap_time_to_seconds(lap_time_str):
    try:
        minutes, seconds = lap_time_str.split(":")
        return int(minutes) * 60 + float(seconds)
    except (ValueError, TypeError):
        return None


def convert_time_to_seconds_2(time_str):
    try:
        if ":" in time_str:
            minutes, seconds = time_str.split(":")
            return int(minutes) * 60 + float(seconds)
        else:
            return float(time_str)
    except (ValueError, TypeError):
        return None


# Skilgreina UI
app_ui = ui.page_fluid(
    # Haus með F1 merki, myndum og titli, með rauðum bakgrunni og hvítum titli
    ui.div(
        ui.row(
            # Mynd af Hamilton til vinstri
            ui.column(
                3,
                ui.div(
                    ui.output_image("hamilton_image"),
                    style="text-align:center; margin: 0; padding: 0; height: 200px"
                )
            ),
            # F1 Merki í miðjunni
            ui.column(
                6,
                ui.div(
                    ui.output_image("f1logo_image"),
                    style="text-align:center; margin: 0; padding: 0; height: 120px"
                )
            ),
            # Mynd af Verstappen til hægri
            ui.column(
                3,
                ui.div(
                    ui.output_image("verstappen_image"),
                    style="text-align:center; margin: 0; padding: 0; height: 200px"
                )
            ),
            # Stíll fyrir röð til að miðja myndir og merki
            style="display: flex; align-items: center; justify-content: center; margin-bottom: 0;"
        ),
        # Titill miðjaður undir myndum og merki
        ui.div(
            ui.h2(
                "Lewis Hamilton VS Max Verstappen",
                style="margin: -15px; padding: 0; font-size: 28px; color: white; font-family: Monaco, monospace; text-align: center;"
            ),
            style="margin-top: 0;"
        ),
        # Setja rauðan bakgrunnslit og fasta hæð fyrir haus
        style="background-color: red; color: white; height: 220px;"
    ),
    # Flipa til að skipuleggja efni með ui.navset_tab og ui.nav_panel
    ui.navset_tab(
        ui.nav_panel(
            "Samanburður yfir allan ferilinn",
            ui.h2("Yfirlit Lewis Hamilton vs Max Verstappen"),
            ui.layout_sidebar(
                # Hliðarvalmynd fyrir valkosti
                ui.sidebar(
                    ui.input_radio_buttons(
                        "x_axis_radio",
                        ui.h4("Veldu X-ás"),
                        choices={"career_race": "Keppnisnúmer á ferli", "race_id": "Keppnisauðkenni"},
                        selected="career_race"
                    )
                ),
                ui.page_fillable(
                    ui.layout_columns(
                        ui.card(
                            output_widget("wins_bar_chart")
                        ),
                        ui.card(
                            output_widget("points_progression_chart")
                        ),
                        ui.card(
                            output_widget("performance_map_1")
                        ),
                        ui.card("Samanburður á Lewis Hamilton og Max Verstappen",
                                output_widget("spider_chart")
                                ),
                        ui.card(
                            output_widget("fastest_lap_heatmap")
                        ),
                        col_widths=[4, 8, 8, 4, 12],
                    )
                )
            ),
        ),
        ui.nav_panel(
            "Samanburður á 2021 Tímabili",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_select(
                        "race_select",
                        "Veldu Keppni:",
                        choices=["2021 Season Overview"] + list(race_mapping.keys()),
                        selected="2021 Season Overview"
                    ),
                ),
                # Aðal efnis svæði sem uppfærist miðað við valda keppni
                ui.div(
                    ui.output_ui("race_content")
                )
            )
        ),
        ui.nav_panel(
            "Framleiðenda Frammistaða",
            ui.input_select("manufacturer_type", "Veldu Flokk", choices=list(manufacturer_choices.keys())),
            output_widget("manufacturer_average_points_plot"),
            output_widget("manufacturer_total_points_plot")
        )
    )
)


# Skilgreina Server Logic
def server(input, output, session):
    # Hlaða 2021 tímabils yfirlitsgögnum
    data = load_2021_season_data()

    # Snúa töflunni
    transposed_data = data.set_index("Ökumaður").transpose()

    # Birta mynd af Hamilton
    @output
    @render.image
    def hamilton_image():
        img_path = Path(__file__).parent / "www" / "hamilton.jpeg"
        if img_path.exists():
            img: ImgData = {
                "src": str(img_path),
                "width": "200px",
                "height": "200px",
                "style": "border:5px solid Turquoise;"
            }
            return img
        else:
            return {
                "src": "",
                "alt": "Mynd af Lewis Hamilton fannst ekki."
            }

    # Birta mynd af Verstappen
    @output
    @render.image
    def verstappen_image():
        img_path = Path(__file__).parent / "www" / "verstappen.jpeg"
        if img_path.exists():
            img: ImgData = {
                "src": str(img_path),
                "width": "200px",
                "height": "200px",
                "style": "border:5px solid blue;"
            }
            return img
        else:
            return {
                "src": "",
                "alt": "Mynd af Max Verstappen fannst ekki."
            }

    # Birta F1 merki mynd
    @output
    @render.image
    def f1logo_image():
        img_path = Path(__file__).parent / "www" / "f1logo.png"
        if img_path.exists():
            img: ImgData = {
                "src": str(img_path),
                "width": "120px",
                "height": "120px",
                "style": "border:2px solid white;"
            }
            return img
        else:
            return {
                "src": "",
                "alt": "F1 Merki mynd fannst ekki."
            }

    # Úttök fyrir "Samanburður yfir allan ferilinn" flipann
    @output
    @render_widget
    def spider_chart():
        return create_spider_chart()

    @output
    @render_widget
    def points_progression_chart():
        x_axis_choice = input.x_axis_radio()
        return create_points_progression_chart(x_axis=x_axis_choice)

    @output
    @render_widget
    def fastest_lap_heatmap():
        return create_fastest_lap_heatmap()

    @output
    @render_widget
    def performance_map_1():
        return create_performance_map(location_performance_data)

    @output
    @render_widget
    def performance_map_3():
        return create_performance_map(location_performance_data_2021)

    @output
    @render_widget
    def performance_map_2():
        race = input.race_select()

        # Athuga hvort valin keppni sé í race_mapping
        if race in race_mapping:
            race_id = race_mapping[race]

            # Sía gögnin fyrir valda keppnina
            filtered_data = location_performance_data_2021[location_performance_data_2021['race_id'] == race_id]

            # Athuga hvort síuð gögn séu til
            if not filtered_data.empty:
                return create_performance_map_with_race_points(filtered_data)
            else:
                # Skila tómu korti eða skilaboðum ef engin gögn eru til
                fig = px.scatter_mapbox(
                    [],
                    lat=[],
                    lon=[],
                    mapbox_style="light",
                    title=f"Engar upplýsingar fyrir {race}",
                    height=600
                )
                return fig
        else:
            # Skila tómu korti eða skilaboðum ef valin keppni finnst ekki
            fig = px.scatter_mapbox(
                [],
                lat=[],
                lon=[],
                mapbox_style="light",
                title="Valin keppni er ekki gild.",
                height=600
            )
            return fig

    # Reactive úttak fyrir keppnisefni í "Samanburður á 2021 Tímabili" flipanum
    @output
    @render.ui
    def race_content():
        race = input.race_select()
        if race == "2021 Season Overview":
            # Birta ökumannatölfræðitöflu ásamt myndum og titli
            return ui.TagList(
                # Samþættur titill og 3D módel
                ui.page_fluid(
                    # Miðjaður titill
                    ui.tags.div(
                        ui.h2("Keppnisbílar Lewis Hamilton og Max Verstappen"),
                        style="text-align: center; font-family: Monaco, monospace; margin-top: 20px;"
                    ),
                    # Röð fyrir tvö 3D módel og þeirra skýringar
                    ui.row(
                        # Dálkur fyrir bíl Lewis Hamilton
                        ui.column(
                            6,
                            ui.div(
                                ui.h3("Bíll Lewis Hamilton - Mercedes Benz W12"),
                                style="text-align: center; font-family: Monaco, monospace; font-size: 12px; margin-top: 10px;"
                            ),
                            ui.tags.div(
                                ui.tags.iframe(
                                    title="Mercedes AMG F1 W12 E Performance 2021",
                                    src="https://sketchfab.com/models/e586353e96384dd6a306db3dd56ae7ea/embed",
                                    frameborder="0",
                                    allow="autoplay; fullscreen; xr-spatial-tracking",
                                    mozallowfullscreen="true",
                                    webkitallowfullscreen="true",
                                    width="100%",
                                    height="400px"
                                ),
                                style="text-align: center;"
                            )
                        ),
                        # Dálkur fyrir bíl Max Verstappen
                        ui.column(
                            6,
                            ui.div(
                                ui.h3("Bíll Max Verstappen - Honda RB16B"),
                                style="text-align: center; font-family: Monaco, monospace; font-size: 12px; margin-top: 10px;"
                            ),
                            ui.tags.div(
                                ui.tags.iframe(
                                    title="Red Bull Racing F1 Car - RB16B 2021 Season",
                                    src="https://sketchfab.com/models/3c76346ee84242099675f4de8cbbd587/embed",
                                    frameborder="0",
                                    allow="autoplay; fullscreen; xr-spatial-tracking",
                                    mozallowfullscreen="true",
                                    webkitallowfullscreen="true",
                                    width="100%",
                                    height="400px"
                                ),
                                style="text-align: center;"
                            )
                        )
                    ),
                    # Stíll fyrir heildarkaflann
                    style="margin-bottom: 30px;"
                ),
                # Ökumannatölfræðitafla
                ui.h3("Yfirlit 2021 Tímabils"),
                ui.layout_columns(
                    ui.card(output_widget("vertical_points_chart")),
                    ui.card(output_widget("hamilton_verstappen_cumulative_plot")),
                    ui.card(output_widget("hamilton_verstappen_position_plot")),
                    ui.card(output_widget("horizontal_bar_chart")),
                    ui.card(output_widget("performance_map_3")),
                    col_widths=[4, 8, 6, 6, 12]
                )
            )
        else:
            race_details = get_race_details(race)
            if not race_details:
                race_details_text = "Engar upplýsingar til um þessa keppni."
            else:
                race_details_text = f"""
                Hringir: {race_details['laps']}<br>
                Vegalengd: {race_details['distance']} km
                """

            return ui.TagList(
                ui.h3(f"Höfuð-á-Höfuð Samanburður fyrir {race}"),
                ui.layout_columns(
                    ui.card(
                        ui.layout_columns(ui.card(
                            ui.output_image("track_image")),
                            ui.card(
                                ui.div(
                                    ui.h4("Upplýsingar um Keppni"),
                                    ui.HTML(race_details_text),
                                    style="text-align: left; padding: 10px;"
                                )
                            ),
                            col_widths=[12, 6]
                        )
                    ),
                    ui.card(
                        ui.h4("Höfuð-á-Höfuð Samanburður"),
                        output_widget("performance_map_2")
                    ),
                    ui.card(output_widget("horizontal_pit_stop_comparison_chart")),
                    ui.card(output_widget("vertical_comparison_barplot")),
                    ui.card(output_widget("horizontal_race_time_comparison_chart")),
                    ui.card(output_widget("start_vs_finish_positions_chart")),
                    ui.card(output_widget("fastest_lap_chart")),
                    ui.card(output_widget("positions_gained_bar_chart")),
                    col_widths=[8, 4, 4, 8, 6, 6, 6, 6]
                ),
            )

    # Birta ökumannatölfræðitöflu
    @output
    @render.table
    def driver_table():
        # Fyrir sýnidæmi, skila sýnigögnum
        return transposed_data

    # Sýna lárétt súlurit
    @output
    @render_widget
    def horizontal_bar_chart():
        # Snúa gögnunum án 'Stig'
        melted_data = data.drop(columns=["Stig"]).melt(
            id_vars=["Ökumaður"], var_name="Mæling", value_name="Gildi"
        )

        # Plotly súlurit
        fig = go.Figure()

        # Bæta við súlum fyrir hvern ökumann
        for driver in data["Ökumaður"]:
            driver_data = melted_data[melted_data["Ökumaður"] == driver]
            fig.add_trace(go.Bar(
                y=driver_data["Mæling"],  # Láréttar breytur
                x=driver_data["Gildi"],  # Gildin fyrir hverja breytu
                name=driver,
                orientation='h'  # Lárétt súlurit
            ))

        # Uppsetning lárétta súluritsins
        fig.update_layout(
            title="Frammistaða 2021 (Sigur, Verðlaunapallur, Pól)",
            xaxis_title="Gildi",
            yaxis_title="Mæling",
            barmode="group",
            height=400,
            legend_title="Ökumaður",
            template="plotly_white"
        )

        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')

        return fig

    @output
    @render_widget
    def vertical_points_chart():
        # Plotly lóðrétt súlurit fyrir Stig
        fig = go.Figure()

        # Bæta við súlum fyrir hvern ökumann
        for driver in data["Ökumaður"]:
            driver_data = data[data["Ökumaður"] == driver]
            fig.add_trace(go.Bar(
                x=[driver],  # Ökumenn á X-ás
                y=driver_data["Stig"],  # Stig gildi á Y-ás
                name=driver
            ))

        # Uppsetning lóðrétta súluritsins
        fig.update_layout(
            title="Heildarstig á 2021 Tímabili",
            xaxis_title="Ökumaður",
            yaxis_title="Stig",
            barmode="group",
            height=400,
            yaxis=dict(range=[350, 400]),
            legend_title="Ökumaður",
            template="plotly_white"
        )

        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')

        return fig

    # Birta keppnissamanburðartöflu
    @output
    @render.table
    def race_comparison_table():
        race = input.race_select()
        race_id = race_mapping.get(race)
        if race_id:
            comparison_df = get_race_comparison_data(race_id, race)
            if comparison_df is not None:
                return comparison_df
            else:
                return pd.DataFrame({"Skilaboð": [f"Engin gögn til fyrir {race}"]})
        else:
            return pd.DataFrame({"Skilaboð": [f"Keppnisauðkenni fannst ekki fyrir {race}"]})

    # Birta mynd af brautinni miðað við valda keppni
    @output
    @render.image
    def track_image():
        race = input.race_select()
        if race == "2021 Season Overview":
            return None  # Engin mynd fyrir yfirlitið
        else:
            # Búa til skráarheiti byggt á keppnisheiti
            # Meðhöndla sértákn og bil
            image_name = race.lower().replace(" ", "_").replace("-", "_") + ".png"
            img_path = Path(__file__).parent / "www" / image_name
            if img_path.exists():
                img: ImgData = {
                    "src": str(img_path),
                    "width": "700px",
                    "height": "auto",
                    "style": "display: block; margin-left: auto; margin-right: auto; margin-top: 20px;"
                }
                return img
            else:
                return {
                    "src": "",
                    "alt": f"Mynd fyrir {race} fannst ekki."
                }

    # Birta myndir fyrir 2021 Tímabils Yfirlit
    @output
    @render.image
    def hamilton_car_image():
        img_path = Path(__file__).parent / "Bilamyndir" / "LewisHamiltonBill.jpeg"
        if img_path.exists():
            img: ImgData = {
                "src": str(img_path),
                "width": "300px",
                "height": "150px",
                "style": "border:5px solid Turquoise;",
                "alt": "Bíll Lewis Hamilton árið 2021"
            }
            return img
        else:
            return {
                "src": "",
                "alt": "Mynd af bíl Lewis Hamilton fannst ekki."
            }

    @output
    @render.image
    def verstappen_car_image():
        img_path = Path(__file__).parent / "Bilamyndir" / "MaxVerstappenBill.jpeg"
        if img_path.exists():
            img: ImgData = {
                "src": str(img_path),
                "width": "300px",
                "height": "150px",
                "style": "border:5px solid blue;",
                "alt": "Bíll Max Verstappen árið 2021"
            }
            return img
        else:
            return {
                "src": "",
                "alt": "Mynd af bíl Max Verstappen fannst ekki."
            }

    # Línurit fyrir uppsöfnuð stig
    @output
    @render_widget
    def hamilton_verstappen_cumulative_plot():
        # Sækja gögn fyrir uppsöfnuð stig
        query_points = """
            SELECT race_id, driver_id, race_points
            FROM hamilton_verstappen_race_data_2021
            WHERE type = 'RACE_RESULT'
        """
        data_points = pd.read_sql(query_points, con)

        # Sækja gögn fyrir sigurstaði
        query_wins = """
            SELECT race_id, driver_id, position_display_order
            FROM hamilton_verstappen_race_data_2021
            WHERE type = 'RACE_RESULT' AND position_display_order = 1
        """
        data_wins = pd.read_sql(query_wins, con)

        # Nota 'driver_id' sem inniheldur nöfnin beint
        data_points['driver'] = data_points['driver_id']
        data_wins['driver'] = data_wins['driver_id']

        # Reikna uppsafnaðan fjölda stiga fyrir hvern ökumann
        data_points['cumulative_points'] = data_points.groupby('driver')['race_points'].cumsum()

        # Fjarlægja NaN gildi ef einhver eru
        data_points = data_points.dropna(subset=['race_id', 'cumulative_points'])

        # Línurit fyrir uppsöfnuð stig
        fig = px.line(
            data_points, x="race_id", y="cumulative_points", color="driver", line_group='driver',
            title="Hamilton vs Verstappen: Uppsöfnuð Stig árið 2021",
            markers=True,
            color_discrete_map={
                'lewis-hamilton': 'blue',
                'max-verstappen': 'red'
            }
        )

        # Bæta stjörnum við sigurstaði fyrir Hamilton
        fig.add_trace(go.Scatter(
            x=data_wins[data_wins['driver'] == 'lewis-hamilton']['race_id'],
            y=data_points[data_points['driver'] == 'lewis-hamilton']['cumulative_points'].iloc[
                  data_wins[data_wins['driver'] == 'lewis-hamilton']['race_id'].index] - 5,
            mode='markers',
            name='Sigur Hamilton',
            marker=dict(symbol='star', size=12, color='blue')
        ))

        # Bæta stjörnum við sigurstaði fyrir Verstappen
        fig.add_trace(go.Scatter(
            x=data_wins[data_wins['driver'] == 'max-verstappen']['race_id'],
            y=data_points[data_points['driver'] == 'max-verstappen']['cumulative_points'].iloc[
                  data_wins[data_wins['driver'] == 'max-verstappen']['race_id'].index] - 5,
            mode='markers',
            name='Sigur Verstappen',
            marker=dict(symbol='star', size=12, color='red')
        ))

        # Uppfæra ása og útlit
        fig.update_layout(
            xaxis_title="Keppni",
            yaxis_title="Uppsöfnuð Stig",
            legend_title="Ökumaður",
            template="plotly_white"
        )

        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')

        return fig

    # Línurit fyrir stöðu í keppnum
    @output
    @render_widget
    def hamilton_verstappen_position_plot():
        # Sækja gögn úr töflunni 'hamilton_verstappen_race_data_2021' með 'type' = 'RACE_RESULT'
        query = """
            SELECT race_id, driver_id, position_display_order
            FROM hamilton_verstappen_race_data_2021
            WHERE type = 'RACE_RESULT'
        """
        data = pd.read_sql(query, con)

        # Nota 'driver_id' sem inniheldur nöfnin beint
        data['driver'] = data['driver_id']

        # Gera ráð fyrir að 'race_id' og 'position_display_order' séu heiltölur
        data['race_id'] = data['race_id'].astype(int)
        data['position_display_order'] = data['position_display_order'].astype(int)

        # Raða gögnunum eftir ökumanni og keppni
        data = data.sort_values(['driver', 'race_id'])

        # Fjarlægja NaN gildi ef einhver eru
        data = data.dropna(subset=['race_id', 'position_display_order'])

        # Aðal línuritið fyrir stöðu í keppnum
        fig = px.line(
            data, x="race_id", y="position_display_order", color="driver", line_group='driver',
            title="Hamilton vs Verstappen: Staða í Keppnum árið 2021",
            markers=True,
            color_discrete_map={
                'lewis-hamilton': 'blue',
                'max-verstappen': 'red'
            }
        )

        # Finna gögn þar sem position_display_order = 1 (sigurvegari)
        winner_data = data[data['position_display_order'] == 1]

        # Bæta við stjörnum fyrir sigurvegara
        fig.add_trace(go.Scatter(
            x=winner_data[winner_data['driver'] == 'lewis-hamilton']['race_id'],
            y=winner_data[winner_data['driver'] == 'lewis-hamilton']['position_display_order'],
            mode='markers+text',
            name='Sigur Hamilton',
            marker=dict(symbol='star', size=15, color='blue'),
        ))

        fig.add_trace(go.Scatter(
            x=winner_data[winner_data['driver'] == 'max-verstappen']['race_id'],
            y=winner_data[winner_data['driver'] == 'max-verstappen']['position_display_order'],
            mode='markers+text',
            name='Sigur Verstappen',
            marker=dict(symbol='star', size=15, color='red'),
        ))

        # Snúa y-ásnum svo 1. staður sé efst
        fig.update_yaxes(autorange="reversed")

        # Uppfæra ása og útlit
        fig.update_layout(
            xaxis_title="Keppni",
            yaxis_title="Staða í Keppni",
            template="plotly_white"
        )

        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')

        return fig

    # Nýir úttakshlutir fyrir framleiðenda frammistöðu
    @output
    @render_widget
    def manufacturer_average_points_plot():
        if input.manufacturer_type():
            manufacturer_column = manufacturer_choices[input.manufacturer_type()]
            # Sækja gögn úr 'race_result' viewinu
            query = f"""
                SELECT {manufacturer_column} AS manufacturer_id, points
                FROM race_result
            """
            data = pd.read_sql(query, con)
            # Hópa eftir framleiðanda og reikna meðaltal stiga
            average_points = data.groupby('manufacturer_id')['points'].mean().reset_index()
            # Sækja samanlögð stig til að sía út þá sem hafa minna en 100 stig
            total_points = data.groupby('manufacturer_id')['points'].sum().reset_index()
            # Tengja saman meðaltal og samtala
            merged_data = pd.merge(average_points, total_points, on='manufacturer_id', suffixes=('_mean', '_sum'))
            # Sía út þá sem hafa samtala stiga minna en 100
            filtered_data = merged_data[merged_data['points_sum'] >= 100]
            # Teikna súlurit fyrir meðaltal stiga
            fig = px.bar(
                filtered_data.sort_values('points_mean', ascending=False),
                x='manufacturer_id', y='points_mean',
                title=f"Meðaltal Stiga eftir {input.manufacturer_type()} (≥100 samtala stiga)"
            )
            fig.update_layout(xaxis_title=input.manufacturer_type(), yaxis_title="Meðaltal Stiga")
            fig.update_xaxes(tickangle=45)
            # Bæta við hreinum hover effect
            fig.update_traces(hoverinfo='name+x+y')
            return fig

    @output
    @render_widget
    def manufacturer_total_points_plot():
        if input.manufacturer_type():
            manufacturer_column = manufacturer_choices[input.manufacturer_type()]
            # Sækja gögn úr 'race_result' viewinu
            query = f"""
                SELECT {manufacturer_column} AS manufacturer_id, points
                FROM race_result
            """
            data = pd.read_sql(query, con)
            # Hópa eftir framleiðanda og reikna samtala stiga
            total_points = data.groupby('manufacturer_id')['points'].sum().reset_index()
            # Sía út þá sem hafa samtala stiga minna en 100
            filtered_data = total_points[total_points['points'] >= 100]
            # Teikna súlurit fyrir samtala stiga
            fig = px.bar(
                filtered_data.sort_values('points', ascending=False),
                x='manufacturer_id', y='points',
                title=f"Samtala Stiga eftir {input.manufacturer_type()} (≥100 samtala stiga)"
            )
            fig.update_layout(xaxis_title=input.manufacturer_type(), yaxis_title="Samtala Stiga")
            fig.update_xaxes(tickangle=45)
            # Bæta við hreinum hover effect
            fig.update_traces(hoverinfo='name+x+y')
            return fig

    # Sýna lóðrétt súlurit
    @output
    @render_widget
    def wins_bar_chart():
        # Gögnin fyrir Sigur
        wins_data = pd.DataFrame({
            "Ökumaður": ["Lewis Hamilton", "Max Verstappen"],
            "Sigur": [hamilton_wins, verstappen_wins]
        })

        # Plotly súlurit
        fig = go.Figure()

        # Bæta við súlum fyrir hvern ökumann
        for driver in wins_data["Ökumaður"]:
            driver_data = wins_data[wins_data["Ökumaður"] == driver]
            fig.add_trace(go.Bar(
                x=[driver],
                y=driver_data["Sigur"],
                name=driver,
                text=driver_data["Sigur"],
                textposition="auto",
            ))

        # Uppsetning lóðrétta súluritsins
        fig.update_layout(
            title="Sigur Samanburður",
            xaxis_title="Ökumaður",
            yaxis_title="Sigur",
            barmode="group",
            height=400,
            legend_title="Ökumaður",
            template="plotly_white"
        )

        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')

        return fig

    @output
    @render_widget
    def horizontal_race_bar_chart():
        # Ná í valið keppni
        race = input.race_select()

        # Ná í gögn fyrir valda keppni
        df = get_race_points(race)

        # Búa til lóðrétt súlurit
        fig = px.bar(
            df,
            x="driver_id",
            y="race_points",
            title=f"Stig í Keppni fyrir {race}",
            labels={"driver_id": "Ökumaður", "race_points": "Stig"},
            color="driver_id",
            color_discrete_map={
                'lewis-hamilton': 'rgba(0, 0, 255, 0.7)',
                'max-verstappen': 'rgba(255, 0, 0, 0.7)'
            }
        )
        fig.update_layout(
            xaxis_title="Ökumaður",
            yaxis_title="Stig í Keppni",
            template="plotly_white",
            showlegend=False
        )

        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')

        return fig

    @output
    @render_widget
    def fastest_lap_chart_2():
        race_id = race_mapping.get(input.race_select())
        if not race_id:
            return go.Figure()

        query = f"""
        SELECT driver_id, MIN(lap_time) as fastest_lap
        FROM f1_race_data
        WHERE race_id = {race_id}
        GROUP BY driver_id
        """
        df = pd.read_sql_query(query, con)
        if df.empty:
            return go.Figure()

        fig = px.bar(
            df,
            x="driver_id",
            y="fastest_lap",
            title="Samanburður á Hraðasta Hring",
            labels={"driver_id": "Ökumaður", "fastest_lap": "Hringtími (s)"},
            color="driver_id",
        )
        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')
        return fig

    @output
    @render_widget
    def horizontal_race_time_comparison_chart():
        race_id = race_mapping.get(input.race_select())
        if not race_id:
            fig = go.Figure()
            fig.update_layout(
                title="Engin gögn til fyrir valda keppni.",
                xaxis_title="Keppnistími",
                yaxis_title="Ökumaður",
                template="plotly_white"
            )
            return fig

        query = f"""
        SELECT driver_id, race_time
        FROM hamilton_verstappen_race_data_2021
        WHERE race_id = {race_id}
        """
        df = pd.read_sql_query(query, con)
        df = df.dropna(subset=["race_time"])

        df["race_time"] = df["race_time"].apply(convert_time_to_seconds)

        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                title="Engin gögn til fyrir valda keppni.",
                xaxis_title="Keppnistími",
                yaxis_title="Ökumaður",
                template="plotly_white"
            )
            return fig

        min_value = df["race_time"].min()
        max_value = df["race_time"].max()
        buffer = (max_value - min_value) * 0.25

        fig = px.bar(
            df,
            y="driver_id",
            x="race_time",
            orientation="h",
            title="Samanburður á Keppnistíma",
            labels={"driver_id": "Ökumaður", "race_time": "Keppnistími (s)"},
            color="driver_id",
            color_discrete_map={
                'lewis-hamilton': 'rgba(0, 0, 255, 0.7)',
                'max-verstappen': 'rgba(255, 0, 0, 0.7)'
            }
        )

        fig.update_layout(
            xaxis=dict(
                title="Keppnistími (s)",
                range=[min_value - buffer, max_value + buffer],
            ),
            yaxis_title="Ökumaður",
            template="plotly_white",
            showlegend=False
        )

        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')

        return fig

    @output
    @render_widget
    def vertical_comparison_barplot():
        race_id = race_mapping.get(input.race_select())
        if not race_id:
            return go.Figure()

        query_race_points = f"""
        SELECT driver_id, race_points, race_laps
        FROM hamilton_verstappen_race_data_2021
        WHERE race_id = {race_id}
        """
        df_race_points = pd.read_sql_query(query_race_points, con)

        query_race_data = f"""
        SELECT driver_id, stops
        FROM f1_race_data
        WHERE race_id = {race_id}
        GROUP BY driver_id
        """
        df_race_data = pd.read_sql_query(query_race_data, con)

        df = pd.merge(df_race_points, df_race_data, on="driver_id", how="outer")

        df_long = df.melt(
            id_vars=["driver_id"],
            value_vars=["race_points", "race_laps", "stops"],
            var_name="Flokkur",
            value_name="Gildi"
        )

        fig = px.bar(
            df_long,
            x="driver_id",
            y="Gildi",
            color="Flokkur",
            barmode="group",
            title="Samanburður á Stig í Keppni, Hringjum og Pásum",
            labels={"driver_id": "Ökumaður", "Gildi": "Gildi", "Flokkur": "Flokkur"}
        )

        fig.update_layout(
            xaxis_title="Ökumaður",
            yaxis_title="Gildi",
            template="plotly_white"
        )

        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')

        return fig

    @output
    @render_widget
    def horizontal_pit_stop_comparison_chart():
        race_id = race_mapping.get(input.race_select())
        if not race_id:
            return go.Figure()

        query = f"""
        SELECT driver_id, 
            pit_stop_time, 
            pit_stop_time_sum
        FROM f1_race_data
        WHERE race_id = {race_id}
        """
        df = pd.read_sql_query(query, con)

        df['pit_stop_time'] = df['pit_stop_time'].apply(convert_time_to_seconds_2)
        df['pit_stop_time_sum'] = df['pit_stop_time_sum'].apply(convert_time_to_seconds_2)

        df = df.dropna(subset=['pit_stop_time', 'pit_stop_time_sum'])

        df_long = df.melt(
            id_vars=["driver_id"],
            value_vars=["pit_stop_time", "pit_stop_time_sum"],
            var_name="Flokkur",
            value_name="Gildi"
        )

        fig = px.bar(
            df_long,
            y="driver_id",
            x="Gildi",
            color="Flokkur",
            orientation="h",
            barmode="group",
            title="Samanburður á Pásutíma og Samtals Pásutíma",
            labels={"driver_id": "Ökumaður", "Gildi": "Gildi (s)", "Flokkur": "Flokkur"}
        )

        min_value = df_long["Gildi"].min()
        max_value = df_long["Gildi"].max()
        buffer = (max_value - min_value) * 0.1
        fig.update_layout(
            xaxis=dict(
                title="Gildi (s)",
                range=[min_value - buffer, max_value + buffer]
            ),
            yaxis_title="Ökumaður",
            template="plotly_white"
        )

        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')

        return fig

    @output
    @render_widget
    def fastest_lap_chart():
        race_id = race_mapping.get(input.race_select())
        if not race_id:
            return go.Figure()

        query = f"""
        SELECT driver_id, lap_time
        FROM f1_race_data
        WHERE race_id = {race_id}
        """
        df = pd.read_sql_query(query, con)

        df['lap_time'] = df['lap_time'].apply(convert_lap_time_to_seconds)

        df = df.dropna(subset=['lap_time'])

        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                title="Engin gild gögn fyrir valda keppni.",
                xaxis_title="Hringtími (s)",
                yaxis_title="Ökumaður",
                template="plotly_white"
            )
            return fig

        fig = px.bar(
            df,
            y="driver_id",
            x="lap_time",
            orientation="h",
            title="Samanburður á Hraðasta Hring",
            labels={"driver_id": "Ökumaður", "lap_time": "Hringtími (s)"},
            color="driver_id",
            color_discrete_map={
                'lewis-hamilton': 'rgba(0, 0, 255, 0.7)',
                'max-verstappen': 'rgba(255, 0, 0, 0.7)'
            }
        )

        min_value = df["lap_time"].min()
        max_value = df["lap_time"].max()
        buffer = (max_value - min_value) * 0.25
        fig.update_layout(
            xaxis=dict(
                title="Hringtími (s)",
                range=[min_value - buffer, max_value + buffer]
            ),
            yaxis_title="Ökumaður",
            template="plotly_white",
            showlegend=False
        )

        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')

        return fig

    @output
    @render_widget
    def start_vs_finish_positions_chart():
        race_id = race_mapping.get(input.race_select())
        if not race_id:
            return go.Figure()

        query = f"""
        SELECT driver_id, 
            race_qualification_position_number, 
            race_grid_position_number, 
            race_positions_gained
        FROM hamilton_verstappen_race_data_2021
        WHERE race_id = {race_id}
        """
        df = pd.read_sql_query(query, con)

        df['race_qualification_position_number'] = pd.to_numeric(df['race_qualification_position_number'],
                                                                 errors='coerce')
        df['race_grid_position_number'] = pd.to_numeric(df['race_grid_position_number'], errors='coerce')
        df['race_positions_gained'] = pd.to_numeric(df['race_positions_gained'], errors='coerce')

        df = df.dropna(
            subset=['race_qualification_position_number', 'race_grid_position_number', 'race_positions_gained'])

        df['race_finish_position_number'] = df['race_grid_position_number'] - df['race_positions_gained']

        df_long = df.melt(
            id_vars=["driver_id"],
            value_vars=[
                "race_qualification_position_number",
                "race_grid_position_number",
                "race_finish_position_number"
            ],
            var_name="Flokkur",
            value_name="Staða"
        )

        fig = px.line(
            df_long,
            x="Flokkur",
            y="Staða",
            color="driver_id",
            markers=True,
            title="Rás- vs Lokastöður",
            labels={
                "driver_id": "Ökumaður",
                "Staða": "Staða (Lægri er betri)",
                "Flokkur": "Flokkur"
            },
            line_shape="linear",
        )

        fig.update_traces(marker=dict(size=10))

        fig.update_layout(
            yaxis=dict(
                title="Staða (Lægri er betri)",
                autorange="reversed",
            ),
            xaxis_title="Flokkur (Kvarði, Ráslína, Lok)",
            template="plotly_white",
            legend_title="Ökumaður"
        )

        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')

        return fig

    @output
    @render_widget
    def positions_gained_bar_chart():
        race_id = race_mapping.get(input.race_select())
        if not race_id:
            return go.Figure()

        query = f"""
        SELECT driver_id, race_positions_gained
        FROM hamilton_verstappen_race_data_2021
        WHERE race_id = {race_id}
        """
        df = pd.read_sql_query(query, con)

        df['race_positions_gained'] = pd.to_numeric(df['race_positions_gained'], errors='coerce')
        df = df.dropna(subset=['race_positions_gained'])

        fig = px.bar(
            df,
            x="driver_id",
            y="race_positions_gained",
            color="driver_id",
            title="Stöður Græddar eða Tapaðar",
            labels={
                "driver_id": "Ökumaður",
                "race_positions_gained": "Stöður Græddar (+) eða Tapaðar (-)"
            },
            color_discrete_map={
                'lewis-hamilton': 'rgba(0, 0, 255, 0.7)',
                'max-verstappen': 'rgba(255, 0, 0, 0.7)'
            }
        )

        min_value = df["race_positions_gained"].min()
        max_value = df["race_positions_gained"].max()
        buffer = (max_value - min_value)

        fig.add_shape(
            type="line",
            x0=-0.5,
            x1=len(df['driver_id']) - 0.5,
            y0=0,
            y1=0,
            line=dict(
                color="black",
                width=4
            )
        )

        fig.update_layout(
            yaxis=dict(
                title="Stöður Græddar eða Tapaðar",
                range=[min_value - buffer, max_value + buffer]
            ),
            xaxis_title="Ökumaður",
            template="plotly_white",
            showlegend=False
        )

        # Bæta við hreinum hover effect
        fig.update_traces(hoverinfo='name+x+y')

        return fig


# Búa til Shiny appið
app = App(app_ui, server)
