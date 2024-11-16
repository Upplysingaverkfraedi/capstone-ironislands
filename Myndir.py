import shiny
from shiny import App, render, ui
from pathlib import Path

# Define the UI of the Shiny dashboard
app_ui = ui.page_fluid(
    # Centered title
    ui.tags.div(
        ui.h2("Keppnisbílar Lewis Hamilton og Max Verstappen"),
        style="text-align: center; font-family: Monaco, monospace;"
    ),
    # Row for the two images and their captions
    ui.row(
        # Column for Lewis Hamilton's car
        ui.column(
            5,  # Takes half the width
            ui.div(
                ui.h3("Bíll Lewis Hamilton - Mercedes Benz W12"),
                style="text-align: left; font-family: Monaco, monospace; font-size: 8px;"  # Reduced font size
            ),
            ui.output_image("hamilton_image")
        ),
        # Column for Max Verstappen's car
        ui.column(
            5,  # Takes half the width
            ui.div(
                ui.h3("Bíll Max Verstappen - Honda RB16B"),
                style="text-align: left; font-family: Monaco, monospace; font-size: 8px;"  # Reduced font size
            ),
            ui.output_image("verstappen_image")
        )
    )
)

# Define the server function to render the images with styling
def server(input, output, session):
    @output
    @render.image
    def hamilton_image():
        img_path = Path(__file__).parent / "Bilamyndir" / "LewisHamiltonBill.jpeg"
        return {
            "src": str(img_path),
            "width": "300px",
            "height": "150px",
            "style": "border:5px solid Turquoise;",
            "alt": "Bíll Lewis Hamilton árið 2021"
        }

    @output
    @render.image
    def verstappen_image():
        img_path = Path(__file__).parent / "Bilamyndir" / "MaxVerstappenBill.jpeg"
        return {
            "src": str(img_path),
            "width": "300px",
            "height": "150px",
            "style": "border:5px solid blue;",
            "alt": "Bíll Max Verstappen árið 2021"
        }

# Create the Shiny app
app = App(app_ui, server)

# Run the app
if __name__ == "__main__":
    app.run()