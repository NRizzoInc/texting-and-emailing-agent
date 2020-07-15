#!/bin/bash
# Note: needs to be admin cmd or sudo

[[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]] && isWindows=true || isWindows=false

if [[ ${isWindows} == false ]]; then
    if [ "$EUID" -ne 0 ]; then
        echo "Please run as root ('sudo')"
        exit
    else # have sudo permissions
        echo "IMPLEMENT LINUX STOP"
        # linux start cmd
    fi
else # is windows
    # || denotes "on fail"
    echo "Stopping MongoDB"
    net stop MongoDB && echo "Successfully Stopped MongoDB" || echo "Run in Admin Command Prompt"
fi
