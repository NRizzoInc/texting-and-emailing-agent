#!/bin/bash
# this script enables user to run the code in this repo 
# using the virtual environment

# TODO: use common file to share these values between scripts
virtualEnvironName="emailEnv"
THIS_FILE_DIR="$(readlink -fm $0/..)"
rootDir="$(readlink -fm ${THIS_FILE_DIR}/..)"
virtualEnvironDir="${rootDir}/${virtualEnvironName}"
pythonLocation="" # global (changed based on OS)
backendPath=${rootDir}/backend
srcPath=${backendPath}/src
executePath=${srcPath}/emailAgent.py

# check OS... (decide how to call python)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # windows
    pythonLocation=${virtualEnvironDir}/Scripts/python.exe
else
    # linux
    pythonLocation=${virtualEnvironDir}/bin/python # NOTE: don't use ".exe"
fi

${pythonLocation} ${executePath} $1 $2 $3
