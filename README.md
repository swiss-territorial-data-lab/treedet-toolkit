# STDL Tree Detection Toolkit

This repository hosts a collection of tools which were developed by the [STDL](https://www.stdl.ch/) within the frame of the Isolated Tree Detection Project.

## Requirements

This toolkit was tested with Python 3.8. Provided that the `conda` executable is available (we recommend using [Miniconda](https://docs.conda.io/en/latest/miniconda.html)), the following commands allow one to set up a suitable virtual environment:

```bash
$ conda config --add channels conda-forge
$ conda create -n <the name of the virtual env> -c conda-forge python=3.8
$ conda activate <the name of the virtual env>
$ conda install --file requirements.txt
```

On Windows 10, we faced an ``ImportError: DLL load failed while importing'' error which could be fixed by issuing the following two extra commands:

```bash
$ pip uninstall pyproj && pip install pyproj
$ conda install --file requirements.txt
```

## Assessment Scripts

### `src/assessment_scripts/det_vs_gt.py`

This script allows one to assess the quality of (semi-)automatic detections _versus_ Ground Truth (GT) data.

#### How-to

The script requires a configuration file as argument, for instance:  

```bash
$ python det_vs_gt.py <the configuration file (YAML format)>
```

The configuration file must comply with the [provided template](src/assessment_scripts/cfg_det_vs_gt_template.yaml), which is self-explanatory.

## Data transformation scripts

### `src/data_transformers/ts_txt_to_gpkg.py`

This script turns TerraScan TXT output files into GeoPackages. Input files must comply to the following requirements:

* values must be comma-separated
* values must be arranged according to the following sequence: `Group id`, `Point count`, `Average easting`, `Average northing`, `Average z`, `Ground z at average xy`, `Trunk easting`, `Trunk northing`, `Trunk ground z`, `Trunk diameter`, `Canopy width`,`Biggest distance`, `Smallest distance`, `Length`, `Width`, `Height`

The script produces a couple of GeoPackage files: one in which XY geometries stem from the `Average easting` and `Average northing` fields; another one in which XY geometries stems from the `Trunk easting` and `Trunk northing` fields.

#### How-to

The script requires some input arguments. The list and description of such arguments can be obtained as follows: 

```bash
$ python ts_txt_to_gpkg.py -h
```

### `src/data_transformers/gis_to_las.py`

This script generate a LAS file out of any GIS file readable by GeoPandas (SHP, GeoPackage, GeoJSON, ...). It implements some opinions which hold in the frame of the STDL TreeDet Project:

* the input file must concern the territory of the Canton of Geneva, for which a DEM is accessible through a Web Service (the URL and query string are hard-coded in the script).
* Output z coordinates are set according to the DEM. A +1 m offset is added.
* The input file should include the columns `group_id`, `TP_charge` and `FP_charge`/`FN_charge`. Values along these columns are copied to the output LAS.
* Polygonal geometries are summarized by their centroid.
* The following colors are used:

    | Color  | (R, G, B)     | Used for              |  
    | ------ | ------------- | --------------------- |
    | Bright Green | (102, 255, 0) | True Positive (TP) GT trees | 
    | Bud Green | (123, 182, 97) | True Positive (TP) detections |
    | Blue | (255, 0, 0) | False Negative (FN) GT trees |
    | Red | (255, 0, 0) | False Positive (FP) detections |
    | Gray | (128, 128, 128) | Unknown | 

    For mixed TP/FP or TP/FN items, the above base colors are weighted by the charge. For instance, if `TP_charge = 1/4` and `FN_charge = 3/4`, then the item will have the color `(63, 0, 191) = 1/4 x (255, 0, 0) + 3/4 x (0, 0, 255)`.

#### How-to

The script requires some input arguments. The list and description of such arguments can be obtained as follows: 

```bash
$ python gis_to_las.py -h
```