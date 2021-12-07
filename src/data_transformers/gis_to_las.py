import os, sys
import time
import argparse
import pandas as pd
import geopandas as gpd
import requests
import laspy
import numpy as np

from shapely.geometry import Point
from logzero import logger
from tqdm.auto import tqdm
from fractions import Fraction

tqdm.pandas()


# CONSTANTS
BRIGHT_GREEN = (102, 255, 0)
BUD_GREEN = (123, 182, 97)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

LAS_CLASS = 17


def file_loader(full_path):

    gdf = gpd.read_file(full_path)#, sep=SEPARATOR, names=COL_NAMES)

    return gdf


def get_z(x, y):

    url = f"https://ge.ch/sitgags2/rest/services/RASTER/MNA_TERRAIN/ImageServer/getSamples?geometry={x},{y}&geometryType=esriGeometryPoint&sampleDistance=&sampleCount=&mosaicRule=&pixelSize=&returnFirstValueOnly=true&f=json"
    
    res = requests.get(url)
    data = res.json()
    z = data['samples'][0]['value']
    time.sleep(0.1)
    
    return float(z) 

def add_z(row):
    
    x = row.geometry.x
    y = row.geometry.y
    
    z = get_z(x, y)
    
    row['x'] = float(x)
    row['y'] = float(y)
    row['z'] = z
    row['geometry'] = Point(x, y, z)
    
    return row

def add_rgb(row):
    
    if ('FP_charge' in row) and ('TP_charge' in row):
        # det
        row['r'], row['g'], row['b'] = (Fraction(row.FP_charge) * np.array(RED) + Fraction(row.TP_charge) * np.array(BUD_GREEN)).astype(np.int32)
    elif ('FN_charge' in row) and ('TP_charge' in row):
        # GT
        row['r'], row['g'], row['b'] = (Fraction(row.FN_charge) * np.array(BLUE) + Fraction(row.TP_charge) * np.array(BRIGHT_GREEN)).astype(np.int32)
    else:
        row['r'], row['g'], row['b'] = GRAY

    return row


def add_z_offset(row):

    if ('FP_charge' in row) and ('TP_charge' in row):
        # det
        row['z_offset'] = 2.0
    elif ('FN_charge' in row) and ('TP_charge' in row):
        # GT
        row['z_offset'] = 1.0
    else:
        row['z_offset'] = 0.0

    return row


def gdf_to_las(gdf):

    header = laspy.LasHeader(point_format=2, version="1.4") # cf. https://laspy.readthedocs.io/en/latest/intro.html
    header.offsets = [gdf.x.min(), gdf.y.min(), gdf.z.min()]
    header.scales = np.array([1.0, 1.0, 1.0])
    if "group_id" in gdf.columns.tolist():
        header.add_extra_dim(laspy.ExtraBytesParams(name="group_id", type=np.int32))
    if "TP_charge" in gdf.columns.tolist():
        header.add_extra_dim(laspy.ExtraBytesParams(name="TP_charge", type=float))
    if "FP_charge" in gdf.columns.tolist():
        header.add_extra_dim(laspy.ExtraBytesParams(name="FP_charge", type=float))
    if "FN_charge" in gdf.columns.tolist():
        header.add_extra_dim(laspy.ExtraBytesParams(name="FN_charge", type=float))
    

    las = laspy.LasData(header)

    las.x = gdf.x
    las.y = gdf.y
    las.z = gdf.z + gdf.z_offset
    if "group_id" in gdf.columns.tolist():
        las.group_id = gdf.group_id.fillna(-1).astype(np.int32)

    if "TP_charge" in gdf.columns.tolist():
        las.TP_charge = gdf.TP_charge.fillna(-1).map(Fraction).astype(float)
    if "FP_charge" in gdf.columns.tolist():
        las.FP_charge = gdf.FP_charge.fillna(-1).map(Fraction).astype(float)
    if "FN_charge" in gdf.columns.tolist():
        las.FN_charge = gdf.FN_charge.fillna(-1).map(Fraction).astype(float)
    
    las.red = gdf.r
    las.green = gdf.g
    las.blue = gdf.b

    las.classification = [LAS_CLASS]*len(gdf)
    
    return las

if __name__ == "__main__":

    tic = time.time()
    logger.info("Starting...")
    
    parser = argparse.ArgumentParser(description="An opinionated script turning GIS files (SHP, GPKG, ...) into LAS.")
    parser.add_argument('--input-file', dest='in_file', type=str, help='input file')
    parser.add_argument('--output-folder', dest='out_folder', type=str, help='output folder')
    
    args = parser.parse_args()
    in_file = args.in_file
    in_basename =os.path.basename(in_file)
    in_filename, _ = os.path.splitext(in_basename)
    out_folder = args.out_folder

    if any([x is None for x in [in_file, out_folder]]):
        logger.critical("Invalid arguments. Exiting.")
        sys.exit(1)
    
    logger.info("> Loading input file...")
    gdf = file_loader(args.in_file)
    gdf['geometry'] = gdf.geometry.centroid
    logger.info("< ...done.")

    logger.info("> Replacing geometries by centroids...")
    gdf['geometry'] = gdf.geometry.centroid
    logger.info("< ...done.")

    logger.info("> Computing RGB values...")
    gdf = gdf.apply(add_rgb, axis=1)
    logger.info("< ...done.")

    logger.info("> Fetching z coordinates from remote DEM...")
    gdf_with_z = gdf.progress_apply(add_z, axis=1)
    logger.info("< ...done.")

    logger.info("> Computing offset along the z-coordinate...")
    gdf_with_z = gdf_with_z.apply(add_z_offset, axis=1)
    logger.info("< ...done.")

    logger.info("> Generating LAS...")
    las = gdf_to_las(gdf_with_z)
    assert len(las) == len(gdf)
    out_filename = f"{in_filename}.las"
    out_file = os.path.join(out_folder, out_filename)
    las.write(out_file)
    logger.info("< ...done.")
    
    
    print("The following file was written:")
    print(out_file)

    print()
    print("*** Please execute the following command if you also want to generate files compatible with Potree. ***")
    print("/!\\ Replace <path to PotreeConverter.exe> with the actual path and feel free to adapt the output folder name to your needs!")
    print()
    print(f"<path to PotreeConverter.exe> {out_file} -o {os.path.join(out_folder, in_filename)}" )