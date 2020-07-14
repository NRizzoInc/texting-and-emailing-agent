#!/bin/bash
# this script enables user to run the code in this repo 
# using the virtual environment
virtualEnvironName="emailEnv"
THIS_FILE_DIR="$(readlink -fm $0/..)"
rootDir="$(readlink -fm ${THIS_FILE_DIR}/..)"
virtualEnvironDir="${rootDir}/${virtualEnvironName}"
pythonLocation="" # global (changed based on OS)
backendPath=${rootDir}/backend
srcPath=${backendPath}/src/webApp
executePath=${srcPath}/webApp.py

# check OS... (decide how to call python)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # windows
    pythonLocation=${virtualEnvironDir}/Scripts/python.exe
else
    # linux
    pythonLocation=${virtualEnvironDir}/bin/python # NOTE: don't use ".exe"
fi

# use "$@" to pass on all parameter the same way to python script
${pythonLocation} ${executePath} "$@"
