#!/usr/bin/env python3
import argparse
import os

import pandas as pd
from pandas import DataFrame


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


def main(args) -> None:
    dca_vessels = list(pd.read_csv(args.dca_path)["Radiokallesignal (ERS)"].unique())
    por_data = prepare_data(read_and_combine(args.por_path), "Ankomsttidspunkt")
    dep_data = prepare_data(read_and_combine(args.dep_path), "Avgangstidspunkt")

    por_data = por_data[por_data["Radiokallesignal (ERS)"].isin(dca_vessels)]
    dep_data = dep_data[dep_data["Radiokallesignal (ERS)"].isin(dca_vessels)]
    por_data.to_csv(args.target_dir + "por.csv", index=False)
    dep_data.to_csv(args.target_dir + "dep.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--dep_path", help="Path to DEP data")
    parser.add_argument("--por_path", help="Path to DEP data")
    parser.add_argument(
        "--target_dir", help="Path to directory where results are stored"
    )
    parser.add_argument("--dca_path", help="Path to processed dca")
    args = parser.parse_args()

    main(args)
