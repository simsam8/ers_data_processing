#!/usr/bin/env python3
import argparse
import os
from datetime import datetime
from zipfile import ZipFile

import pandas as pd


def get_dca_with_mmsi(dca_data_path: str, mmsi_data_path: str):
    """
    Merges dca and mmsi data.
    Returns a dataframe with DCA start and stop times
    as well as the mmsi.

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
    return merged[["Starttidspunkt", "Stopptidspunkt", "mmsi"]]


def _process_chunk(
    ais_chunk,
    start_times,
    stop_times,
    dca_mmsi,
):
    """
    Intermediate function to check if ais datetime is
    in dca fishing interval.
    Returns ais data marked whether its fishing or not.
    """
    ais_dates = ais_chunk["date_time_utc"].values
    chunk_mmsi = ais_chunk["mmsi"].values

    # Use broadcasting to create a boolean array,
    # where True means the date is in the interval
    is_in_start = ais_dates[:, None] >= start_times
    is_in_stop = ais_dates[:, None] <= stop_times
    same_mmsi = chunk_mmsi[:, None] == dca_mmsi
    is_in_interval = (is_in_start & is_in_stop) & same_mmsi

    # Any interval containing the ais_date will have True in the row
    ais_chunk["fishing"] = is_in_interval.any(axis=1)
    return ais_chunk


def process_ais(file_path: str, dca_data: pd.DataFrame):
    """
    Process a single file with ais data,
    uses dca_data to mark whether it is fishing or not.
    Returns marked ais data.

    Parameters:
    -----------
    file_path: path to AIS data
    dca_data: dataframe with dca data
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

    # Get date from AIS filename and filter DCA data
    ais_date = os.path.basename(file_path)[4:-4]
    dca_slice = dca_data.where(
        dca_data["Starttidspunkt"].dt.date
        == datetime.strptime(ais_date, "%Y%m%d").date()
    ).dropna()

    # Convert interval times to numpy arrays
    start_times = dca_slice["Starttidspunkt"].values
    stop_times = dca_slice["Stopptidspunkt"].values
    dca_mmsis = dca_slice["mmsi"].values

    # print(f"{ais_date}, Size of AIS: {len(ais_data)}, Size of DCA: {len(dca_slice)}")
    result = _process_chunk(ais_data, start_times, stop_times, dca_mmsis)
    return result


def mark_ais_fishing(ais_data_path: str, dca_date_slice, save_destination: str) -> None:
    """
    Reads all ais data from a year, marks fishing status, and saves to destination.
    """
    ais_list = os.listdir(ais_data_path)
    if not os.path.exists(save_destination):
        os.mkdir(save_destination)
    for ais_day in ais_list:
        if ais_day.endswith(".zip"):
            ais_df = process_ais(os.path.join(ais_data_path, ais_day), dca_date_slice)
            filename = f"{ais_day[:-4]}"
            ais_df.to_parquet(f"{save_destination}/{filename}.parquet")


def unzip_ais(file_path, destination=None) -> None:
    """
    Unzip folder with AIS data.
    If destination is not set, unzips
    to the same directory with the same name.
    """
    if destination is None:
        destination = file_path[:-4]
    with ZipFile(file_path, "r") as zObject:
        zObject.extractall(destination)


def zip_ais_directory(dir_to_zip, destination):
    """
    Zip a directory to the destination zipfile
    """
    with ZipFile(destination, "w") as zObject:
        for folder_name, _, file_names in os.walk(dir_to_zip):
            for filename in file_names:
                f_path = os.path.join(folder_name, filename)
                zObject.write(f_path, os.path.basename(f_path))


def main(args):

    dca_data = get_dca_with_mmsi(args.dca_path, args.mmsi_path)
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
                mark_ais_fishing(filepath_dir, dca_data, target_dir)
                print(f"Finished marking {ais_dir}.")
                if args.zip:
                    zip_ais_directory(target_dir, f"{target_dir}.zip")
                    print(f"Rezipped {target_dir}")

    else:
        print("Unzipping...")
        unzip_ais(args.path)
        ais_dir = args.path[:-4]
        print("Processing and marking...")
        mark_ais_fishing(ais_dir, dca_data, args.target_dir)
        if args.zip:
            print("Zipping...")
            zip_ais_directory(args.target_dir, f"{args.target_dir}.zip")

    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to mark AIS data with fishing tag. Can be used as a \
        standalone script, or imported as a python module."
    )
    parser.add_argument(
        "path", help="Path to file(or directory) containing zipped AIS data"
    )
    parser.add_argument("target_dir", help="Path to directory where results are stored")
    parser.add_argument(
        "--dca_path", help="Path to DCA data created from process_ers.py", required=True
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
