"""
    \n@File: Responsible for maintaing the "users" collection
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import json
import pickle, copyreg, ssl # for serializing User objects (SSL obj requires more work)

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from pymongo import MongoClient, collection
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

    def _addUserToColl(self, userToken, username, password, userObj):
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
            \n@Note: Useful if chained with other functions that require id (i.e. 'findUserById()')
        """
        match = list(self.usersColl.find({"username": username}))
        matchId = match[0]["id"]
        return matchId

    def findUserById(self, userToken):
        """
            \n@Param: userToken - The user's unique token id
            \n@Return: The 'User' object
        """
        userDoc = self._getDocById(self.usersColl, userToken)
        serializedUserObj = userDoc["User"]
        userObj = self._deserializeData(serializedUserObj)
        return userObj

    def getUserByUsername(self, username):
        """
            \n@Param: username: The username of the user's account
            \n@Returns: None if username does not exist
        """
        userDoc = self._getDocByUsername(self.usersColl, username)
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

    def updateUserObjById(self, myId:str, updatedUserObj:object)->dict():
        """
            \n@Brief: Updates the 'User' object in the document corresponding to the id
            \n@Param: myId - The UUID of the user to update
            \n@Param: updatedUser - The User object to replace the existing one with
            \n@Returns: An instance of UpdateResult
        """
        query = {"id": myId}
        # use '$' to indicate what value to change
        toUpdateWith = {"$User": updatedUserObj}
        return self.usersColl.update_one(query, toUpdateWith)
