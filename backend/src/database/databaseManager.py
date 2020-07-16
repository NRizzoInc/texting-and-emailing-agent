"""
    @file: This file contains the database helper class that manages both 'users' and 'contacts' collections
    @Note: Calling this with python will do nothing
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import json
import pickle, copyreg, ssl # for serializing User objects (SSL obj requires more work)

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from pymongo import MongoClient
from bson.binary import Binary # for serializing/derializing User objects

#--------------------------------OUR DEPENDENCIES--------------------------------#
import utils
from .usersCollectionManager import UsersCollectionManager
from .contactsCollectionManager import ContactsCollectionManager

class DatabaseManager(UsersCollectionManager, ContactsCollectionManager):
    def __init__(self):
        """
            \n@Brief: This class is meant to help manage the database of users' information
            \n@Note: Will create the database if it does not already exist
            \n@Note: Will inheret other database managers to consolidate into one
        """
        # Inheret all functions and 'self' variables
        super().__init__()

        # if db or collection(s) don't exist, add dummy data to them to create it
        allCollections = [self.userColl, self.contactsColl]
        for collObj in allCollections: 
            self.createCollDNE(collObj)

