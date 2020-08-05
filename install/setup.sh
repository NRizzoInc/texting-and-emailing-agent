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

# CLI Flags
print_flags () {
    echo "========================================================================================================================="
    echo "Usage: setup.sh"
    echo "========================================================================================================================="
    echo "Helper utility to setup everything to use this repo"
    echo "========================================================================================================================="
    echo "How to use:" 
    echo "  To Start: ./setup.sh [flags]"
    echo "========================================================================================================================="
    echo "Available Flags (mutually exclusive):"
    echo "    -a | --install-all: If used, install everything (recommended for fresh installs)"
    echo "    -p | --python-packages: Update virtual environment with current python packages (this should be done on pulls)"
    echo "    -s | --deploy-services: Deploy the source code to enable the system service to run (only works on Ubuntu)"
    echo "    -m | --install-mongo: Install & setup MongoDB (needed for managing users & only needed once)"
    echo "    -h | --help: This message"
    echo "========================================================================================================================="
}

# parse command line args
upgradePkgs=false
installMongo=false
deployServices=false
noneSet=true
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -a | --install-all )
            upgradePkgs=true
            installMongo=true
            noneSet=false
            break
            ;;
        -m | --install-mongo )
            installMongo=true
            noneSet=false
            break
            ;;
        -p | --python-packages )
            upgradePkgs=true
            noneSet=false
            break
            ;;
        -s | --deploy-services )
            deployServices=true
            noneSet=false
            break
            ;;
        -h | --help )
            print_flags
            exit 0
            ;;
        * )
            echo "... Unrecognized Command: $1"
            print_flags
            exit 1
    esac
    shift
done

if [[ ${noneSet} == true ]]; then
    print_flags
    echo "Please use one of the flags (just use -a if you are unsure)"
    exit
fi


THIS_FILE_DIR="$(readlink -fm $0/..)"
virtualEnvironName="emailEnv"
rootDir="$(readlink -fm ${THIS_FILE_DIR}/..)"
backendDir=${rootDir}/backend
userDataDir=${backendDir}/userData
installDir=${rootDir}/install
helpScriptDir=${installDir}/helper-scripts
mongoInstallScript=${helpScriptDir}/install-mongoDB.sh
virtualEnvironDir=${rootDir}/${virtualEnvironName}
pythonVersion=3.7
pipLocation="" # make global
pythonLocation="" # global (changed based on OS)


if [[ ${installMongo} == true ]]; then
    echo "#0 Downloading/Installing Prerequisite Software"
    echo "#0.1 Downloading/Installing MongoDB -- Database"
    bash ${mongoInstallScript} \
        --root-dir ${rootDir} \
        --install-dir ${installDir} \
        --helper-script-dir ${helpScriptDir}
fi

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

    echo "#1.3 Getting Path to Virtual Environment's Python"
    pythonLocation=${virtualEnvironDir}/Scripts/python.exe
    echo "-- pythonLocation: ${pythonLocation}"

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
        ${pythonName}-venv \
        mongodb

    echo "#1.4 Creating Virtual Environment"
    ${pythonName} -m venv ${virtualEnvironDir} # actually create the virtual environment
    source ${virtualEnvironDir}/bin/activate
    pipLocation=${virtualEnvironDir}/bin/pip${pythonVersion}

    if [[ ${deployServices} == true ]]; then
        echo "#1.5 Exporting Path to Source Code"
        # set it locally

        # make environment variable for path global (if already exists -> replace it, but keep backup)
        # https://serverfault.com/a/413408 -- safest way to create & use environment vars with services
        environDir=/etc/sysconfig
        environFile=${environDir}/webAppEnviron
        echo "Environment File: ${environFile}"

        # if dir & file do not exist, add them before trying to scan & create backup
        test -d ${environDir} && echo "${environDir} Already Exists" || mkdir ${environDir}
        test -f ${environFile} && echo "${environFile} Already Exists" || touch ${environFile}

        # create backup & save new version with updated path
        sed -i.bak '/emailWebAppRootDir=/d' ${environFile}
        echo "emailWebAppRootDir=${rootDir}" >> ${environFile}
        source ${environFile}
        echo "emailWebAppRootDir: ${rootDir}"

        echo "#1.6 Deploying Service File"
        sysServiceDir=/etc/systemd/system
        serviceFileDir=${rootDir}/install${sysServiceDir}
        serviceFile=$(find ${serviceFileDir} -maxdepth 1 -name "*web-app*" -print)
        serviceFileName=$(basename "${serviceFile}")
        cp ${serviceFile} ${sysServiceDir}/
        echo "-- Deployed ${serviceFile} -> ${sysServiceDir}/${serviceFileName}"

        echo "#1.8 Getting Path to Virtual Environment's Python"
        pythonLocation=${virtualEnvironDir}/bin/python # NOTE: don't use ".exe"
        echo "-- pythonLocation: ${pythonLocation}"
    fi
fi

if [[ ${upgradePkgs} == true ]]; then
    # update pip to latest
    echo "#2 Upgrading pip to latest"
    $pythonLocation -m pip install --upgrade pip

    # now pip necessary packages
    echo "#3 Installing all packages"
    $pipLocation install -r ${installDir}/requirements.txt
fi


if [[ ${deployServices} == true ]]; then

    # Start service after everything installed if linux
    if [[ "${isWindows}" = false ]]; then
        echo "#4 Starting Services"
        # stop daemon to allow reload
        echo "-- Stopping ${serviceFileName} Daemon"
        systemctl stop ${serviceFileName}
        echo "-- Stopping MongoDB Daemon"
        systemctl stop mongodb
        echo "-- Stopped ${serviceFileName} Daemon"

        # refresh service daemons
        systemctl daemon-reload

        # Restart Daemons
        echo "-- Reloaded ${serviceFileName} Daemon"
        systemctl start ${serviceFileName}
        echo "-- Reloaded MongoDB Daemon"
        systemctl start mongodb

        # Done
        echo "-- Started ${serviceFileName} Daemon"

        # Make Daemons Persistent for Boot
        systemctl enable ${serviceFileName}
        echo "-- Making Daemons Persistent for Boot"
    fi
fi
