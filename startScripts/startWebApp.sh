#!/bin/bash
# this script enables user to run the code in this repo 
# using the virtual environment
virtualEnvironName="emailEnv"
THIS_FILE_DIR="$(readlink -fm $0/..)"
rootDir="$(readlink -fm ${THIS_FILE_DIR}/..)"
virtualEnvironDir=${rootDir}/${virtualEnvironName}
pythonLocation=${virtualEnvironDir}/Scripts/python.exe

${pythonLocation} -c """
import os, sys
from backend.src.webApp import sys, WebApp
client = WebApp()
"""
