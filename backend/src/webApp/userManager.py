"""
    @file Responsible for handling & keeping track of multiple users to keeping their data safe and seperate
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import base64
from datetime import datetime, timedelta
import os
import uuid

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
# from werkzeug.contrib.securecookie import SecureCookie
from flask import Flask, redirect, flash
from flask_login import LoginManager

#--------------------------------OUR DEPENDENCIES--------------------------------#
import utils
import webAppConsts
from database import databaseManager
from user import User

class UserManager():
    __userDataDir = webAppConsts.userDataDir
    __cookieDataPath = webAppConsts.cookieDataPath
    # make dir and file if they do not exist (are not tracked by git)
    if not os.path.exists(__userDataDir): os.mkdir(__userDataDir)
    if not os.path.exists(__cookieDataPath): utils.writeJson(__cookieDataPath, {})

    # MongoDB database manager
    dbManager = databaseManager.DatabaseManager()
    
    # create database of User objects (maps tokenId -> User obj)
    userDatabase = {} # TODO: remove once MongoDB fully functional

    def __init__(self, app:Flask):
        self.flaskApp = app
        self.loginManager = LoginManager(app)
        self.createLoginManager()

    def createLoginManager(self):
        """
            \n@Brief: Helper function that creates all the necessary login manager attributes (callbacks)
            \n@Note: Wrapper to provide closure for `self`
        """

        @self.loginManager.user_loader
        def loadUser(userToken):
            """
                \n@Brief: When Flask app is asked for "current_user", this decorator gets the current user's User object
                \n@Note: Refence current user with `current_user` (from flask_login import current_user) 
                \n@Param: userToken - The user's unique token id
                \n@Return: Reference to the User class related to this uuid
            """
            return UserManager.dbManager.findUser(userToken) 

        @self.loginManager.unauthorized_handler
        def onNeedToLogIn():
            """
                \n@Brief: VERY important callback that redirects the user to log in if needed --
                gets triggered by "@login_required" if page is accessed without logging in
            """
            # if user is forced to login, display this message
            # loginMsg = "Please log in to access this page"
            # flash(loginMsg)
            return redirect(webAppConsts.formSites["webAppLogin"])

    def createSafeCookieId(self):
        # https://docs.python.org/3/library/uuid.html -- safe random uuid
        return str(uuid.uuid4())

    def addUser(self, webAppUsername, webAppPassword):
        """
            \n@Brief: Add a user
            \n@Param: webAppUsername - The user's username on the site
            \n@Param: webAppPassword - The user's password on the site
            \n@Note: Username has already been checked to not be a repeat
        """
        # do-while loop to make sure non-colliding unique id is made
        while True:
            userToken = self.createSafeCookieId()
            inUse = UserManager.dbManager.isIdInUse(userToken)
            if not inUse: break # leave loop once new id is found
            else: print(f"userToken '{userToken}' is already taken")

        # create new email agent for each user
        newUserObj = User(webAppUsername, webAppPassword, userToken)
        UserManager.dbManager.addUser(userToken, webAppUsername, webAppPassword, newUserObj)

    def removeUser(self, userToken):
        """
            \n@Brief: Remove a user
            \n@Param: userToken - The user's unique token
        """
        UserManager.userDatabase[userToken].logoutClient()
        del UserManager.userDatabase[userToken]

##################################### WRAPPER FUNCTIONS FOR LOWER LEVEL API ###########################################

    @classmethod
    def getPasswordFromUsername(cls, username):
        """
            \n@Note: Wrapper for dbManager.getPasswordFromUsername so multiple classes can use this function
            \n@Param: username - The password to find's username
            \n@Returns: The matching password 
        """
        return cls.dbManager.getPasswordFromUsername(username)

    @classmethod
    def getPasswordFromId(cls, myId):
        """
            \n@Note: Wrapper for dbManager.getPasswordFromId so multiple classes can use this function
            \n@Param: myId - The password to find's id
            \n@Returns: The matching password 
        """
        return cls.dbManager.getPasswordFromId(myId)

    @classmethod
    def isUsernameInUse(cls, username):
        """Wrapper for dbManager.isUsernameInUse so multiple classes can use this function"""
        return cls.dbManager.isUsernameInUse(username)

    @classmethod
    def getUserByUsername(cls, username):
        """
            \n@Param: username: The username of the user's account
            \n@Returns: None if username does not exist
        """
        myId = cls.dbManager.getIdByUsername(username)
        return cls.dbManager.findUser(myId)
