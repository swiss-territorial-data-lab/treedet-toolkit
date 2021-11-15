import os, sys
import time
import argparse
import pandas as pd
import geopandas as gpd

from shapely.geometry import Point
from logzero import logger

def file_loader(full_path):

    COL_NAMES = [
        'Group id',
        'Point count',
        'Average easting',
        'Average northing',
        'Average z',
        'Ground z at average xy',
        'Trunk easting',
        'Trunk northing',
        'Trunk ground z',
        'Trunk diameter',
        'Canopy width',
        'Biggest distance',
        'Smallest distance',
        'Length',
        'Width',
        'Height'
    ]

    SEPARATOR = ','

    df = pd.read_csv(full_path, sep=SEPARATOR, names=COL_NAMES)

    return df

def gen_geometry(row, x_col_name, y_col_name):

    x, y = row[x_col_name], row[y_col_name]
    row['geometry'] = Point(x,y)
    
    return row


header = [
    'Group id',
    'Point count',
    'Average easting',
    'Average northing',
    'Average z',
    'Ground z at average xy',
    'Trunk easting',
    'Trunk northing',
    'Trunk ground z',
    'Trunk diameter',
    'Canopy width',
    'Biggest distance',
    'Smallest distance',
    'Length',
    'Width',
    'Height'
]

if __name__ == "__main__":

    tic = time.time()
    logger.info("Starting...")
    
    parser = argparse.ArgumentParser(description="This script turns TerraScan TXT output files into GeoPackage files.")
    parser.add_argument('--input-file', dest='in_file', type=str, help='input file')
    parser.add_argument('--output-folder', dest='out_folder', type=str, help='output folder')
    parser.add_argument('--epsg', dest='epsg', type=str, help='EPSG (ex.: 2056)')

    args = parser.parse_args()
    epsg = args.epsg if args.epsg is not None else '2056'
    in_file = args.in_file
    out_folder = args.out_folder

    if any([x is None for x in [in_file, out_folder]]):
        logger.critical("Invalid arguments. Exiting.")
        sys.exit(1)
    
    logger.info("> Loading input file...")
    df = file_loader(args.in_file)
    logger.info("< ...done.")

    gdf = gpd.GeoDataFrame(df)

    logger.info("> Generating geometries...")
    average_xy_gdf = gdf.apply(lambda row: gen_geometry(row, 'Average easting', 'Average northing'), axis=1)
    average_xy_gdf = average_xy_gdf.set_crs(epsg=epsg)

    trunk_xy_gdf =  gdf.apply(lambda row: gen_geometry(row, 'Trunk easting', 'Trunk northing'), axis=1)
    trunk_xy_gdf =  trunk_xy_gdf.set_crs(epsg=epsg)
    logger.info("< ...done.")

    basename = os.path.basename(in_file)
    filename, _ = os.path.splitext(basename)

    average_xy_filename = f"{filename}_average_xy.gpkg"
    trunk_xy_filename = f"{filename}_trunk_xy.gpkg"

    average_xy_file_fullpath = os.path.join(out_folder, average_xy_filename)
    trunk_xy_file_fullpath = os.path.join(out_folder, trunk_xy_filename)

    logger.info("> Exporting to GPKG...")
    average_xy_gdf.to_file(average_xy_file_fullpath, driver='GPKG')
    trunk_xy_gdf.to_file(trunk_xy_file_fullpath, driver='GPKG')
    logger.info("< ...done. The following files were written:")
    for x in [average_xy_file_fullpath, trunk_xy_file_fullpath]:
        print(x)