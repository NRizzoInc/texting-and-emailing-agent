
import os, sys
import json

def loadJson(pathToJson):
    with open(pathToJson, 'r+') as readFile:
        data = json.load(readFile)
    return data