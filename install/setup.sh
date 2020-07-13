#!/bin/bash
# create virtual environment to install desired packages (i.e. flask)
THIS_FILE_DIR="$(readlink -fm $0/..)"
virtualEnvironName="emailEnv"
rootDir="$(readlink -fm ${THIS_FILE_DIR}/..)"
virtualEnvironDir=${rootDir}/${virtualEnvironName}
pythonLocation=${virtualEnvironDir}/Scripts/python.exe
pipLocation="" # make global

# check OS... (decide how to activate virtual environment)
echo "#1 Setting up virtual environment"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # windows
    echo "#1.1 Creating Virtual Environment"
    py -m venv $virtualEnvironDir # actually create the virtual environment
    $virtualEnvironDir/Scripts/activate
    pipLocation=$virtualEnvironDir/Scripts/pip3.exe

else
    # linx
    # needed to get specific versions of python
    pythonVersion=3.7
    pythonName=python${pythonVersion}
    echo "#1.1 Adding python ppa"
    sudo add-apt-repository -y ppa:deadsnakes/ppa

    echo "#1.2 Updating..."
    sudo apt update -y

    echo "#1.3 Upgrading..."
    sudo apt upgrade -y
    sudo apt install -y \
        ${pythonName} \
        ${pythonName}-venv

    echo "#1.4 Creating Virtual Environment"
    ${pythonName} -m venv ${virtualEnvironDir} # actually create the virtual environment
    source ${virtualEnvironDir}/bin/activate
    pipLocation=${virtualEnvironDir}/bin/pip${pythonVersion}
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
