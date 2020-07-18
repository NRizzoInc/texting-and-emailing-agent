"""
    \n@File: Contains common database functions that can be shared between classes
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import json
import pickle, copyreg, ssl # for serializing User objects (SSL obj requires more work)

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from pymongo import MongoClient

#--------------------------------OUR DEPENDENCIES--------------------------------#
from backend.src.constants import Constants
from backend.src import utils

class DatabaseBaseClass(Constants):
    def __init__(self):
        """
            \n@Brief: Helper class that is meant to be inhereted by other database manager classes
        """
        # Inheret all functions and 'self' variables
        super().__init__()

        self.dbRef = MongoClient("mongodb://localhost:27017/")
        self.dbClient = self.dbRef[self._dbName]
        self.usersColl = self.dbClient[self._userCollectionName] # this is for web app
        self.contactsColl = self.dbClient[self._contactsCollectionName] # this is for email agent to manage contact lists

    def _createCollDNE(self, collObj:MongoClient):
        """Wrapper of lowest level api functions that creates a collection if it does not exist (DNE)"""
        exists = self.__doesCollExist(collObj)
        collName = collObj.name
        if not exists:
            print(f"Database collection '{collName}' does not exist... creating")
            self._createCollection(collObj)
        else:
            print(f"Database collection '{collName}' already exists")

    def __doesCollExist(self, collObj:MongoClient)->bool():
        collectionNames = self.dbClient.list_collection_names()
        return collObj.name in collectionNames

    def _createCollection(self, collObj:MongoClient):
        """Meant to help create the database & collection if they dont exist by adding dummy data"""
        dummyData = {"id": "admin-account", "username": "dev", "password": "1@Mdummy5@t@P@ssw0rD"}
        self._insertData(collObj, dummyData)

    def _insertData(self, collObj:MongoClient, data):
        """Accepts a list of dictionaries (or just one) to submit"""
        insertingMultiple = utils.isList(data)
        numEntries = len(data)
        if not insertingMultiple:
            collObj.insert_one(data)
        # else:               self.usersColl.insert_many(data)

    def _replaceDataById(self, collObj:MongoClient, userId:str, newData:dict):
        """
            \n@Brief: Updates the FIRST card within the collection fitting the filter with 'newData'
            \n@Param: collObj - The collection object
            \n@Param: userId - The UUID of the user's data to replace/update
            \n@Param: newData - The data to update the card with
        """
        query = {"id": userId}
        self._replaceData(collObj, query, newData)

    def _replaceData(self, collObj:MongoClient, myFilter:dict, newData:dict):
        """
            \n@Brief: Updates the FIRST card within the collection fitting the filter with 'newData'
            \n@Param: collObj - The collection object
            \n@Param: myFilter - The query parameter to find the card to update
            \n@Param: newData - The data to update the card with
        """
        collObj.find_one_and_replace(myFilter, newData, upsert=True)

    def _getDocById(self, collObj:MongoClient, userId):
        """Returns collection object based on the UUID -- returns empty dict for non-existant user"""
        match = list(collObj.find({"id": userId})) # "match" because there should only ever be one
        numMatches = len(match)
        if numMatches > 0:  return match[0]
        else:               return {}

    def _getDocByUsername(self, collObj:MongoClient, username):
        """Returns collection object based on the username -- returns empty dict for non-existant user"""
        match = list(collObj.find({"username": username})) # "match" because there should only ever be one
        numMatches = len(match)
        if numMatches > 0:  return match[0]
        else:               return {} 

    def _docExists(self, collObj:MongoClient, query:dict):
        """Returns true if an item exists with your desired traits (both key and value)"""
        match = list(collObj.find(query))
        numMatches = len(match)
        return numMatches > 0

    def _deserializeData(self, data:bytes):
        """
            \n@Param: data - The serialized object to deserialize
            \n@Return: The deserialized object
            \n@Note: Meant to deserialize objects that were serialized with '_serializeObj()'
        """
        deserializedObj = pickle.loads(data)
        return deserializedObj

    def _serializeObj(self, obj)->bytes():
        """
            \n@Param: obj - The object to serial
            \n@Return: The serialized object
            \n@Note: Meant to serialize objects (pairs with '_deserializeData()')
        """
        serializedObj = pickle.dumps(obj)
        return serializedObj
