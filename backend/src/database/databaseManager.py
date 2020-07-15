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
        dbExists = self._doesDBExist()
        self.db = self.dbClient[self._dbName]
        self.dbColl = self.db[self._dbCollectionName]

        # if db & collection don't exist, add dummy data to them to create it
        if not dbExists:
            print(f"Database '{self._dbName}' does not exist... creating")
            self.createDB()
        else:
            print(f"Database '{self._dbName}' already exists")

    def _doesDBExist(self):
        dbNames = self.dbClient.list_database_names()
        print(f"Current Databases: {dbNames}")
        return self._dbName in dbNames

    def createDB(self):
        """Meant to help create the database & collection if they dont exist by adding dummy data"""
        dummyData = {"username": "dev", "password": "1@Mdummy5@t@P@ssw0rD"}
        self.insertData(dummyData)
    
    def insertData(self, data):
        """Accepts a list of dictionaries (or just one) to submit"""
        insertingMultiple = utils.isList(data)
        numEntries = len(data)
        if not insertingMultiple:
            self.dbColl.insert_one(data)
        # else:               self.dbColl.insert_many(data)
