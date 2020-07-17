#!/bin/bash
# this script enables user to run the code in this repo using the virtual environment
# It abstracts concepts to pass data to lower scripts such that only one script ever needs to be called

# Get paths to everything
virtualEnvironName="emailEnv"
THIS_FILE_DIR="$(readlink -fm $0/..)"
# rootDir="$(readlink -fm ${THIS_FILE_DIR}/..)" # if script moved down a dir
rootDir=${THIS_FILE_DIR}
virtualEnvironDir="${rootDir}/${virtualEnvironName}"
backendPath=${rootDir}/backend
srcPath=${backendPath}/src
emailDirPath=${srcPath}/emailing
webDirPath=${srcPath}/webApp
emailExecPath=${emailDirPath}/emailCLIManager.py
webExecPath=${webDirPath}/webApp.py
executePath="" # global (defined later based on CLI flag)

# check OS... (decide how to call python)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # windows
    pythonLocation=${virtualEnvironDir}/Scripts/python.exe
else
    # linux
    pythonLocation=${virtualEnvironDir}/bin/python # NOTE: don't use ".exe"
fi

# CLI Flags
print_flags () {
    echo "=========================================================================================================="
    echo "Usage: start.sh"
    echo "=========================================================================================================="
    echo "Helper utility to start up the email application (via either web app form or command line)"
    echo "Starts up the virtual environment via bash."
    echo "User does not need to have python locally installed or worry about activating the virtual environment"
    echo "=========================================================================================================="
    echo "How to use:" 
    echo "  To Start: ./start.sh --mode <mode> [options]"
    echo "  To Stop: control+c"
    echo "=========================================================================================================="
    echo "Available Flags:"
    echo "  -m,--mode <mode>: Either 'web' or 'cli'"
    echo "                    ('web': start the web application)"
    echo "                    ('cli': start the command line email application)"
    echo "  -h,--help : Prints the command line help message of the native mode that is run"
    echo "              (or this message if no mode specified)"
    echo "=========================================================================================================="
}

# parse command line args
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -m | --mode )
            mode="$2"
            if [[ ${mode} == "web" ]]; then
                executePath=${webExecPath}
            elif [[ ${mode} == "cli" ]]; then
                executePath=${emailExecPath}
            else
                echo "Error: Invalid mode -- see flags section in usage"
                print_flags
                exit 1
            fi
            shift # remove --mode from CLI
            shift # remove <mode> from CLI
            break # stop searching command line if mode provided
            ;;

        # none of these are reachable if mode is provided due to the break within the "mode" flag
        -h | --help )
            print_flags
            exit 0
            ;;
        # * )
        #     echo "... Unrecognized command"
        #     print_flags
        #     exit 1
    esac
    shift
done

# check if executePath is ever set (was mode set)
if [[ ${executePath} == "" ]]; then
    echo "Error: No mode selected -- see flags section in usage"
    print_flags
    exit 1
fi


# use "$@" to pass on all parameter the same way to python script
${pythonLocation} ${executePath} "$@"
