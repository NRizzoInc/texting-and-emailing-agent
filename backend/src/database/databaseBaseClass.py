"""
    \n@File: Contains common database functions that can be shared between classes
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import json
import pickle, copyreg, ssl # for serializing User objects (SSL obj requires more work)

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from pymongo import MongoClient
from bson.binary import Binary # for serializing/derializing User objects

#--------------------------------OUR DEPENDENCIES--------------------------------#
import constants

class DatabaseBaseClass():
    def __init__(self):
        """
            \n@Brief: Helper class that is meant to be inhereted by other database manager classes
        """
        self._dbName = constants.dbName
        self._userCollectionName = constants.userCollectionName
        self._contactsCollectionName = constants.contactsCollectionName
        self.dbRef = MongoClient("mongodb://localhost:27017/")
        self.dbClient = self.dbRef[self._dbName]
        self.userColl = self.dbClient[self._userCollectionName] # this is for web app
        self.contactsColl = self.dbClient[self._contactsCollectionName] # this is for email agent to manage contact lists

    def createCollDNE(self, collObj:MongoClient):
        """Wrapper of lowest level api functions that creates a collection if it does not exist (DNE)"""
        exists = self._doesCollExist(collObj)
        collName = collObj.name
        if not exists:
            print(f"Database collection '{collName}' does not exist... creating")
            self.createCollection(collObj)
        else:
            print(f"Database collection '{collName}' already exists")

    def _doesCollExist(self, collObj:MongoClient)->bool():
        collectionNames = self.dbClient.list_collection_names()
        return collObj.name in collectionNames

    def createCollection(self, collObj:MongoClient):
        """Meant to help create the database & collection if they dont exist by adding dummy data"""
        dummyData = {"id": "admin-account", "username": "dev", "password": "1@Mdummy5@t@P@ssw0rD"}
        databaseUtils.insertData(collObj, dummyData)

    def insertData(self, collObj:MongoClient, data):
        """Accepts a list of dictionaries (or just one) to submit"""
        insertingMultiple = utils.isList(data)
        numEntries = len(data)
        if not insertingMultiple:
            collObj.insert_one(data)
        # else:               self.userColl.insert_many(data)

    def exists(self, collObj:MongoClient, query:dict):
        """Returns true if an item exists with your desired traits (both key and value)"""
        match = list(collObj.find(query))
        numMatches = len(match)
        return numMatches > 0

    def deserializeData(self, data:Binary):
        decodedObj = Binary(data).decode()
        deserializedObj = pickle.loads(data)
        return deserializedObj

    def serializeObj(self, obj):
        """
            \n@Param: obj - The object to serial
            \n@Return: The serialized object
            \n@Note: Meant to serialize objects (pairs with 'deserializeData()')
        """
        serializedObj = pickle.dumps(obj)
        binarySerialObj = Binary(serializedObj)
        return binarySerialObj
