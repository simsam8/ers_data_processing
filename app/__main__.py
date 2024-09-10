# Run this app with `python app` and
# visit http://127.0.0.1:8050/ in your web browser.

import pandas as pd
from dash import Dash, Input, Output, callback, dcc, html
from figures import fig_area_catch, fig_species_weight, fig_vessel_catch

df = pd.read_csv("processed/dca/combined.csv")
df["Starttidspunkt"] = pd.to_datetime(df["Starttidspunkt"])
df["year"] = df["Starttidspunkt"].dt.year
df["month"] = df["Starttidspunkt"].dt.month
year_max = df["year"].max()
year_min = df["year"].min()

vessels = df["Radiokallesignal (ERS)"].unique()


def generate_table(dataframe, max_rows=10) -> html.Table:
    return html.Table(
        [
            html.Thead(html.Tr([html.Th(col) for col in dataframe.columns])),
            html.Tbody(
                [
                    html.Tr(
                        [html.Td(dataframe.iloc[i][col]) for col in dataframe.columns]
                    )
                    for i in range(min(len(dataframe), max_rows))
                ]
            ),
        ]
    )


def generate_interval_menu(id) -> html.Div:
    return html.Div(
        [
            dcc.RadioItems(
                options={"year": "Yearly", "month": "Monthly"},
                value="year",
                id=f"{id}_interval_radio",
            ),
            dcc.Slider(
                id=f"{id}_interval_slider",
                min=year_min,
                max=year_max,
                step=1,
                disabled=True,
                marks={i: f"{i}" for i in range(int(year_min), year_max + 1)},
            ),
        ]
    )


def create_container(id, title, graph_function=None, **kwargs) -> html.Div:
    container = html.Div(
        [
            html.H2(title),
            generate_interval_menu(id=f"{id}"),
            (
                dcc.Graph(id=f"{id}_graph", figure=graph_function(df, **kwargs))
                if graph_function is not None
                else dcc.Graph(id=f"{id}_graph")
            ),
        ]
    )
    return container


app = Dash(__name__)
app.config.suppress_callback_exceptions = True

app.layout = html.Div(
    children=[
        generate_table(df),
        html.Div(
            children=[
                create_container(
                    id="species_over_time",
                    title="Species weight over time",
                    graph_function=fig_species_weight,
                ),
                create_container(
                    id="vessel_catch",
                    title="Vessels catch over time",
                    graph_function=fig_vessel_catch,
                ),
                create_container(
                    id="area_catch",
                    title="Area catch over time",
                    graph_function=fig_area_catch,
                ),
            ],
        ),
    ]
)

####################
# Callback functions
####################


def set_graph_interval(container_id, graph_function):
    @callback(
        Output(f"{container_id}_graph", "figure"),
        [
            Input(f"{container_id}_interval_radio", "value"),
            Input(f"{container_id}_interval_slider", "value"),
        ],
    )
    def set_graph_year(interval, year):
        return graph_function(df, interval, year)

    @callback(
        Output(f"{container_id}_interval_slider", "disabled"),
        Input(f"{container_id}_interval_radio", "value"),
    )
    def toggle_year_slider(interval):
        if interval == "year":
            return True
        elif interval == "month":
            return False


# Initialize callbacks
set_graph_interval("species_over_time", fig_species_weight)
set_graph_interval("vessel_catch", fig_vessel_catch)
set_graph_interval("area_catch", fig_area_catch)


if __name__ == "__main__":
    app.run(debug=True)
