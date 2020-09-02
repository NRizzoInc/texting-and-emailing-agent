"""
    @file Responsible for handling & keeping track of multiple users to keeping their data safe and seperate
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import base64
from datetime import datetime, timedelta
import os

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
# from werkzeug.contrib.securecookie import SecureCookie
from flask import Flask, redirect, flash
from flask_login import LoginManager

#--------------------------------OUR DEPENDENCIES--------------------------------#
from backend.src import utils
from backend.src.webApp import webAppConsts
from backend.src.database.databaseManager import DatabaseManager
from backend.src.webApp.user import User

class UserManager(LoginManager, DatabaseManager):
    def __init__(self, app:Flask):
        self.flaskApp = app

        # create login manager object
        LoginManager.__init__(self, self.flaskApp)
        self.createLoginManager()

        # Create Database Manager
        DatabaseManager.__init__(self)

    def createLoginManager(self):
        """
            \n@Brief: Helper function that creates all the necessary login manager attributes (callbacks)
            \n@Note: Wrapper to provide closure for `self`
        """

        @self.user_loader
        def loadUser(userToken):
            """
                \n@Brief: When Flask app is asked for "current_user", this decorator gets the current user's User object
                \n@Note: Refence current user with `current_user` (from flask_login import current_user) 
                \n@Param: userToken - The user's unique token id
                \n@Return: Reference to the User class related to this userToken
            """
            return self.findUserById(userToken, User)

        @self.unauthorized_handler
        def onNeedToLogIn():
            """
                \n@Brief: VERY important callback that redirects the user to log in if needed --
                gets triggered by "@login_required" if page is accessed without logging in
            """
            # if user is forced to login, display this message
            # loginMsg = "Please log in to access this page"
            # flash(loginMsg)
            return redirect(webAppConsts.formSites["webAppLogin"])

    def addUser(self, webAppUsername, webAppPassword):
        """
            \n@Brief: Add a user
            \n@Param: webAppUsername - The user's username on the site
            \n@Param: webAppPassword - The user's password on the site
            \n@Note: Username has already been checked to not be a repeat
        """
        userToken = self.createSafeCookieId()

        # create new email agent for each user
        newUserObj = User(userToken)
        self._addUserToColl(userToken, webAppUsername, webAppPassword, newUserObj)

    def removeUser(self, userToken):
        """
            \n@Brief: Remove a user
            \n@Param: userToken - The user's unique token
        """
        UserManager.userDatabase[userToken].logoutClient()
        del UserManager.userDatabase[userToken]
