import os, sys
import json
# needed to determine which OS is being used
import re
import platform
import subprocess
# used to get local network exposible IP
import socket

def loadJson(pathToJson):
    """Wrapper function that makes it easy to load a json"""
    with open(pathToJson, 'r+') as readFile:
        data = json.load(readFile)
    return data

def writeJson(pathToJson, jsonData, indent=4):
    """Wrapper function that makes it easy to write to a json"""
    with open(pathToJson, 'w+') as writeFile:
        json.dump(jsonData, writeFile, indent=indent) #write empty dictionary to file (creates the file)

def keyExists(thisDict, key):
    """Returns true if dictionary contains the key"""
    return key in thisDict

def mergeDicts(dict1, dict2):
    return {**dict1, **dict2}

def isWindows():
    myPlatform = platform.system()
    return myPlatform == "Windows"

def isLinux():
    myPlatform = platform.system()
    return myPlatform == "Linux"

def getIP():
    """Returns your computer's ip address that is accessible by your router"""
    if isWindows():
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        return IPAddr
    elif isLinux():
        ipExpr = r'inet ([^.]+.[^.]+.[^.]+.[^\s]+)'
        output = subprocess.check_output("ifconfig").decode()
        matches = re.findall(ipExpr, output)

        # based on system's setup, might have multiple ip loops running
        # the only one the router actually sees is the one starting with 192.168
        # https://qr.ae/pNs807
        narrowMatches = lambda match: match.startswith("192.168.")
        IPAddr = list(filter(narrowMatches, matches))[0]
        print("Found ip: {0}".format(IPAddr))
        return IPAddr

def keyExists(myDict, key):
    """Returns True or False if 'key' is in 'myDict'"""
    return key in list(myDict.keys())

def containsConfirmation(response):
    """Helper function that returns if 'y' or 'n' is contained within the argument"""
    return 'y' in response or 'n' in response

def promptUntilSuccess(message, successCondition=None):
    """
        \n@Brief: Keeps prompting user with 'message' until they respond correctly
        \n@Param: message - The message to prompt users with repetitively
        \n@Param: successCondition - (optional) Comparison function that returns a bool -> true means return
        \n@Returns: The validated response
    """
    isValidResponse = False
    while isValidResponse == False:
        response = input(message)
        if response != None and len(response) > 0: 
            if successCondition == None:        return response # if no comparison fn, return checked response
            elif successCondition(response):    return response # if returns true, can return valid response
        else: print("Not a valid response")
