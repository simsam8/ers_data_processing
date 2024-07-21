# ERS Data pre-processing

This project includes code for processing ERS-data and AIS-data
from [Fiskeridirektoratet](https://www.fiskeridir.no/Tall-og-analyse/AApne-data/elektronisk-rapportering-ers).

## Content

- `process_dca.py`: script for processing DCA data.
- `process_fishing_trips.py`: script for defining fishing trips.
- `process_ais.py`: script for processing and marking AIS data
- `extract_ers_data.py`: script to automatically extract raw ERS data
- `visualization.ipynb`: notebook for visualization of data 

## How to use

### extract_ers_data.py

Intended to be used as a script to automatically extract ERS data.

Arguments:

- `data_path`: directory containing raw ERS data
- `target_path`: directory to store results


### process_dca.py

Arguments:

- `path`: path to file(or directory) containing DCA data
- `target_dir`: path to directory where results are stored
- `-d`, `--is_dir`(optional): reads the first argument as a directory
    instead of a file 
- `-c`, `--combine`(optional): saves an additional file with all data 
    combined into a single csv file

### process_fishing_trips.py

Arguments:

- `dep_path`: path to directory containing DEP data
- `por_path`: path to directory containing POR data
- `target_csv`: path to csv file where results are stored


### process_ais.py

Arguments:

- `path`: path to file(or directory) containing zipped AIS data
- `target_dir`: path to directory where results are stored
- `--dca_path`: path to DCA data created from `process_dca.py`
- `--f_trips_path`: path to fishing trips data
- `--mmsi_path`: path to MMSI data in xlsx format
- `-d`, `--is_dir`(optional): reads the first argument as a directory
    instead of a file 
- `-z`, `--zip`(optional): zips the resulting directories


## Example usage

Before using any of the scripts, the folder structure might 
look something like this.

```
data/
├── ais_data
│   ├── AIS_data_2015.zip
│   └── ...
├── MMSI_rc_20211027_.xlsx
└── raw
    ├── elektronisk-rapportering-ers-2011.zip
    └── ...
```

#### Extracting ERS

To extract the raw ERS data you can use the `extract_ers_data.py` like so:
```
./extract_ers_data.py data/raw data/
```

```
data/
├── ais_data
├── dca
│   ├── elektronisk-rapportering-ers-2011-fangstmelding-dca.csv
│   └── ...
├── dep
│   ├── elektronisk-rapportering-ers-2011-avgangsmelding-dep.csv
│   └── ...
├── MMSI_rc_20211027_.xlsx
├── por
│   ├── elektronisk-rapportering-ers-2011-ankomstmelding-por.csv
│   └── ...
├── raw
└── tra
    ├── elektronisk-rapportering-ers-2011-overforingsmelding-tra.csv
    └── ...
```

#### Processing DCA

To process DCA data, you can either process a whole directory at once,
or a single file.

```
data/dca/
    ├── elektronisk-rapportering-ers-2011-fangstmelding-dca.csv
    └── ...

processed/dca/
    └── 
```

To process a whole directory,
```
./process_dca.py data/dca/ processed/dca/ -d
```

or a single file.
```
./process_dca.py data/dca/elektronisk-rapportering-ers-2011-fangstmelding-dca.csv processed/dca/
```

An additional flag `-c` can be added to store all DCA data in a single 
combined file `combined.csv`. This is useful when working with the other 
scripts that uses DCA data.
```
processed/dca/
    └── combined.csv
```


#### Processing Fishing trips

```
data/
├── dep
│   ├── elektronisk-rapportering-ers-2011-avgangsmelding-dep.csv
│   └── ...
└── por
    ├── elektronisk-rapportering-ers-2011-ankomstmelding-por.csv
    └── ...

processed/
```

The first to arguments are the directories for DEP and POR data. 
Then choose where to store the result csv file.

```
./process_fishing_trips.py data/dep/ data/por/ processed/fishing_trips.csv
```


#### Processing AIS data

```
data/
├── ais_data
│   ├── AIS_data_2015.zip
│   └── ...
└── MMSI_rc_20211027_.xlsx

processed/
├── ais
├── dca
│   ├── combined.csv
│   ├── 2020_January.csv
│   └── ...
└── fishing_trips.csv
```

The script needs processed DCA and fishing trip data, and a ERS to MMSI table.
You can read a whole directory of zipped AIS data with the `-d` flag,

```
./process_ais.py data/ais_data processed/ais --dca_path processed/dca/combined.csv \
--f_trips_path processed/fishing_trips.csv --mmsi_path data/MMSI_rc_20211027_.xlsx -d
```

or only a single zip file.

```
./process_ais.py data/ais_data processed/ais/AIS_data_2015.zip \
--dca_path processed/dca/combined.csv \
--f_trips_path processed/fishing_trips.csv --mmsi_path data/MMSI_rc_20211027_.xlsx
```

An additional flag `-z` can be added to zip compress the output.














