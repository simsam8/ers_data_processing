# Run this app with `python app` and
# visit http://127.0.0.1:8050/ in your web browser.

import pandas as pd
import plotly
from dash import Dash, Input, Output, callback, dcc, html
from figures import fig_area_catch, fig_pie_chart, fig_species_weight, fig_vessel_catch

df = pd.read_csv("processed/dca/combined.csv")
df["Starttidspunkt"] = pd.to_datetime(df["Starttidspunkt"])
df["year"] = df["Starttidspunkt"].dt.year
df["month"] = df["Starttidspunkt"].dt.month
year_max = df["year"].max()
year_min = df["year"].min()

vessels = df["Radiokallesignal (ERS)"].unique()


def generate_table(df, max_rows=10) -> html.Table:
    """
    Generate a table of the given dataframe:

    Arg:
        df : A pandas dataframe
        max_rows : Number of rows to display

    Returns:
        A html.Table of the dataframe

    """
    return html.Table(
        [
            html.Thead(html.Tr([html.Th(col) for col in df.columns])),
            html.Tbody(
                [
                    html.Tr(
                        [html.Td(df.iloc[i][col]) for col in df.columns]
                    )
                    for i in range(min(len(df), max_rows))
                ]
            ),
        ]
    )


def generate_interval_menu(id) -> html.Div:
    """
    Creates a menu for an interval menu:

    Args:
        id (str) : container id

    Returns:
        A html.Div of the interval menu
    """
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


def generate_pie_chart_menu(id) -> html.Div:
    """
    Creates a menu for the pie chart.

    Args:
        id (str) : container id

    Returns:
        A html.Div of the pie chart menu
    """
    return html.Div(
        [
            dcc.RadioItems(
                options=["vessels", "species", "area"],
                value="vessels",
                id=f"{id}_category_radio",
            ),
            dcc.Input(
                type="number",
                value=5,
                min=2,
                id=f"{id}_number_input",
            ),
        ]
    )


def create_container(id, title, graph_type, graph_function=None, **kwargs) -> html.Div:
    """
    Creates a container with a given graph type and graph function.

    Args:
        id (str) : container id.
        title (str) : container title.
        graph_type (str) : Type of graph to use. (interval, pie)
        graph_function (func) : Graphing function to generate figure.

    Returns:
        A html.Div containing graph and menu
    """
    if graph_type == "interval":
        menu = generate_interval_menu(id=id)
    else:
        menu = generate_pie_chart_menu(id=id)
    container = html.Div(
        [
            html.H2(title),
            menu,
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
                    graph_type="interval",
                    graph_function=fig_species_weight,
                ),
                create_container(
                    id="vessel_catch",
                    title="Vessels catch over time",
                    graph_type="interval",
                    graph_function=fig_vessel_catch,
                ),
                create_container(
                    id="area_catch",
                    title="Area catch over time",
                    graph_type="interval",
                    graph_function=fig_area_catch,
                ),
                create_container(
                    id="pie_top_n",
                    title="Top N pie chart",
                    graph_type="pie",
                    graph_function=fig_pie_chart,
                    category="vessels",
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


@callback(
    Output("pie_top_n_graph", "figure"),
    [
        Input("pie_top_n_category_radio", "value"),
        Input("pie_top_n_number_input", "value"),
    ],
)
def update_pie_chart(category, number):
    if type(number) is not int:
        return plotly.graph_objs.Figure()
    else:
        return fig_pie_chart(df, category, number)


# Initialize callbacks
set_graph_interval("species_over_time", fig_species_weight)
set_graph_interval("vessel_catch", fig_vessel_catch)
set_graph_interval("area_catch", fig_area_catch)


if __name__ == "__main__":
    app.run(debug=True)
