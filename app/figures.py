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
