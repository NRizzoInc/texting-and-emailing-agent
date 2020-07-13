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

# have to be in root dir for this to work
cd ${rootDir}

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
