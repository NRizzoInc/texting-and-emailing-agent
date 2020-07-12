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
from backend.src.emailAgent import sys, EmailAgent
while (len(sys.argv) < 4):
    sys.argv.append('')
sys.argv[1] = '$1'
sys.argv[2] = '$2'
sys.argv[3] = '$3'
client = EmailAgent()
client.start()
"""
