#!/usr/bin/env python3
import argparse
import os
from datetime import datetime
from zipfile import ZipFile

import numpy as np
import pandas as pd
from pandas import DataFrame


def get_dca_with_mmsi(dca_data_path: str, mmsi_data_path: str) -> DataFrame:
    """
    Merges dca and mmsi data.
    Returns a dataframe with DCA start and stop times
    as well as the mmsi and duration.

    Parameters:
    -----------
    dca_data_path: path to dca data
    mmsi_data_path: path to mmsi data
    """
    dca_data = pd.read_csv(dca_data_path)
    mmsi_data = pd.read_excel(mmsi_data_path)
    mmsi_data = mmsi_data[["mmsi", "kallesignal"]]

    merged = dca_data.merge(
        mmsi_data, left_on="Radiokallesignal (ERS)", right_on="kallesignal"
    ).drop(columns=["kallesignal"])
    merged["Starttidspunkt"] = pd.to_datetime(merged["Starttidspunkt"])
    merged["Stopptidspunkt"] = pd.to_datetime(merged["Stopptidspunkt"])
    return merged[["Starttidspunkt", "Stopptidspunkt", "mmsi", "Varighet"]]


def get_fish_trips_with_mmsi(
    fish_trip_data_path: str, mmsi_data_path: str
) -> DataFrame:
    """
    Merges fishing trip data and mmsi data.
    Returns a dataframe with DCA start and stop times
    as well as the mmsi and trip id.

    Parameters:
    -----------
    fish_trip_data_path: path to fishing trips data
    mmsi_data_path: path to mmsi data
    """
    ft = pd.read_csv(fish_trip_data_path)
    mmsi_data = pd.read_excel(mmsi_data_path)
    mmsi_data = mmsi_data[["mmsi", "kallesignal"]]

    merged = ft.merge(mmsi_data, left_on="ERS", right_on="kallesignal").drop(
        columns=["kallesignal"]
    )
    merged["Avgangstidspunkt"] = pd.to_datetime(merged["Avgangstidspunkt"])
    merged["Ankomsttidspunkt"] = pd.to_datetime(merged["Ankomsttidspunkt"])
    return merged[["Avgangstidspunkt", "Ankomsttidspunkt", "mmsi", "trip_id"]]


def _calculate_in_interval(
    chunk, other, start_column: str, stop_column: str
) -> np.ndarray:
    """
    Helper function to check if an AIS row is in the interval
    of any of the rows of the other dataframe.
    Start and stop columns are found in the other dataframe.
    """

    dates = chunk["date_time_utc"].values
    chunk_mmsi = chunk["mmsi"].values
    other_mmsi = other["mmsi"].values
    start_times = other[start_column].values
    stop_times = other[stop_column].values

    # Use broadcasting to create a boolean array where True
    # means the date is in the interval
    is_in_start = dates[:, None] >= start_times
    is_in_stop = dates[:, None] <= stop_times
    same_mmsi = chunk_mmsi[:, None] == other_mmsi
    is_in_interval = (is_in_start & is_in_stop) & same_mmsi
    return is_in_interval


def _apply_marks(chunk, dca_slice, fishing_trips) -> DataFrame:
    """
    Helper function to mark AIS row with DCA duration and fishing state,
    and fishing trip id.
    """
    trip_ids = fishing_trips["trip_id"].values
    duration = dca_slice["Varighet"].values

    is_in_interval_trip = _calculate_in_interval(
        chunk, fishing_trips, "Avgangstidspunkt", "Ankomsttidspunkt"
    )
    is_in_interval_dca = _calculate_in_interval(
        chunk, dca_slice, "Starttidspunkt", "Stopptidspunkt"
    )

    # Initialize the duration column with NaN
    chunk["trip_id"] = np.nan
    chunk["duration"] = np.nan

    # Assign the duration and trip id where the interval is True
    for i in range(len(chunk)):
        if is_in_interval_dca[i].any():
            chunk.loc[i, "duration"] = duration[is_in_interval_dca[i]].max()
        if is_in_interval_trip[i].any():
            chunk.loc[i, "trip_id"] = trip_ids[is_in_interval_trip[i]].max()

    chunk["fishing"] = is_in_interval_dca.any(axis=1)
    return chunk


