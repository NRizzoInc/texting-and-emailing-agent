
import os, sys
import json

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