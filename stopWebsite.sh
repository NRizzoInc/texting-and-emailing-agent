#!/bin/bash
function killWebsite() {
	grepWebPid=$(ps -ef | grep 'webApp.py')
	getWebPid=$(echo $grepWebPid | tr -s ' ' | cut -d' ' -f2) # truncastes spaces to cut them-standardized
	echo "Website PID: $getWebPid"
	kill -9 $getWebPid
	echo "Killed the process"
}
killWebsite # call function
export -f killWebsite
