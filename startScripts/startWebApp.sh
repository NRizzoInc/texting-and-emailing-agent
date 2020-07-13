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
import os, sys, pathlib, platform

# if windows, need to modify path
myPlatform = platform.system()
isWindows = myPlatform == 'Windows'

# get root dir path based on string collected in bash script
rootDir = str(pathlib.Path('${rootDir}'))

# for windows, current path looks like: D:\test\readme.md 
# current path from bash script: \d\test\readme.md
# need to convert \d\test\readme.md -> D:\test\readme.md
if (isWindows):
    rootDirNoFrontSlash = rootDir[1:] # d\..
    rootDirCapital = rootDirNoFrontSlash.capitalize() # D\..
    rootDir = rootDirCapital[:1] + ':' + rootDirCapital[1:] # insert ':' after drive letter

# Navigate to correct directory to import
print('Running from {0}'.format(rootDir))
os.chdir(rootDir)

# Finally actually import the src code
from backend.src.webApp.webApp import sys, WebApp
client = WebApp()
"""
