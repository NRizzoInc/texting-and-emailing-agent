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

# CLI Flags
print_flags () {
    echo "Usage: startWebApp.sh"
    echo "=========================================================================================================="
    echo "Helper utility to start up the email web application"
    echo "Starts up the virtual environment via bash, meaning user does not need to have python locally installed"
    echo "How to use:" 
    echo "To Start: ./startWebApp.sh [options]"
    echo "To Stop: control+c script to stop the web app"
    echo "=========================================================================================================="
    echo "Available flags:"
    echo "  -p,--port <desired port>: Choose the port to run on"
    echo "  -h,--help : This messsage"
    echo "=========================================================================================================="
}

# parse command line args
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -p | --port )
            port="$2"
            shift
            ;;
        -h | --help )
            print_flags
            exit 0
            ;;
        * )
            echo "... Unrecognized command"
            print_flags
            exit 1
    esac
    shift
done

# check OS... (decide how to call python)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # windows
    pythonLocation=${virtualEnvironDir}/Scripts/python.exe
else
    # linux
    pythonLocation=${virtualEnvironDir}/bin/python # NOTE: don't use ".exe"
fi

${pythonLocation} ${executePath} --port ${port}
