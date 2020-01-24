#/bin/bash
# this script enables user to run the code in this repo 
# using the virtual environment
THIS_FILE_DIR="$(readlink -fm $0/..)"
virtualEnvironName="emailEnv"
virtualEnvironDir=$THIS_FILE_DIR/$virtualEnvironName
pythonLocation=$virtualEnvironDir/Scripts/python.exe

$pythonLocation -c """
import os, sys
import emailAgent
while (len(sys.argv) < 4):
    sys.argv.append('')
sys.argv[1] = '$1'
sys.argv[2] = '$2'
sys.argv[3] = '$3'
emailer = emailAgent.emailAgent()
emailer.start()
"""
