#!/usr/bin/env python3
import argparse
import os
from zipfile import ZipFile


def _move_to_dir(zObject: ZipFile, filename, target_path):
    if filename[-7:-4] in ["dca", "por", "dep", "tra"]:
        zObject.extract(filename, os.path.join(target_path, filename[-7:-4]))


def extract_ers(path: str, target_path: str):
    ers_types = ["dca", "por", "dep", "tra"]
    for ers_type in ers_types:
        type_path = os.path.join(target_path, ers_type)
        if not os.path.exists(type_path):
            os.mkdir(type_path)

    for ers_zip in os.listdir(path):
        if ers_zip.endswith(".zip"):
            with ZipFile(os.path.join(path, ers_zip), "r") as zObject:
                for info in zObject.infolist():
                    _move_to_dir(zObject, info.filename, target_path)


def main(args):
    extract_ers(args.data_path, args.target_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extracts ERS data and organizes the data types\
        into directories in the target directory."
    )
    parser.add_argument("data_path", help="Directory containing raw ERS data.")
    parser.add_argument("target_path", help="Path to target directory.")
    args = parser.parse_args()
    main(args)
