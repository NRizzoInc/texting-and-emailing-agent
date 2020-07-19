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
from backend.src import utils
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
            "User": self._serializeObj(userObj) if userObj != None else None # need to serialize object for storage
        }
        self._replaceDataById(self.usersColl, userToken, newUser)

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

    def findUserById(self, userToken, UserObjRef):
        """
            \n@Param: userToken - The user's unique token id
            \n@Param: UserObjRef - reference to the constructor for the User object
            \n@Return: The 'User' object (None if 'User' DNE or unset)
        """
        userDoc = self._getDocById(self.usersColl, userToken)
        return self._createUserIfDNE(userDoc, UserObjRef)

    def getUserByUsername(self, username, UserObjRef):
        """
            \n@Param: username: The username of the user's account
            \n@Param: UserObjRef - reference to the constructor for the User object
            \n@Returns: None if username does not exist
        """
        userDoc = self._getDocByUsername(self.usersColl, username)
        return self._createUserIfDNE(userDoc, UserObjRef)

    def _createUserIfDNE(self, userDoc, UserObjRef):
        """
            \n@Brief: Get the User object referenced in the document. If it doesn't exist, create one
            \n@Param: userDoc - The dictionary containing the information belonging to a specific user
            \n@Param: UserObjRef - reference to the constructor for the User object
            \n@Returns: The User object associated with the document (creates one if not already made/set)
            \n@Note: Good if paired with '__checkIfUserValid'
        """
        userObj = self.__checkIfUserValid(userDoc)
        userId = userDoc["id"]
        return userObj if userObj != None else UserObjRef(userId)

    def __checkIfUserValid(self, userDoc:dict):
        """
            \n@Brief: Helper function that checks if the 'User' obj within the document has been set and is valid
            \n@Param: userDoc - The dictionary containing the information belonging to a specific user
            \n@Return: The User object 
        """
        if utils.keyExists(userDoc, "User") and userDoc["User"] != None:
            serializedUserObj = userDoc["User"]
            userObj = self._deserializeData(serializedUserObj)
        else: userObj = None
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
            \n@Returns: The matching password (or "" if not yet set)
        """
        match = self._getDocById(self.usersColl, myId)
        username = match["password"] if utils.keyExists(match, "password") else ""
        return username

    def updateUserObjById(self, myId:str, updatedUserObj:object)->dict():
        """
            \n@Brief: Updates the 'User' object in the document corresponding to the id
            \n@Param: myId - The UUID of the user to update
            \n@Param: updatedUser - The User object to replace the existing one with
            \n@Returns: An instance of UpdateResult
        """
        query = {"id": myId}
        # https://docs.mongodb.com/manual/reference/operator/update/#id1 -- different update commands
        # $set = set matching field
        serializedUpdatedObj = self._serializeObj(updatedUserObj)
        toUpdateWith = {"$set": {"User": serializedUpdatedObj}}
        return self.usersColl.update_one(query, toUpdateWith)

    def setUsernameById(self, myId:str, username:str):
        """
            \n@Brief: Sets the username in the database for the user with 'myId'
            \n@Param: myId - The id of the user whose username you want to set
            \n@Param: username - The username to set
            \n@Note: Probably only useful for command line uses
            \n@Returns: An instance of UpdateResult
        """
        query = {"id": myId}
        toUpdateWith = {"$set": {"username": username}}
        return self.usersColl.update_one(query, toUpdateWith)

    def setPasswordById(self, myId:str, password:str):
        """
            \n@Brief: Sets the password in the database for the user with 'myId'
            \n@Param: myId - The id of the user whose username you want to set
            \n@Param: password - The password to set
            \n@Note: Probably only useful for command line uses
            \n@Returns: An instance of UpdateResult
        """
        query = {"id": myId}
        toUpdateWith = {"$set": {"password": password}}
        return self.usersColl.update_one(query, toUpdateWith)

    def getUsernameById(self, myId:str)->str():
        """
            \n@Brief: Gets the username in the database for the user with 'myId'
            \n@Param: myId - The id of the user whose username you want to set
            \n@Returns: The username belonging to the ID (empty string if not set)
        """
        match = self._getDocById(self.usersColl, myId)
        username = match["username"] if utils.keyExists(match, "username") else ""
        return username

