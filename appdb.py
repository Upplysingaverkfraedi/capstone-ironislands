from shiny import App, render, ui
import pandas as pd
import plotly.express as px
import sqlite3
from shinywidgets import render_widget, output_widget

# Setja upp tengingu við gagnagrunn
con = sqlite3.connect("f1db.db")

# Lesa möguleika fyrir dropdown valmöguleika
driver_choices = pd.read_sql("SELECT name FROM driver", con)['name'].tolist()
constructor_choices = pd.read_sql("SELECT name FROM constructor", con)['name'].tolist()
circuit_choices = pd.read_sql("SELECT name FROM circuit", con)['name'].tolist()

# Búa til valmöguleika fyrir framleiðanda flokka
manufacturer_choices = {
    "Vélaframleiðandi": "engine_manufacturer_id",
    "Dekkjaframleiðandi": "tyre_manufacturer_id",
    "Lið": "constructor_id"
}

# UI hluti
app_ui = ui.page_fluid(
    ui.h2("Formula 1 Mælaborð"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("driver", "Veldu Ökumann", choices=driver_choices),
            ui.input_select("constructor", "Veldu Lið", choices=constructor_choices),
            ui.input_select("circuit", "Veldu Braut", choices=circuit_choices),
            ui.input_action_button("update", "Uppfæra")
        ),
        ui.page_auto(
            ui.navset_tab(
                ui.nav_panel("Ökumannsframmistaða", output_widget("driver_performance_plot")),
                ui.nav_panel("Liðsframmistaða", output_widget("constructor_performance_plot")),
                ui.nav_panel("Brautaframmistaða", output_widget("circuit_plot")),
                ui.nav_panel(
                    "Hamilton vs Verstappen 2021",
                    ui.output_ui("hamilton_verstappen_plots")
                ),
                ui.nav_panel(
                    "Framleiðenda Frammistaða",
                    ui.input_select("manufacturer_type", "Veldu Flokk", choices=list(manufacturer_choices.keys())),
                    output_widget("manufacturer_average_points_plot"),
                    output_widget("manufacturer_total_points_plot")
                )
            )
        )
    )
)

# Server hluti
def server(input, output, session):
    @output
    @render_widget
    def circuit_plot():
        if input.circuit():
            circuit_query = f"""
                SELECT race.id AS race_id, driver.name AS driver, race_driver_standing.points AS points 
                FROM race 
                JOIN circuit ON circuit.id = race.circuit_id 
                JOIN race_driver_standing ON race.id = race_driver_standing.race_id 
                JOIN driver ON driver.id = race_driver_standing.driver_id 
                WHERE circuit.name = '{input.circuit()}'
            """
            circuit_data = pd.read_sql(circuit_query, con)
            fig = px.line(
                circuit_data, x="race_id", y="points", color="driver",
                title=f"Frammistaða eftir Braut: {input.circuit()}"
            )
            fig.update_layout(xaxis_title="Keppni", yaxis_title="Stig")
            return fig

    @output
    @render_widget
    def driver_performance_plot():
        if input.driver():
            driver_query = f"""
                SELECT race.id AS race_id, race_driver_standing.points AS points 
                FROM race_driver_standing
                JOIN driver ON driver.id = race_driver_standing.driver_id
                JOIN race ON race.id = race_driver_standing.race_id
                WHERE driver.name = '{input.driver()}'
            """
            driver_data = pd.read_sql(driver_query, con)
            fig = px.line(
                driver_data, x="race_id", y="points",
                title=f"Frammistaða Ökumanns: {input.driver()}"
            )
            fig.update_layout(xaxis_title="Keppni", yaxis_title="Stig")
            return fig

    @output
    @render_widget
    def constructor_performance_plot():
        if input.constructor():
            constructor_query = f"""
                SELECT race.id AS race_id, race_constructor_standing.points AS points 
                FROM race_constructor_standing
                JOIN constructor ON constructor.id = race_constructor_standing.constructor_id
                JOIN race ON race.id = race_constructor_standing.race_id
                WHERE constructor.name = '{input.constructor()}'
            """
            constructor_data = pd.read_sql(constructor_query, con)
            fig = px.line(
                constructor_data, x="race_id", y="points",
                title=f"Frammistaða Liðs: {input.constructor()}"
            )
            fig.update_layout(xaxis_title="Keppni", yaxis_title="Stig")
            return fig

    # Búa til samsettan úttak fyrir Hamilton vs Verstappen línuritin
    @output
    @render.ui
    def hamilton_verstappen_plots():
        return ui.TagList(
            ui.h3("Uppsöfnuð Stig"),
            output_widget("hamilton_verstappen_cumulative_plot"),
            ui.h3("Staða í Keppnum"),
            output_widget("hamilton_verstappen_position_plot")
        )

    # Línurit fyrir uppsöfnuð stig
    @output
    @render_widget
    def hamilton_verstappen_cumulative_plot():
        # Sækja gögn úr töflunni 'hamilton_verstappen_race_data_2021' með 'type' = 'RACE_RESULT'
        query = """
            SELECT race_id, driver_id, race_points
            FROM hamilton_verstappen_race_data_2021
            WHERE type = 'RACE_RESULT'
        """
        data = pd.read_sql(query, con)

        # Nota 'driver_id' sem inniheldur nöfnin beint
        data['driver'] = data['driver_id']

        # Gera ráð fyrir að 'race_id' sé heiltala
        data['race_id'] = data['race_id'].astype(int)

        # Raða gögnunum eftir ökumanni og keppni
        data = data.sort_values(['driver', 'race_id'])

        # Reikna uppsafnaðan fjölda stiga fyrir hvern ökumann
        data['cumulative_points'] = data.groupby('driver')['race_points'].cumsum()

        # Fjarlægja NaN gildi ef einhver eru
        data = data.dropna(subset=['race_id', 'cumulative_points'])

        # Bæta við merkjum og tilgreina liti, nota line_group
        fig = px.line(
            data, x="race_id", y="cumulative_points", color="driver", line_group='driver',
            title="Hamilton vs Verstappen: Uppsöfnuð Stig árið 2021",
            markers=True,
            color_discrete_map={
                'lewis-hamilton': 'blue',
                'max-verstappen': 'red'
            }
        )
        # Auka breidd línanna
        fig.update_traces(line=dict(width=4))

        # Uppfæra ása og útlit
        fig.update_layout(
            xaxis_title="Keppni",
            yaxis_title="Uppsöfnuð Stig",
        )

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

        # Bæta við merkjum og tilgreina liti, nota line_group
        fig = px.line(
            data, x="race_id", y="position_display_order", color="driver", line_group='driver',
            title="Hamilton vs Verstappen: Staða í Keppnum árið 2021",
            markers=True,
            color_discrete_map={
                'lewis-hamilton': 'blue',
                'max-verstappen': 'red'
            }
        )
        # Auka breidd línanna
        fig.update_traces(line=dict(width=4))

        # Snúa y-ásnum svo 1. staður sé efst
        fig.update_yaxes(autorange="reversed")

        # Uppfæra ása og útlit
        fig.update_layout(
            xaxis_title="Keppni",
            yaxis_title="Staða í Keppni",
        )

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
            return fig

# Búa til Shiny appið
app = App(app_ui, server)

if __name__ == "__main__":
    app.run()
