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
from constants import Constants

class DatabaseBaseClass(Constants):
    def __init__(self):
        """
            \n@Brief: Helper class that is meant to be inhereted by other database manager classes
        """
        # Inheret all functions and 'self' variables
        super().__init__()

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

    def replaceData(self, collObj:MongoClient, myFilter:dict, newData:dict):
        """
            \n@Brief: Updates the FIRST card within the collection fitting the filter with 'newData'
            \n@Param: collObj - The collection object
            \n@Param: myFilter - The query parameter to find the card to update
            \n@Param: newData - The data to update the card with
        """
        collObj.find_one_and_replace(myFilter, newData, upsert=True)

    def getCardById(self, collObj:MongoClient, userId):
        """Returns collection object based on the UUID -- returns empty dict for non-existant user"""
        match = list(collObj.find({"id": userId})) # "match" because there should only ever be one
        numMatches = len(match)
        if numMatches > 0:  return match[0]
        else:               return {} 

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
