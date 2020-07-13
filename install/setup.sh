#!/bin/bash
# create virtual environment to install desired packages (i.e. flask)
THIS_FILE_DIR="$(readlink -fm $0/..)"
virtualEnvironName="emailEnv"
rootDir="$(readlink -fm ${THIS_FILE_DIR}/..)"
virtualEnvironDir=${rootDir}/${virtualEnvironName}
pythonLocation=${virtualEnvironDir}/Scripts/python.exe
pipLocation="" # make global

# check OS... (decide how to activate virtual environment)
echo "#1 Creating Virtual Environment"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # windows
    py -m venv $virtualEnvironDir # actually create the virtual environment
    $virtualEnvironDir/Scripts/activate
    pipLocation=$virtualEnvironDir/Scripts/pip3.exe

else
    # linx
    # sudo apt update
    # sudo apt install python3-pip
    # sudo apt-get install python3-venv
    python3 -m venv $virtualEnvironDir # actually create the virtual environment
    source $virtualEnvironDir/bin/activate
    pipLocation=$virtualEnvironDir/bin/pip3
fi

# update pip to latest
echo "#2 Upgrading pip to latest"
$pythonLocation -m pip install --upgrade pip

# now pip necessary packages
echo "#3 Installing all packages"
$pipLocation install flask
$pipLocation install pyinstaller # to turn python to .exe
$pipLocation install fleep # to identify file types based on content -  https://github.com/floyernick/fleep-py
$pipLocation install flask-login
$pipLocation install flask-wtf
$pipLocation install flask-socketio
