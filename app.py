# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import pandas as pd
import plotly.express as px
from plotly.graph_objs import Figure
from dash import Dash, Input, Output, callback, dcc, html

df = pd.read_csv("processed/dca/combined.csv")
df["Starttidspunkt"] = pd.to_datetime(df["Starttidspunkt"])
df["year"] = df["Starttidspunkt"].dt.year
df["month"] = df["Starttidspunkt"].dt.month
year_max = df["year"].max()
year_min = df["year"].min()

vessels = df["Radiokallesignal (ERS)"].unique()
species = [
    "Blåkveite",
    "Breiflabb",
    "Dypvannsreke",
    "Flekksteinbit",
    "Gråsteinbit",
    "Hyse",
    "Kveite",
    "Lange",
    "Lyr",
    "Lysing",
    "Sei",
    "Snabeluer",
    "Torsk",
    "Uer (vanlig)",
    "ANDRE",
]


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


def fig_species_weight(interval="year", year_n=2014) -> Figure:
    filtered_df = df
    if interval == "month":
        filtered_df = filtered_df[filtered_df["year"] == year_n]

    filtered_df = filtered_df.melt(
        id_vars=[interval],
        var_name="species",
        value_name="weight",
        value_vars=species,
    )
    filtered_df = filtered_df.groupby([interval, "species"], as_index=False).sum()
    fig = px.line(
        filtered_df, x=interval, y="weight", color="species", symbol="species"
    )
    return fig


def fig_vessel_catch(interval="year", year_n=2014) -> Figure:
    filtered_df = df
    if interval == "month":
        filtered_df = filtered_df[filtered_df["year"] == year_n]

    filtered_df = filtered_df[[interval, "Radiokallesignal (ERS)", "Rundvekt"]]

    filtered_df = filtered_df.groupby(
        [interval, "Radiokallesignal (ERS)"], as_index=False
    ).sum()
    fig = px.line(
        filtered_df,
        x=interval,
        y="Rundvekt",
        color="Radiokallesignal (ERS)",
        symbol="Radiokallesignal (ERS)",
    )
    return fig


def fig_area_catch(interval="year", year_n=None) -> Figure:
    filtered_df = df
    if interval == "month" and year_n is not None:
        filtered_df = filtered_df[filtered_df["year"] == year_n]

    filtered_df = filtered_df[[interval, "Hovedområde start", "Rundvekt"]]
    filtered_df = filtered_df.groupby(
        [interval, "Hovedområde start"], as_index=False
    ).sum()
    fig = px.line(
        filtered_df,
        x=interval,
        y="Rundvekt",
        color="Hovedområde start",
        symbol="Hovedområde start",
    )
    return fig


def create_container(id, title, graph_function=None, **kwargs) -> html.Div:
    container = html.Div(
        [
            html.H2(title),
            generate_interval_menu(id=f"{id}"),
            (
                dcc.Graph(id=f"{id}_graph", figure=graph_function(**kwargs))
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
        return graph_function(interval, year)

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
