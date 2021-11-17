import os, sys

# the following lines allow us to import modules from within this file's parent folder
from inspect import getsourcefile
current_path = os.path.abspath(getsourcefile(lambda:0))
current_dir = os.path.dirname(current_path)
parent_dir = current_dir[:current_dir.rfind(os.path.sep)]
sys.path.insert(0, parent_dir)

from assessment_scripts import det_vs_gt
from tkinter import Tk 
from tkinter.filedialog import askdirectory
 
Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing 
yamlFolderPath = askdirectory() # show an "Open" dialog box and return the path to the selected file 

configFileList = []

# List all files in selected folder.
for fileName in os.listdir(yamlFolderPath):
    # If the file name ends with the correct extension, 
    # it is added to the list of files to use later.
    if fileName.endswith(".yaml"):
        toAppend = yamlFolderPath + "\\" + fileName
        configFileList.append(toAppend)

print("{} config files found in selected folder.".format(str(len(configFileList))))

for config in configFileList:
    det_vs_gt.main(config)

print("Batch evaluation successfully completed on {} config files.".format(str(len(configFileList))))