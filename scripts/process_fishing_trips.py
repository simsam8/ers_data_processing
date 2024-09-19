#!/usr/bin/env python3
import argparse
import os

import pandas as pd


def read_and_combine(data_folder):
    dframes = []
    for file in os.listdir(data_folder):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(data_folder, file), sep=";", low_memory=False)
            dframes.append(df)
    return pd.concat(dframes)


def prepare_data(df, time_column: str):
    columns = ["Melding ID", "Radiokallesignal (ERS)", time_column, "Havn (kode)"]
    df = df[columns].drop_duplicates()
    df[time_column] = pd.to_datetime(df[time_column], dayfirst=True, format="mixed")
    return df


def rearrange_trip_columns(trip_list):
    trip = pd.DataFrame(
        [
            [
                trip_list[0]["Radiokallesignal (ERS)"],
                trip_list[0]["Havn (kode)"],
                trip_list[0]["Avgangstidspunkt"],
                trip_list[-1]["Havn (kode)"],
                trip_list[-1]["Ankomsttidspunkt"],
            ]
        ],
        columns=[
            "ERS",
            "Havn_avgang",
            "Avgangstidspunkt",
            "Havn_ankomst",
            "Ankomsttidspunkt",
        ],
    )
    return trip


# NOTE: this function may need to be reworked, but it seems to work as intended
def define_fishing_trips(dep_df, por_df):
    """
    Defines all fishing trips for a vessel.
    """
    dep_df = dep_df.sort_values("Avgangstidspunkt")
    por_df = por_df.sort_values("Ankomsttidspunkt")
    fishing_trips = []

    # Initialize indices and state variables
    dep_idx, por_idx = 0, 0
    current_dep, current_por = None, None
    in_trip = False
    no_port = True
    current_trip = []

    if dep_df.empty or por_df.empty:
        return pd.DataFrame(
            columns=[
                "ERS",
                "Havn_avgang",
                "Avgangstidspunkt",
                "Havn_ankomst",
                "Ankomsttidspunkt",
            ]
        )

    # Iterate through the arrival dataframe
    while por_idx < len(por_df) and dep_idx < len(dep_df):
        if not in_trip:
            # If not currently in a trip, start a new trip
            if dep_idx < len(dep_df):
                current_dep = dep_df.iloc[dep_idx]
                current_trip = []
                current_trip.append(current_dep)
                in_trip, no_port = True, True
                dep_idx += 1
            else:  # No more departures left to process
                pass

        # Get the current arrival entry
        current_por = por_df.iloc[por_idx]

        # If the current arrival time is before the next departure time
        if (
            dep_idx < len(dep_df)
            and current_por["Ankomsttidspunkt"]
            < dep_df.iloc[dep_idx]["Avgangstidspunkt"]
        ):
            current_trip.append(current_por)
            por_idx += 1
            no_port = False
        else:
            # If no port was encountered before the next departure,
            # add the next departure
            if dep_idx < len(dep_df) and no_port:
                current_dep = dep_df.iloc[dep_idx]
                current_trip.append(current_dep)
                dep_idx += 1

            # Edge case when on the last departure, to add the last arrival
            # and finish trip
            elif (
                dep_idx == len(dep_df)
                and current_dep["Avgangstidspunkt"] < current_por["Ankomsttidspunkt"]
            ):
                current_trip.append(current_por)
                fishing_trips.append(rearrange_trip_columns(current_trip))
                current_trip = []
                in_trip = False
            else:  # End the current trip
                in_trip = False
                fishing_trips.append(rearrange_trip_columns(current_trip))
                current_trip = []

    # Add the last complete trip
    if in_trip and current_trip:
        try:
            fishing_trips.append(rearrange_trip_columns(current_trip))
        except KeyError:
            pass
    return (
        pd.concat(fishing_trips, ignore_index=True)
        if fishing_trips
        else pd.DataFrame(
            columns=[
                "ERS",
                "Havn_avgang",
                "Avgangstidspunkt",
                "Havn_ankomst",
                "Ankomsttidspunkt",
            ]
        )
    )


def define_fishing_trips_all_vessels(dep_data, por_data):
    """
    Define fishing trips for all vessels.
    """
    call_signs = dep_data["Radiokallesignal (ERS)"].unique()
    all_trips = []
    for c_sign in call_signs:
        dep = dep_data.where(dep_data["Radiokallesignal (ERS)"] == c_sign).dropna(
            how="all"
        )
        por = por_data.where(por_data["Radiokallesignal (ERS)"] == c_sign).dropna(
            how="all"
        )
        c_trips = define_fishing_trips(dep, por)
        all_trips.append(c_trips)

    trip_frame = pd.concat(all_trips)
    trip_frame = trip_frame.where(
        trip_frame["Avgangstidspunkt"] < trip_frame["Ankomsttidspunkt"]
    ).dropna(how="all")
    trip_frame = trip_frame.sort_values("Avgangstidspunkt")
    trip_frame = trip_frame.reset_index(drop=True)
    trip_frame["trip_id"] = trip_frame.index + 1
    return trip_frame


def main(args):
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
