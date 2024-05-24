# SRC folder description

This folder contains the source code of the project and represent the entrypoint to edit and modify the Autonomic manager functionalities.

## dagster_service 
In this folder you can find the `dagster` project files, parameters and modules. 

Each module represent a solution implementation. 

The `commons` module contains a wide range of accessory functions that are shared with all the solutions


## orion_catcher
Here you find a folder called `solution_configs`, where the parameters of the modules are stored and the `main.py` where a FastAPI app enables the orion endpoints for each solution. 
