# STDL Tree Detection Toolkit

This repository hosts a collection of tools which were developed by the [STDL](https://www.stdl.ch/) within the frame of the Isolated Tree Detection Project.

## Assessment Scripts

### `src/assessment_scripts/det_vs_gt.py`

This script allows one to assess the quality of (semi-)automatic detections _versus_ Ground Truth (GT) data.

#### How-to

The script requires a configuration file as argument, for instance:  

```bash
$ python det_vs_gt.py <the configuration file (YAML format)>
```

The configuration file must comply with the [provided template](src/assessment_scripts/cfg_det_vs_gt_template.yaml), which is self-explanatory.
