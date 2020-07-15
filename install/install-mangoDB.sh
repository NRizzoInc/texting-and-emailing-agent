#!/bin/bash

[[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]] && isWindows=true || isWindows=false
# CLI Flags
print_flags () {
    echo "=========================================================================================================="
    echo "Usage: install-mangoDB.sh"
    echo "=========================================================================================================="
    echo "Helper utility to download the correct version of mangoDB"
    echo "=========================================================================================================="
    echo "How to use:" 
    echo "  To Start: ./install-mangoDB.sh [flags]"
    echo "=========================================================================================================="
    echo "Available Flags:"
    echo "  --root-dir <dir> : Absolute path to the root of the repo"
    echo "=========================================================================================================="
}

# parse command line args
rootDir=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --root-dir )
            rootDir="$2"
            shift
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

# might need Admin Privelages for windows

downloadName="mongodb-win32-x86_64-enterprise-windows-64-4.2.8-signed.msi"
externDir=${rootDir}/extern
downloadPath=${externDir}/${downloadName}
winDownloadURL=https://downloads.mongodb.com/win32/${downloadName}
curl --url ${winDownloadURL} --output ${downloadPath}
