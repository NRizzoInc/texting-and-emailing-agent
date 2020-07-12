#!/bin/bash
# this script enables user to run the code in this repo 
# using the virtual environment
THIS_FILE_DIR="$(readlink -fm $0/..)"
virtualEnvironName="emailEnv"
virtualEnvironDir=$THIS_FILE_DIR/$virtualEnvironName
pythonLocation=$virtualEnvironDir/Scripts/python.exe

$pythonLocation -c """
import os, sys
from backend.src.webApp import sys, WebApp
client = WebApp()
"""
