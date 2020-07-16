"""
    @file: This file contains the database helper class
    @Note: Calling this with python will do nothing
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import json

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from pymongo import MongoClient
from bson.binary import Binary # for serializing/derializing User objects

#--------------------------------OUR DEPENDENCIES--------------------------------#
import utils
import pickle, copyreg, ssl # for serializing User objects (SSL obj requires more work)

class DatabaseManager():
    def __init__(self):
        """
            \n@Brief: This class is meant to help manage the database of users' information
            \n@Note: Will create the database if it does not already exist
        """
        self._dbName = "email-web-app"
        self._userCollectionName = "users"
        self._contactsCollectionName = "contacts"
        self.dbClient = MongoClient("mongodb://localhost:27017/")
        self.db = self.dbClient[self._dbName]
        self.userColl = self.db[self._userCollectionName] # this is for web app
        self.contactsColl = self.db[self._contactsCollectionName] # this is for email agent to manage contact lists

        # if db or collection(s) don't exist, add dummy data to them to create it
        allCollections = [self.userColl, self.contactsColl]
        map(self._createCollDNE, allCollections)


############################################### HIGH LEVEL API FUNCTIONS ##############################################

    def addUser(self, userToken, username, password, userObj):
        """
            \n@Brief: High level api function call to add a user to the database
            \n@Param: userToken - The user's unique safe id (aka id)
            \n@Param: username - The user's chosen username
            \n@Param: password - The user's chosen password
            \n@Param: userObj - Reference to the instantiated userObj
        """
        newUser = {
            "id": userToken,
            "username": username,
            "password": password,
            "User": self._serializeObj(userObj) # need to serialize object for storage
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

    def getIdByUsername(self, username)->str():
        """
            \n@Param: username - The username matching the id you are looking for
            \n@Return: The corresponding id
            \n@Note: Useful if chained with other functions that require id (i.e. 'findUser()')
        """
        match = list(self.userColl.find({"username": username}))
        matchId = match[0]["id"]
        return matchId

    def findUser(self, userToken):
        """
            \n@Param: userToken - The user's unique token id
            \n@Return: The 'User' object
        """
        match = list(self.userColl.find({"id": userToken}))
        serializedUserObj = match[0]["User"]
        userObj = self._deserializeData(serializedUserObj)
        return userObj

    def getPasswordFromUsername(self, username:str)->str():
        """
            \n@Param: username - The password to find's username
            \n@Returns: The matching password 
        """
        match = list(self.userColl.find({"username": username}))
        actualPassword = match[0]["password"]
        return actualPassword

    def getPasswordFromId(self, myId:str)->str():
        """
            \n@Param: myId - The password to find's id
            \n@Returns: The matching password 
        """
        match = list(self.userColl.find({"id": myId}))
        actualPassword = match[0]["password"]
        return actualPassword

############################################### LOW LEVEL API FUNCTIONS ###############################################

    def _createCollDNE(self, collObj:MongoClient):
        """Wrapper of lowest level api functions that creates a collection if it does not exist (DNE)"""
        exists = self.__doesCollExist(collObj)
        collName = collObj.name
        if not exists:
            print(f"Collection '{collName}' does not exist... creating")
            self.__createCollection(collObj)
        else:
            print(f"Database '{collName}' already exists")

    def __doesCollExist(self, collObj:MongoClient)->bool():
        collectionNames = self.dbClient.list_collection_names()
        return collObj.name in collectionNames

    def __createCollection(self, collObj:MongoClient):
        """Meant to help create the database & collection if they dont exist by adding dummy data"""
        dummyData = {"id": "admin-account", "username": "dev", "password": "1@Mdummy5@t@P@ssw0rD"}
        self._insertData(collObj, dummyData)
    
    def _insertData(self, collObj:MongoClient, data):
        """Accepts a list of dictionaries (or just one) to submit"""
        insertingMultiple = utils.isList(data)
        numEntries = len(data)
        if not insertingMultiple:
            collObj.insert_one(data)
        # else:               self.userColl.insert_many(data)

    def _exists(self, query:dict):
        """Returns true if an item exists with your desired traits (both key and value)"""
        match = list(self.userColl.find(query))
        numMatches = len(match)
        return numMatches > 0

    def _deserializeData(self, data:Binary):
        decodedObj = Binary(data).decode()
        deserializedObj = pickle.loads(data)
        return deserializedObj

    def _serializeObj(self, obj):
        """
            \n@Param: obj - The object to serial
            \n@Return: The serialized object
            \n@Note: Meant to serialize objects (pairs with '_deserializeData()')
        """
        serializedObj = pickle.dumps(obj)
        binarySerialObj = Binary(serializedObj)
        return binarySerialObj
