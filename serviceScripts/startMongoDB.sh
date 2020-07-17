#!/bin/bash
# Note: needs to be admin cmd or sudo

[[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]] && isWindows=true || isWindows=false

# $1 = service to test
service_exists() {
    local n=$1
    if [[ $(systemctl list-units --all -t service --full --no-legend "$n.service" | cut -f1 -d' ') == $n.service ]]; then
        return 0
    else
        return 1
    fi
}

if [[ ${isWindows} == false ]]; then
    if [ "$EUID" -ne 0 ]; then
        echo "Please run as root ('sudo')"
        exit
    else # have sudo permissions
        if service_exists mongodb; then
            echo "Starting MongoDB"
            systemctl start mongodb
        else
            echo "MongoDB service not yet created...(probably have to run './install/setup.sh')"
        fi
    fi
else # is windows
    # || denotes "on fail"
    echo "Starting MongoDB (if it is not doing anything, control+c once)"
    net start MongoDB && echo "Successfully Started MongoDB" || echo "Run in Admin Command Prompt"
fi
