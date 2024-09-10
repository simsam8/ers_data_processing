import pandas as pd
import plotly.express as px
from plotly.graph_objs import Figure

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


def fig_species_weight(df, interval="year", year_n=2014) -> Figure:
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


def fig_vessel_catch(df, interval="year", year_n=2014) -> Figure:
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


def fig_area_catch(df, interval="year", year_n=None) -> Figure:
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


def fig_pie_chart(df: pd.DataFrame, category: str, top_n: int = 5) -> Figure:
    """
    Categories: (vessels, species, area)
    """
    category_map = {
        "vessels": "Radiokallesignal (ERS)",
        "area": "Hovedområde start",
    }
    if category in category_map:
        category = category_map[category]

    filtered_df = df
    if category == "species":
        filtered_df = filtered_df[species]
        filtered_df = filtered_df.melt(
            var_name="species",
            value_name="Rundvekt",
            value_vars=species,
        )
        filtered_df = filtered_df.replace("ANDRE", "Arter uten navn")

    else:
        filtered_df = filtered_df[[category, "Rundvekt"]]

    filtered_df = filtered_df.groupby(category, as_index=False).sum()

    result = filtered_df.nlargest(top_n, columns="Rundvekt", keep="all")
    result.loc[len(result)] = [
        "ANDRE",
        filtered_df.loc[
            ~filtered_df[category].isin(result[category]), "Rundvekt"
        ].sum(),
    ]

    fig = px.pie(result, names=category, values="Rundvekt")
    return fig
