# -*- coding: utf-8 -*-

import os

# Importation du module arcpy
import arcpy
from arcpy.sa import *

arcpy.overwriteoutput = 1


# Workspace
Workspace = arcpy.GetParameterAsText(0)
# Folder containing your input files.
folderPath = arcpy.GetParameterAsText(1)
# File extension to detect
fileExtension = arcpy.GetParameterAsText(2)
# Do you want to define projection for detected files ?
projectionBool = arcpy.GetParameterAsText(3)
# Coordinate system to project to.
chosenEPSG = arcpy.GetParameterAsText(4)
# Choose whether to generate YAML config files or not.
YAMLbool = arcpy.GetParameterAsText(5)
# Choose where to generate YAML config files.
YAMLpath = arcpy.GetParameterAsText(6)
# Input GT sectors file(s)
inputGTsectors = arcpy.GetParameterAsText(7)
#Input GT trees file(s)
inputGTtrees = arcpy.GetParameterAsText(8)
# Output files folder path
outputPath = arcpy.GetParameterAsText(9)
# GT sectors buffer size [m]
GTbuffer = arcpy.GetParameterAsText(10)
# Tolerance [m]
tolerance = arcpy.GetParameterAsText(11)


# Set the current workspace
arcpy.env.workspace = Workspace


fileList = []

# List all files in selected folder.
for fileName in os.listdir(folderPath):
    # If the file name ends with the correct extension, 
    # it is added to the list of files to use later.
    if fileName.endswith(fileExtension):
        toAppend = folderPath + "\\" + fileName
        fileList.append(toAppend)

arcpy.AddMessage("{} detection files found in selected folder.".format(str(len(fileList))))


for chosenFile in fileList:
    if str(projectionBool) == "true":
        # Do define projection method on all files.
        arcpy.management.DefineProjection(chosenFile, chosenEPSG)

if str(projectionBool) == "true":
    arcpy.AddMessage("Projections successfully defined for all files.")

inputGTsectors = inputGTsectors.split(";")
inputGTtrees = inputGTtrees.split(";")


##################################
### Generate yaml config files ###
##################################

if str(YAMLbool) == "true":
    # For each detection file found in selected folder,
    # We write, line by line, its yaml config file.
    # Some lines refer to the current detection file's names.
    for chosenFile in fileList:
        # To get the name of a file from its path,
        # split the path with respect to the seperator, take the last element of the thusly created list
        # and replace the extension with an empty string (i.e. removing the extension)
        chosenFileName = chosenFile.split("\\")[-1].replace(fileExtension, "") 
        yamlFullPath = YAMLpath + "\\" + chosenFileName +"_config.yaml"
        with open(yamlFullPath, "w") as configFile:
            configFile.write("input_files:\n")
            configFile.write("  gt_sectors:\n")
            for GT_sectors_file in inputGTsectors:
                configFile.write("    - \"" + GT_sectors_file.replace("\\", "/") + "\"\n")
            configFile.write("  gt_trees:\n")
            for GT_trees_file in inputGTtrees:
                configFile.write("    - \"" + GT_trees_file.replace("\\", "/") + "\"\n")
            configFile.write("  detections:\n")
            configFile.write("    - \"" + chosenFile.replace("\\", "/") + "\"\n")
            configFile.write("output_files:\n")
            configFile.write("  tagged_gt_trees: \"" + outputPath.replace("\\", "/") + "/" + chosenFileName + "_tagGT.gpkg\"\n")
            configFile.write("  tagged_detections: \"" + outputPath.replace("\\", "/") + "/" + chosenFileName + "_tagDet.gpkg\"\n")
            configFile.write("  metrics: \"" + outputPath.replace("\\", "/") + "/" + chosenFileName + "_metrics.csv\"\n")
            configFile.write("settings:\n")
            configFile.write("  gt_sectors_buffer_size_in_meters: " + str(GTbuffer) + "\n")
            configFile.write("  tolerance_in_meters: " + str(tolerance) + "\n")

            arcpy.AddMessage("Successfully wrote YAML config file {} of {}.".format(str(fileList.index(chosenFile) + 1), str(len(fileList))))

