#!/usr/bin/env python3
import argparse
import os

import numpy as np
import pandas as pd
from pandas import DataFrame, Series


def read_and_combine(data_folder: str) -> DataFrame:
    """
    Read all data from a data folder, and combine it into a single dataframe.
    """
    dframes = []
    for file in os.listdir(data_folder):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(data_folder, file), sep=";", low_memory=False)
            dframes.append(df)
    return pd.concat(dframes)


def prepare_data(df, time_column: str) -> DataFrame:
    columns = [
        "Melding ID",
        "Radiokallesignal (ERS)",
        time_column,
        "Havn (kode)",
        "Kvantum type (kode)",
        "Rundvekt",
    ]
    df = df[columns].drop_duplicates()
    df[time_column] = pd.to_datetime(df[time_column], dayfirst=True, format="mixed")
    return df


def _prepare_dataframe_for_fishing_trips(
    df_dep: DataFrame, df_por: DataFrame, vessel_id
) -> tuple[DataFrame, DataFrame]:
    dep = df_dep[df_dep["Radiokallesignal (ERS)"] == vessel_id]
    agg_func = {
        "Melding ID": "first",
        "Radiokallesignal (ERS)": "first",
        "Avgangstidspunkt": "first",
        "Kvantum type (kode)": "first",
        "Havn (kode)": "first",
        "Rundvekt": "sum",
    }
    dep_out = dep.groupby("Melding ID", as_index=False).aggregate(agg_func)
    dep_out = dep_out.sort_values("Avgangstidspunkt")

    por = df_por[df_por["Radiokallesignal (ERS)"] == vessel_id]
    agg_func = {
        "Melding ID": "first",
        "Radiokallesignal (ERS)": "first",
        "Ankomsttidspunkt": "first",
        "Kvantum type (kode)": "first",
        "Rundvekt": "sum",
    }
    por_out = por.groupby(
        ["Melding ID", "Kvantum type (kode)"], as_index=False
    ).aggregate(agg_func)
    por_out = por_out.pivot(
        index="Melding ID", columns="Kvantum type (kode)", values="Rundvekt"
    )
    por_out = por_out.join(
        por[
            ["Melding ID", "Radiokallesignal (ERS)", "Ankomsttidspunkt", "Havn (kode)"]
        ].set_index("Melding ID"),
        on="Melding ID",
    ).drop_duplicates()
    por_out = por_out.sort_values("Ankomsttidspunkt")

    return dep_out, por_out


def _prepare_timestamps(df_dep: DataFrame, df_por: DataFrame) -> DataFrame:
    """
    Combines the dataframes and sorts all entries by
    their timestamps in ascending order.
    """
    time_stamps = pd.concat([df_dep, df_por])
    time_stamps["Type"] = np.where(time_stamps["Avgangstidspunkt"].isna(), "POR", "DEP")
    time_stamps["Timestamp"] = np.where(
        time_stamps["Avgangstidspunkt"].isna(),
        time_stamps["Ankomsttidspunkt"],
        time_stamps["Avgangstidspunkt"],
    )
    time_stamps = (
        time_stamps.sort_values("Timestamp").reset_index().drop("index", axis=1)
    )
    return time_stamps


def _create_single_trip(start: Series, end: Series) -> Series:
    common_cols = [
        "Melding ID",
        "Timestamp",
        "Type",
        "Rundvekt",
        "KG",
        "OB",
        "Kvantum type (kode)",
    ]
    start = start.drop(common_cols + ["Ankomsttidspunkt", "Radiokallesignal (ERS)"])
    start = start.rename({"Havn (kode)": "Havn_start (kode)"})
    end = end.drop(common_cols + ["Avgangstidspunkt"])
    end = end.rename({"Havn (kode)": "Havn_slutt (kode)"})

    trip = pd.concat([start, end])
    return trip


def _define_fishing_trips(time_stamps: DataFrame) -> DataFrame:
    """
    Defines fishing trips for a vessel given a dataframe that is sorted by timestamps.
    """
    trips = []
    start: None | Series = None
    end: None | Series = None
    for _, data in time_stamps.iterrows():
        if start is None and data["Type"] == "DEP":
            start = data

        if start is not None and data["Type"] == "POR" and data["KG"] == data["OB"]:
            end = data

        if end is not None and data["Type"] == "DEP":
            trips.append(_create_single_trip(start, end))
            start = data
            end = None

    # Add the remaining trip
    if start is not None and end is not None:
        trips.append(_create_single_trip(start, end))

    return pd.concat(trips, axis=1).T


def define_fishing_trips_all_vessels(
    dep_data: DataFrame, por_data: DataFrame
) -> DataFrame:
    """
    Defines fishing trips for all unique vessels.
    """
    trips_vessel = []
    print("Total unique vessels: ", len(dep_data["Radiokallesignal (ERS)"].unique()))
    for vessel in dep_data["Radiokallesignal (ERS)"].unique():
        df_dep, df_por = _prepare_dataframe_for_fishing_trips(
            dep_data, por_data, vessel
        )

        # Skip vessels that does not contain KG or OB in POR data
        if "KG" not in df_por.columns:
            print("KG not in vessel: ", vessel)
            continue
        elif "OB" not in df_por.columns:
            print("OB not in vessel: ", vessel)
            continue

        time_stamps = _prepare_timestamps(df_dep, df_por)
        trips = _define_fishing_trips(time_stamps)
        trips_vessel.append(trips)

    all_trips = pd.concat(trips_vessel).reset_index(drop=True)
    all_trips["trip_id"] = all_trips["Radiokallesignal (ERS)"] + (
        all_trips["Avgangstidspunkt"].apply(lambda x: x.timestamp())
        + all_trips["Ankomsttidspunkt"].apply(lambda x: x.timestamp())
    ).astype(int).astype(str)
    return all_trips


def main(args) -> None:
    dep_data = prepare_data(read_and_combine(args.dep_path), "Avgangstidspunkt")
    por_data = prepare_data(read_and_combine(args.por_path), "Ankomsttidspunkt")
    trips = define_fishing_trips_all_vessels(dep_data, por_data)
    trips.to_csv(args.target_csv, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to define fishing trips fro DEP and POR data.\
        Can be used as a standalone script, or imported as a python module"
    )
    parser.add_argument("dep_path", help="Path to directory containing DEP data")
    parser.add_argument("por_path", help="Path to directory containing POR data")
    parser.add_argument("target_csv", help="Path to csv file where results are stored")
    args = parser.parse_args()

    main(args)
