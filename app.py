# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, callback, dcc, html
from dash.exceptions import PreventUpdate

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


def generate_table(dataframe, max_rows=10):
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


def species_weight_over_time(interval="year", creation_call=False):
    filtered_df = pd.melt(
        df,
        id_vars=[interval],
        var_name="species",
        value_name="weight",
        value_vars=species,
    )
    filtered_df = filtered_df.groupby([interval, "species"], as_index=False).sum()
    fig = px.line(
        filtered_df, x=interval, y="weight", color="species", symbol="species"
    )
    if not creation_call:
        return fig
    else:
        return (
            [
                dcc.Graph(id="current_graph", figure=fig),
            ],
        )


app = Dash(__name__)
app.config.suppress_callback_exceptions = True

app.layout = html.Div(
    children=[
        generate_table(df),
        html.Div(
            id="species_weight_over_time",
            children=[
                html.H2("Species weight over time"),
                html.Label("Time interval"),
                dcc.Dropdown(["Yearly", "Monthly"], id="time_interval"),
                dcc.Graph(id="species_weight_graph"),
            ],
        ),
    ]
)


@callback(
    Output("species_weight_graph", "figure"),
    Input("time_interval", "value"),
)
def set_graph_interval(interval):
    if not interval:
        raise PreventUpdate
    mapping = {"Yearly": "year", "Monthly": "month"}
    return species_weight_over_time(mapping[interval])


if __name__ == "__main__":
    app.run(debug=True)
