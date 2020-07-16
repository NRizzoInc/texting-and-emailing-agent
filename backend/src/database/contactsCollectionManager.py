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
