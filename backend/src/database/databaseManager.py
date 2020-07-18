"""
    @file: This file contains the database helper class that manages both 'users' and 'contacts' collections
    @Note: Calling this with python will do nothing
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import json
import pickle, copyreg, ssl # for serializing User objects (SSL obj requires more work)
from itertools import count # to keep track of # initializations

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from pymongo import MongoClient
from bson.binary import Binary # for serializing/derializing User objects

#--------------------------------OUR DEPENDENCIES--------------------------------#
from backend.src import utils
from backend.src.database.usersCollectionManager import UsersCollectionManager
from backend.src.database.contactsCollectionManager import ContactsCollectionManager

class DatabaseManager(UsersCollectionManager, ContactsCollectionManager):
    _numInits = 0

    def __init__(self):
        """
            \n@Brief: This class is meant to help manage the database of users' information
            \n@Note: Will create the database if it does not already exist
            \n@Note: Will inheret other database managers to consolidate into one
        """
        # Inheret all functions and 'self' variables
        super().__init__()

        # only check & create database collections once
        if DatabaseManager._numInits == 0:
            # if db or collection(s) don't exist, add dummy data to them to create it
            allCollections = [self.usersColl, self.contactsColl]
            for collObj in allCollections: 
                self._createCollDNE(collObj)
        DatabaseManager._numInits += 1