def process_ais(
    file_path: str, dca_data: DataFrame, fishing_trips: DataFrame
) -> DataFrame:
    """
    Process a single compressed zip file with ais data,
    uses dca_data to mark with fishing information,
    and fishing trips to connect AIS with corresponding
    fishing trip.
    Returns marked ais data.

    Parameters:
    -----------
    file_path: path to AIS data
    dca_data: dataframe with dca data
    fishing_trips: dataframe with fishing trip data
    """
    # Read AIS file
    column_dtypes = {
        "mmsi": int,
        "date_time_utc": object,
        "lon": float,
        "lat": float,
        "sog": float,
        "cog": float,
        "true_heading": int,
        "nav_status": int,
        "message_nr": int,
    }
    ais_data = pd.read_csv(file_path, sep=";", dtype=column_dtypes, compression="zip")
    ais_data["date_time_utc"] = pd.to_datetime(ais_data["date_time_utc"])

    # Get date from AIS filename and, filter DCA data and fishing trips
    ais_date = os.path.basename(file_path)[4:-4]
    dca_slice = dca_data.where(
        dca_data["Starttidspunkt"].dt.date
        == datetime.strptime(ais_date, "%Y%m%d").date()
    ).dropna()
    fish_trip_slice = fishing_trips.where(
        fishing_trips["Avgangstidspunkt"].dt.date
        == datetime.strptime(ais_date, "%Y%m%d").date()
    ).dropna()

    result = _apply_marks(ais_data, dca_slice, fish_trip_slice)
    return result


def process_ais_folder(
    ais_data_path: str,
    dca_date_slice: DataFrame,
    fishing_trips: DataFrame,
    save_destination: str,
):
    """
    Reads all files from folder containing AIS data, marks fishing status,\
    and saves to destination.
    """
    ais_list = os.listdir(ais_data_path)
    for i, ais_day in enumerate(ais_list):
        if ais_day.endswith(".zip"):
            print(i, end=" ")
            ais_df = process_ais(
                os.path.join(ais_data_path, ais_day), dca_date_slice, fishing_trips
            )
            filename = f"{ais_day[:-4]}"
            if not os.path.exists(save_destination):
                os.mkdir(save_destination)
            ais_df.to_parquet(f"{save_destination}/{filename}.parquet")


def unzip_ais(file_path: str, destination: str | None = None) -> None:
    """
    Unzip folder with AIS data.
    If destination is not set, unzips
    to the same directory with the same name.
    """
    if destination is None:
        destination = file_path[:-4]
    with ZipFile(file_path, "r") as zObject:
        zObject.extractall(destination)


def zip_ais_directory(dir_to_zip: str, destination: str) -> None:
    """
    Zip a directory to the destination zipfile
    """
    with ZipFile(destination, "w") as zObject:
        for folder_name, _, file_names in os.walk(dir_to_zip):
            for filename in file_names:
                f_path = os.path.join(folder_name, filename)
                zObject.write(f_path, os.path.basename(f_path))


def main(args) -> None:

    dca_data = get_dca_with_mmsi(args.dca_path, args.mmsi_path)
    fishing_trips = get_fish_trips_with_mmsi(args.f_trips_path, args.mmsi_path)
    if args.is_dir:
        # Unzip
        print("Unzipping...")
        for ais_zip in os.listdir(args.path):
            if ais_zip.endswith(".zip"):
                unzip_ais(os.path.join(args.path, ais_zip))
                print(f"Unzipped {ais_zip}")

        # Read and process
        print("Processing and marking...")
        for ais_dir in os.listdir(args.path):
            if ais_dir.startswith("AIS") and not ais_dir.endswith(".zip"):
                filepath_dir = os.path.join(args.path, ais_dir)
                target_dir = os.path.join(args.target_dir, ais_dir)
                process_ais_folder(filepath_dir, dca_data, fishing_trips, target_dir)
                print(f"Finished marking {ais_dir}.")
                if args.zip:
                    zip_ais_directory(target_dir, f"{target_dir}.zip")
                    print(f"Rezipped {target_dir}")

    else:
        print("Unzipping...")
        unzip_ais(args.path)
        ais_dir = args.path[:-4]
        print("Processing and marking...")
        process_ais_folder(ais_dir, dca_data, fishing_trips, args.target_dir)
        if args.zip:
            print("Zipping...")
            zip_ais_directory(args.target_dir, f"{args.target_dir}.zip")

    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to mark AIS data with information about fishing trip.\
        Can be used as a standalone script, or imported as a python module."
    )
    parser.add_argument(
        "path", help="Path to file(or directory) containing zipped AIS data"
    )
    parser.add_argument("target_dir", help="Path to directory where results are stored")
    parser.add_argument(
        "--dca_path", help="Path to DCA data created from process_ers.py", required=True
    )
    parser.add_argument(
        "--f_trips_path", help="Path to fishing trips data", required=True
    )
    parser.add_argument(
        "--mmsi_path", help="Path to MMSI data in xlsx format", required=True
    )
    parser.add_argument(
        "-d", "--is_dir", action="store_true", help="Read a directory instead of a file"
    )
    parser.add_argument("-z", "--zip", action="store_true", help="Zip marked AIS data")
    args = parser.parse_args()

    main(args)
