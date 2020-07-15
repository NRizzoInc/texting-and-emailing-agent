"""
    @file: This file contains the database helper class
    @Note: Calling this with python will do nothing
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import json

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
import pymongo
import utils

class DatabaseManager():
    def __init__(self):
        """
            \n@Brief: This class is meant to help manage the database of users' information
            \n@Note: Will create the database if it does not already exist
        """
        self._dbName = "email-web-app"
        self._dbCollectionName = "users"
        self.dbClient = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.dbClient[self._dbName]
        self.dbColl = self.db[self._dbCollectionName]

        # if db & collection don't exist, add dummy data to them to create it
        if not self._doesDBExist():
            print(f"Database '{self._dbName}' does not exist... creating")
            self._createDB()
        else:
            print(f"Database '{self._dbName}' already exists")

############################################### HIGH LEVEL API FUNCTIONS ##############################################

    def addUser(self, userToken, username, password):
        """
            \n@Brief: High level api function call to add a user to the database
            \n@Param: userToken - The user's unique safe id (aka id)
            \n@Param: username - The user's chosen username
            \n@Param: password - The user's chosen password
        """
        newUser = {
            "id": userToken,
            "username": username,
            "password": password
        }
        self._insertData(newUser)

    def isUsernameInUse(self, usernameToTest:str):
        usernameExists = self._exists({"username": usernameToTest})
        # print(f"usernameExists: {usernameExists}")
        return usernameExists
    
    def isIdInUse(self, idToTest:str):
        idExists = self._exists({"id": idToTest})
        # print(f"idExists: {idExists}")
        return idExists


############################################### LOW LEVEL API FUNCTIONS ###############################################

    def _doesDBExist(self):
        dbNames = self.dbClient.list_database_names()
        print(f"Current Databases: {dbNames}")
        return self._dbName in dbNames

    def _createDB(self):
        """Meant to help create the database & collection if they dont exist by adding dummy data"""
        dummyData = {"id": "admin-account", "username": "dev", "password": "1@Mdummy5@t@P@ssw0rD"}
        self._insertData(dummyData)
    
    def _insertData(self, data):
        """Accepts a list of dictionaries (or just one) to submit"""
        insertingMultiple = utils.isList(data)
        numEntries = len(data)
        if not insertingMultiple:
            self.dbColl.insert_one(data)
        # else:               self.dbColl.insert_many(data)

    def _exists(self, query:dict):
        """Returns true if an item exists with your desired traits (both key and value)"""
        match = list(self.dbColl.find(query))
        numMatches = len(match)
        return numMatches > 0
