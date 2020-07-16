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

    def getContactList(self, userId)->dict():
        """
            \n@Brief: Returns the contact list matching the userId
            \n@Param: userId - The UUID of the user whose contact list needs to be retrieved
            \n@Returns: Dictionary containing the user's contact list
        """
        return self.getCardById(self.contactsColl, userId)
