"""
    \n@File: Responsible for maintaing the "contacts" collection
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import json

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from pymongo import MongoClient

#--------------------------------OUR DEPENDENCIES--------------------------------#
import utils
from .databaseBaseClass import DatabaseBaseClass

class ContactsCollectionManager(DatabaseBaseClass):
    def __init__(self):
        """
            \n@Brief: This class is responsible for managing the contacts's collection
            \n@Note: Inheret from DatabaseBaseClass which gives it alot of util functions and self variables
        """
        # Inheret all functions and 'self' variables
        super().__init__()

    def getContactList(self, userId:str)->dict():
        """
            \n@Brief: Returns the contact list matching the userId
            \n@Param: userId - The UUID of the user whose contact list needs to be retrieved
            \n@Returns: Dictionary containing the user's contact list
        """
        # document in database contains more than just the contact list
        contactList = self._getDocById(self.contactsColl, userId)
        if len(contactList) == 0:   return contactList
        else:                       return contactList[self.contactListKey]

    def setContactList(self, userId:str, newContactList:dict)->dict():
        """
            \n@Brief: Updates the contact list matching the userId in the database
            \n@Param: userId - The UUID of the user whose contact list needs to be retrieved
            \n@Param: newContactList - The updated contact list
            \n@Returns: Dictionary containing the updated contact list
        """
        data = {self.contactListKey: newContactList}
        toSave = utils.mergeDicts(query, data)
        self._replaceDataById(self.contactsColl, userId, toSave)
        return newContactList
