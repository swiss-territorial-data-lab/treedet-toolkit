# STDL Tree Detection Toolkit

This repository hosts a collection of tools which were developed by the [STDL](https://www.stdl.ch/) within the frame of the Isolated Tree Detection Project.

## Requirements

This toolkit was tested with Python 3.8. Provided that the `conda` executable is available (we recommend using [Miniconda](https://docs.conda.io/en/latest/miniconda.html)), the following commands allow one to set up a suitable virtual environment:

```bash
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
