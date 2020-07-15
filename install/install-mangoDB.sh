#!/bin/bash
# @File: Downloads MongoDB
# Note: Important Files are mongod.exe (daemon = server) & mongo.exe (client)
# Windows: default download = C:\Program Files\MongoDB\Server\4.2\bin
# Linux: ??

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
    echo "Needed Flags:"
    echo "  --root-dir <dir> : Absolute path to the root of the repo"
    echo "  --install-dir <dir> Absolute path to the install directory of the repo (this folder)"
    echo "=========================================================================================================="
}

# parse command line args
rootDir=""
installDir=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --root-dir )
            rootDir="$2"
            shift
            ;;
        --install-dir )
            installDir="$2"
            shift
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

# vars needed for both linux & windows
externDir=${rootDir}/extern
mangoDir=${externDir}/MangoDB
mangoInstallDirname="Server" # root/extern/mangoDB/Server

if [[ ${isWindows} == true ]]; then
    # might need Admin Privelages for windows

    # basic paths for download
    downloadName="mongodb-win32-x86_64-enterprise-windows-64-4.2.8-signed.msi"
    winDownloadURL=https://downloads.mongodb.com/win32/${downloadName}
    downloadPath=${mangoDir}/${downloadName} # needed for curl command
    installBatchScript=${installDir}/install-mangoDB.bat

    # download the .msi install file
    curl --url ${winDownloadURL} --output ${downloadPath}

    ##### get windows download path for .msi install command (convert from linux -> windows)
    # remove first '/' (/d/...)
    downloadPathDrive=${downloadPath:1}
    # capitalize drive letter -- https://stackoverflow.com/a/12487455
    downloadPathDrive="${downloadPathDrive^}"
    # insert ':' between first & second char
    downloadPathDriveColon=${downloadPathDrive:0:1}:${downloadPathDrive:1}
    # replace all '/' with '\' -- https://stackoverflow.com/a/13210909 - ${parameter//pattern/string}
    downloadPathWin=${downloadPathDriveColon////\\}

    # call batch script (cannot call it directly due to differences between bash and batch)
    # need to encapsualte command in quotes, but rightmost quote cannot be escaped and is added to the path
    # accepts arguments: 1st = path to download
    ${installBatchScript} ${downloadPathWin} ${mangoInstallDirname}
else
    # linux - TODO
    echo "IMPLEMENT LINUX"
fi
