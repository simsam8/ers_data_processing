# ERS Data pre-processing

This project includes code for pre-processing ERS-data 
from [Fiskedirektoratet](https://www.fiskeridir.no/Tall-og-analyse/AApne-data/elektronisk-rapportering-ers).

## Content

- `process_ers.py`: python script/module for pre-processing
- `visualization.ipynb`: notebook for visualization of data 

## How to use

The file `process_ers.py` can be run as script or used as a python module.

### As script

The script has the following arguments:

- `filename`: path to file(or directory) containing ers data
- `target_dir`: path to directory where results are stored
- `-d`, `--is_dir`(optional): reads the first argument as a directory
    instead of a file 
- `-c`, `--combine`(optional): saves an additional file with all data 
    combined into a single csv file


### As module

The module contains two functions:

- `process_ers_data`: processes a dataframe containing ERS-data
- `save_by_month`: groups the given dataframe into months by the 
    given datetime column, and saves them as individual files to the target directory
