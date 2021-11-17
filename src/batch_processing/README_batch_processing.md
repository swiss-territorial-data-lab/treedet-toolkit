First use the toolbox provided, you may add it to any ArcGis Pro project.

Inside the toolbox, you will find the "detectFiles" script, it should be linked to the "detectFiles.py" python script.
If for some reason you cannot import the tool, you may create another one, link it to the python script, and set the following parameters, (the order matters)

![image](https://user-images.githubusercontent.com/93572721/142226467-7bf06b84-4fbc-48f9-aa50-1311c6558d85.png)

Run the tool in arcgis, and you should get a bunch of .yaml files in your selected output folder.

You can then use batchEv.py (inside the batch_processing folder) to run the detection algorithm on all of these .yaml config files all at once.

Use the same virtual environment, except this time you simply input the "python batchEv.py" command. No additional argument. You have to be inside the "batch_processing" folder. You will then be prompted for the folder where all the .yaml files you wish to process are located.
