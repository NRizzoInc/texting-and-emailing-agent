
import os, sys
import json

def loadJson(pathToJson):
    """Wrapper function that makes it easy to load a json"""
    with open(pathToJson, 'r+') as readFile:
        data = json.load(readFile)
    return data
