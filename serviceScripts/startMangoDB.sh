#!/bin/bash
# Note: needs to be admin cmd or sudo

[[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]] && isWindows=true || isWindows=false

if [[ ${isWindows} == false ]]; then
    if [ "$EUID" -ne 0 ]; then
        echo "Please run as root ('sudo')"
        exit
    else # have sudo permissions
        echo "IMPLEMENT LINUX START"
        # linux start cmd
    fi
else # is windows
    # || denotes "on fail"
    echo "Starting MongoDB"
    net start MongoDB && echo "Successfully Started MongoDB" || echo "Run in Admin Command Prompt"
fi