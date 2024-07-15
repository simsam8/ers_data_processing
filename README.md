# ERS Data pre-processing

This project includes code for pre-processing ERS-data and AIS-data
from [Fiskeridirektoratet](https://www.fiskeridir.no/Tall-og-analyse/AApne-data/elektronisk-rapportering-ers).

## Content

- `process_ers.py`: python script/module for pre-processing
- `process_ais.py`: python script/module for processing and marking AIS data
- `visualization.ipynb`: notebook for visualization of data 

## How to use

### process_ers.py

The file `process_ers.py` can be run as script or used as a python module.

#### As script

The script has the following arguments:

- `path`: path to file(or directory) containing ERS data
- `target_dir`: path to directory where results are stored
- `-d`, `--is_dir`(optional): reads the first argument as a directory
    instead of a file 
- `-c`, `--combine`(optional): saves an additional file with all data 
    combined into a single csv file


#### As module

The module contains two functions:

- `process_ers_data`: processes a dataframe containing ERS data
- `save_by_month`: groups the given dataframe into months by the 
    given datetime column, and saves them as individual files to the target directory


### process_ais.py

#### As script

The script has the following arguments:

- `path`: path to file(or directory) containing zipped AIS data
- `target_dir`: path to directory where results are stored
- `--dca_path`: path to DCA data created from `process_ers.py`
- `--mmsi_path`: path to MMSI data in xlsx format
- `-d`, `--is_dir`(optional): reads the first argument as a directory
    instead of a file 
- `-z`, `--zip`(optional): zips the resulting directories


#### As module

- `get_dca_with_mmsi`: Connects MMSI to DCA data, and returns time interval of DCA and 
    mmsi number.
- `process_ais`: Processes a single file with AIS data.
- `mark_ais_fishing`: Processes a whole year of AIS data, saves to destination.
- `unzip_ais`: Unzips archived AIS data.
- `zip_ais_directory`: Zip marked AIS data.



