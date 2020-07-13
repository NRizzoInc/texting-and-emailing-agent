#!/bin/bash
# create virtual environment to install desired packages (i.e. flask)
[[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]] && isWindows=true || isWindows=false

# if linux, need to check if using correct permissions
if [[ "${isWindows}" = false ]]; then
    if [ "$EUID" -ne 0 ]; then
        echo "Please run as root ('sudo')"
        exit
    fi
fi

THIS_FILE_DIR="$(readlink -fm $0/..)"
virtualEnvironName="emailEnv"
rootDir="$(readlink -fm ${THIS_FILE_DIR}/..)"
virtualEnvironDir=${rootDir}/${virtualEnvironName}
pythonLocation=${virtualEnvironDir}/Scripts/python.exe
pythonVersion=3.7
pipLocation="" # make global

# check OS... (decide how to activate virtual environment)
echo "#1 Setting up virtual environment"
if [[ ${isWindows} = true ]]; then
    # windows
    echo "#1.1 Checking Python Version"
    currVersionText=$(python3 --version)
    currVersionMinor=$(echo "$currVersionText" | awk '{print $2}')
    currVersion=$(echo "${currVersionMinor}" | sed -r 's/\.[0-9]$//') # strips away minor version (3.7.2 -> 3.7)

    echo "Using python${currVersion} to build virtual environment"
    if [[ ${pythonVersion} != ${currVersion} ]]; then
        echo "WARNING: Wrong version of python being used. Expects python${pythonVersion}. This might affect results"
    fi

    echo "#1.2 Creating Virtual Environment"
    py -m venv $virtualEnvironDir # actually create the virtual environment
    $virtualEnvironDir/Scripts/activate
    pipLocation=$virtualEnvironDir/Scripts/pip3.exe

else
    # linx
    # needed to get specific versions of python
    pythonName=python${pythonVersion}
    echo "#1.1 Adding python ppa"
    add-apt-repository -y ppa:deadsnakes/ppa

    echo "#1.2 Updating..."
    apt update -y

    echo "#1.3 Upgrading..."
    apt upgrade -y
    apt install -y \
        ${pythonName} \
        ${pythonName}-venv

    echo "#1.4 Creating Virtual Environment"
    ${pythonName} -m venv ${virtualEnvironDir} # actually create the virtual environment
    source ${virtualEnvironDir}/bin/activate
    pipLocation=${virtualEnvironDir}/bin/pip${pythonVersion}

    echo "#1.5 Exporting Path to Source Code"
    # set it locally
    emailWebAppRootDir=${rootDir}

    # make environment variable for path global (if already exists -> replace it, but keep backup)
    sed -i.bak '/emailWebAppRootDir=/d' ~/.bashrc
    echo "export emailWebAppRootDir=${rootDir}" >> ~/.bashrc
    source ~/.bashrc
    echo "emailWebAppRootDir: ${emailWebAppRootDir}"
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
