#!/bin/bash
# this script enables user to run the code in this repo 
# using the virtual environment
virtualEnvironName="emailEnv"
THIS_FILE_DIR="$(readlink -fm $0/..)"
rootDir="$(readlink -fm ${THIS_FILE_DIR}/..)"
virtualEnvironDir="${rootDir}/${virtualEnvironName}"
pythonLocation="" # global (changed based on OS)

# check OS... (decide how to call python)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # windows
    pythonLocation=${virtualEnvironDir}/Scripts/python.exe
else
    # linux
    activateLocation=${virtualEnvironDir}/bin/activate
    pythonLocation=${virtualEnvironDir}/bin/python # NOTE: don't use ".exe"
fi

${pythonLocation} -c """
import os, sys
from backend.src.webApp.webApp import sys, WebApp
client = WebApp()
"""
