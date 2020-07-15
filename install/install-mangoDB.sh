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
    echo "  --user-data-dir <dir> Absolute path to the user data directory of the repo"
    echo "=========================================================================================================="
}

# parse command line args
rootDir=""
installDir=""
userDataDir=""
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
        --user-data-dir )
            userDataDir="$2"
            shift
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

# $1 is path to convert
# returns windows path -- capture with res=$(linuxToWinPath <path>)
function linuxToWinPath() {
    # get arg
    local pathLinux=$1

    # remove first '/' (/d/...)
    local pathDrive=${pathLinux:1}
    # capitalize drive letter -- https://stackoverflow.com/a/12487455
    local pathDrive="${pathDrive^}"
    # insert ':' between first & second char
    local pathDriveColon=${pathDrive:0:1}:${pathDrive:1}
    # replace all '/' with '\' -- https://stackoverflow.com/a/13210909 - ${parameter//pattern/string}
    local pathWin=${pathDriveColon////\\}

    # return
    echo "${pathWin}"
}
# $1 is path to convert
# returns windows path with double backslash ('\\') -- capture with res=$(escapeBackslash <path>)
function escapeBackslash() {
    local originalPath=$1
    # find and replace each '\' with '\\'
    doubleBackslash=${originalPath//\\/\\\\}

    # return
    echo "${doubleBackslash}"
}

# vars needed for both linux & windows
startScriptsDir=${rootDir}/serviceScripts
externDir=${rootDir}/extern
mangoDir=${externDir}/MangoDB
mangoInstallDir=${mangoDir}/"Server"
startMongoScript=${startScriptsDir}/startMangoDB.sh
stopMongoScript=${startScriptsDir}/stopMangoDB.sh
mongoConfigPath=${mangoDir}/mongod.cfg
mongoConfigTemplatePath=${mongoConfigPath}.bak

if [[ ${isWindows} == true ]]; then
    # might need Admin Privelages for windows

    # basic paths for download
    downloadName="mongodb-win32-x86_64-enterprise-windows-64-4.2.8-signed.msi"
    winDownloadURL=https://downloads.mongodb.com/win32/${downloadName}
    downloadPath=${mangoDir}/${downloadName} # needed for curl command
    installBatchScript=${installDir}/install-mangoDB.bat

    # download the .msi install file
    curl --url ${winDownloadURL} --output ${downloadPath}

    # call batch script (cannot call it directly due to differences between bash and batch)
    # need to encapsualte command in quotes, but rightmost quote cannot be escaped and is added to the path
    # see the script for all its arguments
    ${installBatchScript} \
        $(linuxToWinPath ${downloadPath}) \
        $(linuxToWinPath ${mangoDir}) \
        $(linuxToWinPath ${mangoInstallDir}) \
        ${startMongoScript} \
        ${stopMongoScript}
else
    # linux - TODO
    echo "IMPLEMENT LINUX"
fi

# Create & Register the Database Dir (default path)
dbDataDir=$(linuxToWinPath ${userDataDir})
echo "dbDataDir: ${dbDataDir}"
# fill in path variables in config file
# <<dbDataDir>> = value of ${dbDataDir}
# have to escape '\' characters
filledInTemplate=$(sed "s/<<dbDataDir>>/$(escapeBackslash ${dbDataDir})/g" ${mongoConfigTemplatePath})
echo "${filledInTemplate}" > ${mongoConfigPath}
"C:\Program Files\MongoDB\Server\4.2\bin\mongod.exe" --config ${mongoConfigPath}

# Start MangoDB to Create the Database
bash ${startMongoScript}

# Inform user how to stop it
echo "Stop MangoDB Server/Daemon with '${stopMongoScript}'"
