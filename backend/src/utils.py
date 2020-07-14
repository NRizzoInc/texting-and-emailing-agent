
import os, sys
import json
import re
import socket # used to get local network exposible IP

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

def getIP():
    """Returns your computer's ip address that is accessible by your router"""
    myPlatform = platform.system()
    if myPlatform == "Windows":
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        return IPAddr
    elif myPlatform == "Linux":
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