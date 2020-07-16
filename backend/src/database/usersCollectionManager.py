"""
    \n@File: Responsible for maintaing the "users" collection
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import json
import pickle, copyreg, ssl # for serializing User objects (SSL obj requires more work)

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from pymongo import MongoClient
from bson.binary import Binary # for serializing/derializing User objects

#--------------------------------OUR DEPENDENCIES--------------------------------#
import utils
from .databaseBaseClass import DatabaseBaseClass

class UsersCollectionManager(DatabaseBaseClass):
    def __init__(self):
        """
            \n@Brief: This class is responsible for managing the user's collection
            \n@Note: Inheret from DatabaseBaseClass which gives it alot of util functions and self variables
        """
        # Inheret all functions and 'self' variables
        super().__init__()

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
        self._insertData(self.usersColl, newUser)

    def isUsernameInUse(self, usernameToTest:str):
        usernameExists = self._docExists(self.usersColl, {"username": usernameToTest})
        # print(f"usernameExists: {usernameExists}")
        return usernameExists
    
    def isIdInUse(self, idToTest:str):
        idExists = self._docExists(self.usersColl, {"id": idToTest})
        # print(f"idExists: {idExists}")
        return idExists

    def getIdByUsername(self, username)->str():
        """
            \n@Param: username - The username matching the id you are looking for
            \n@Return: The corresponding id
            \n@Note: Useful if chained with other functions that require id (i.e. 'findUser()')
        """
        match = list(self.usersColl.find({"username": username}))
        matchId = match[0]["id"]
        return matchId

    def findUser(self, userToken):
        """
            \n@Param: userToken - The user's unique token id
            \n@Return: The 'User' object
        """
        userDoc = self._getDocById(self.usersColl, userToken)
        serializedUserObj = userDoc["User"]
        userObj = self._deserializeData(serializedUserObj)
        return userObj

    def getPasswordFromUsername(self, username:str)->str():
        """
            \n@Param: username - The password to find's username
            \n@Returns: The matching password 
        """
        match = list(self.usersColl.find({"username": username}))
        actualPassword = match[0]["password"]
        return actualPassword

    def getPasswordFromId(self, myId:str)->str():
        """
            \n@Param: myId - The password to find's id
            \n@Returns: The matching password 
        """
        match = list(self.usersColl.find({"id": myId}))
        actualPassword = match[0]["password"]
        return actualPassword
