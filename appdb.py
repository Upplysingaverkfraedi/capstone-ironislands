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

# Búa til Shiny appið
app = App(app_ui, server)

if __name__ == "__main__":
    app.run()
