#!/bin/bash
# this script starts up the website in a background process that will live on even after ssh logout
thisDir="$(readlink -fm $0/..)"
function startWebsite() {
    cd $thisDir 
    nohup python3 webApp.py > webOutput.log &
    echo "Website is up!"
}
export -f startWebsite
startWebsite
echo "IMPORTANT!! To kill the website, run stopWebsite.sh"

