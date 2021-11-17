import det_vs_gt_experiments as ev

import os

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
    ev.main(config)

print("Batch evaluation successfully completed on {} config files.".format(str(len(configFileList))))