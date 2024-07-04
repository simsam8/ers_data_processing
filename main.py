#!/usr/bin/env python3
import numpy as np
import pandas as pd


def process_ers_data(dca_data: pd.DataFrame):

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
        "Hovedområde start (kode)",
        "Hovedområde stopp (kode)",
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

    message_ids = complete_data["Melding ID"].unique()
    call_signs = complete_data["Radiokallesignal (ERS)"].unique()
    # print(call_signs)
    complete_data["Starttidspunkt"] = pd.to_datetime(
        complete_data["Starttidspunkt"], format="mixed"
    )
    complete_data["Stopptidspunkt"] = pd.to_datetime(
        complete_data["Stopptidspunkt"], format="mixed"
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
            # if (messages.iloc[i+1]["Melding ID"] == messages.iloc[i]["Melding ID"] and
            # Message ID can be same or different
            if (
                messages.iloc[i + 1]["Starttidspunkt"]
                < messages.iloc[i]["Stopptidspunkt"]
                and messages.iloc[i + 1]["Starttidspunkt"]
                >= messages.iloc[i]["Starttidspunkt"]
            ):
                # print(f"Overlap between: {messages.index[i]} and {messages.index[i+1]}")
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
        subset=["Hovedområde start (kode)", "Hovedområde stopp (kode)"]
    )

    df = complete_data_no_dupes
    df = df.sort_values("Starttidspunkt")
    df["Meldingstidspunkt"] = pd.to_datetime(df["Meldingstidspunkt"], format="mixed")

    return df


if __name__ == "__main__":
    dca_data = pd.read_csv(
        "data/elektronisk-rapportering-ers-2018-fangstmelding-dca.csv",
        sep=";",
        decimal=",",
    )

    my_data = process_ers_data(dca_data)

    my_data.to_csv("processed.csv", index=False)
