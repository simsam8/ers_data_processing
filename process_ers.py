#!/usr/bin/env python3
import argparse
import os

import numpy as np
import pandas as pd


def process_ers_data(dca_data: pd.DataFrame):
    """
    Reduces and transforms ERS data.
    """

    keep_columns = [
        "Melding ID",
        "Meldingstidspunkt",
        "Starttidspunkt",
        "Stopptidspunkt",
        "Radiokallesignal (ERS)",
        "Varighet",
        "Startposisjon bredde",
        "Startposisjon lengde",
        "Havdybde start",
        "Stopposisjon bredde",
        "Stopposisjon lengde",
        "Havdybde stopp",
        "Trekkavstand",
        "Redskap FAO (kode)",
        "Hovedart FAO",
        "Art FAO",
        "Rundvekt",
        "Bruttotonnasje 1969",
        "Bruttotonnasje annen",
        "Bredde",
        "Fartøylengde",
        "Hovedområde start",
        "Hovedområde stopp",
    ]

    reduced_data = dca_data[keep_columns]

    # Keep only OTB (bottom trawl) and drop rows with no species information
    reduced_data = reduced_data.where(reduced_data["Redskap FAO (kode)"] == "OTB")
    reduced_data = reduced_data.dropna(subset=["Art FAO"])

    # Sum the round weights for message id, start time, and stop time
    catch_sums = reduced_data.groupby(
        ["Melding ID", "Starttidspunkt", "Stopptidspunkt"]
    )["Rundvekt"].sum()

    # Check for duplicates
    reduced_data.duplicated(
        ["Melding ID", "Starttidspunkt", "Stopptidspunkt", "Art FAO"]
    ).sum()

    # Create columns of round weight for each of 14 fish species + column for rest
    top_species = [
        "Torsk",
        "Sei",
        "Hyse",
        "Uer (vanlig)",
        "Dypvannsreke",
        "Lange",
        "Snabeluer",
        "Blåkveite",
        "Flekksteinbit",
        "Lysing",
        "Gråsteinbit",
        "Breiflabb",
        "Kveite",
        "Lyr",
    ]
    reduced_data = reduced_data.loc[reduced_data["Art FAO"].isin(top_species)]
    reduced_data_pivot = reduced_data.pivot(
        index=["Melding ID", "Starttidspunkt", "Stopptidspunkt"],
        columns="Art FAO",
        values="Rundvekt",
    ).reset_index()
    reduced_data_weight = reduced_data_pivot.merge(
        catch_sums, on=["Melding ID", "Starttidspunkt", "Stopptidspunkt"]
    )

    reduced_data_weight["ANDRE"] = reduced_data_weight.apply(
        lambda row: row["Rundvekt"] - row[top_species].sum(), axis=1
    )
    reduced_data_weight[top_species] = reduced_data_weight[top_species].replace(
        np.nan, 0
    )

    reduced_data = reduced_data.drop(columns=["Art FAO", "Rundvekt"]).drop_duplicates()

    # Merge datasets and combine tonnage columns
    complete_data = reduced_data.merge(
        reduced_data_weight, on=["Melding ID", "Starttidspunkt", "Stopptidspunkt"]
    )
    complete_data[["Bruttotonnasje 1969", "Bruttotonnasje annen"]] = complete_data[
        ["Bruttotonnasje 1969", "Bruttotonnasje annen"]
    ].replace(np.nan, 0)
    complete_data["Bruttotonnasje"] = complete_data.apply(
        lambda row: row["Bruttotonnasje 1969"] + row["Bruttotonnasje annen"], axis=1
    )
    complete_data.drop(
        columns=["Bruttotonnasje 1969", "Bruttotonnasje annen"], inplace=True
    )

    complete_data = complete_data.sort_values(
        ["Meldingstidspunkt", "Starttidspunkt"], ignore_index=True
    )

    # message_ids = complete_data["Melding ID"].unique()
    call_signs = complete_data["Radiokallesignal (ERS)"].unique()
    complete_data["Starttidspunkt"] = pd.to_datetime(
        complete_data["Starttidspunkt"], format="mixed", dayfirst=True
    )
    complete_data["Stopptidspunkt"] = pd.to_datetime(
        complete_data["Stopptidspunkt"], format="mixed", dayfirst=True
    )

    # Drop time overlapping messages for each vessel
    all_messages = []
    for c_sign in call_signs:
        messages = complete_data.where(
            complete_data["Radiokallesignal (ERS)"] == c_sign
        ).dropna(how="all")
        i = 0
        len_df = len(messages)
        while i < len_df - 1:
            # Message ID can be same or different
            if (
                messages.iloc[i + 1]["Starttidspunkt"]
                < messages.iloc[i]["Stopptidspunkt"]
                and messages.iloc[i + 1]["Starttidspunkt"]
                >= messages.iloc[i]["Starttidspunkt"]
            ):
                messages = messages.drop(messages.index[i + 1], inplace=False)
                len_df -= 1
            i += 1
        all_messages.append(messages)

    complete_data_no_dupes = pd.concat(all_messages)

    complete_data_no_dupes["Trekkavstand"] = complete_data_no_dupes[
        "Trekkavstand"
    ].replace(np.nan, 0)

    # Drop rows where area is nan
    complete_data_no_dupes = complete_data_no_dupes.dropna(
        subset=["Hovedområde start", "Hovedområde stopp"]
    )

    df = complete_data_no_dupes
    df = df.sort_values("Starttidspunkt")
    df["Meldingstidspunkt"] = pd.to_datetime(
        df["Meldingstidspunkt"], format="mixed", dayfirst=True
    )

    return df


def save_by_month(df: pd.DataFrame, column: str, dest: str):
    """
    Takes a dataframe, groups it and saves by month using the given
    column.

    Parameters:
    df: Dataframe
    column: Datatime column to group by
    dest: Destination folder
    """

    groups = df.groupby(pd.Grouper(key=column, freq="ME"))
    dfs_by_month = [month for _, month in groups]

    for month in dfs_by_month:
        month.index = pd.DatetimeIndex(month[column])

    month_map = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }

    for month_n in dfs_by_month:
        year = month_n.index.year[0]
        month = month_n.index.month[0]
        month_n.to_csv(f"{dest}/{year}_{month_map[month]}.csv", index=False)


def main(args):
    if args.is_dir:
        dca_frames = []
        for dca_file in os.listdir(args.path):
            if dca_file.endswith(".csv"):
                df = pd.read_csv(
                    os.path.join(args.path, dca_file),
                    sep=";",
                    decimal=",",
                    low_memory=False,
                )
                dca_frames.append(df)

        dca_data = pd.concat(dca_frames)
    else:
        dca_data = pd.read_csv(args.path, sep=";", decimal=",")

    my_data = process_ers_data(dca_data)
    if args.combine:
        my_data.to_csv(os.path.join(args.target_dir, "combined.csv"), index=False)

    save_by_month(my_data, "Starttidspunkt", dest=args.target_dir)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Script to process ERS data. Can be used as standalone script,\
        or imported as a python module."
    )
    parser.add_argument("path", help="Path to file(or directory) containing ERS data")
    parser.add_argument("target_dir", help="Path to directory where results are stored")
    parser.add_argument(
        "-d", "--is_dir", action="store_true", help="Read a directory instead of a file"
    )
    parser.add_argument(
        "-c",
        "--combine",
        action="store_true",
        help="Save an additional file with all data combined in one csv file.",
    )
    args = parser.parse_args()

    main(args)
