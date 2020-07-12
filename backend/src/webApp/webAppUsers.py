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
from flask_login import LoginManager, UserMixin

# For login forms
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField

#--------------------------------OUR DEPENDENCIES--------------------------------#
# Note: the number of '.' means the number of dirs to go up (1 means this dir)
from .. import emailAgent
from .. import utils
from . import webAppConsts

class UserManager():
    __userDataDir = webAppConsts.userDataDir
    __cookieDataPath = webAppConsts.cookieDataPath
    # make dir and file if they do not exist (are not tracked by git)
    if not os.path.exists(__userDataDir): os.mkdir(__userDataDir)
    if not os.path.exists(__cookieDataPath): utils.writeJson(__cookieDataPath, {})
    
    # create database of User objects (maps tokenId -> User obj)
    userDatabase = {}

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
            return UserManager.userDatabase[userToken]

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

    @classmethod
    def getUserLogin(cls, userToken)->dict():
        """
            \n@Brief: Get the user's webapp login info (username + password) based on their browser's cookie
            \n@Param: `userToken` The user's unique id retrieved from cookie
            \n@Note: username & password login info is for webApp (NOT for gmail or other email site)
            \n@Note: `userToken` is the user's unique token based on browser and cookie data
            \n@Return: {username: str, password: str}
        """
        cookieJson = utils.loadJson(cls.__cookieDataPath)
        return cookieJson[userToken]

    @classmethod
    def isUsernameInUse(cls, username)->bool():
        return cls.getUserByUsername(username) != None
    
    @classmethod
    def createSafeCookieId(cls):
        # https://docs.python.org/3/library/uuid.html -- safe random uuid
        return str(uuid.uuid4())

    @classmethod
    def getUserByUsername(cls, username):
        """
            Returns None if username does not exist
        """
        # search through user database's User objects (the values) until a User has the desired username
        findUsernameMatch = lambda x: x.webAppUsername == username
        # there should only be one (either way choose the first) or None if not found
        userMatches = list(filter(findUsernameMatch, cls.userDatabase.values()))
        userMatch = userMatches[0] if len(userMatches) > 0 else None
        return userMatch

    def addUser(self, webAppUsername, webAppPassword):
        """
            \n@Brief: Add a user
            \n@Param: webAppUsername - The user's username on the site
            \n@Param: webAppPassword - The user's password on the site
            
        """
        # do-while loop to make sure non-colliding unique id is made
        firstTime = True
        userToken = ""
        while firstTime or userToken in UserManager.userDatabase:
            firstTime = False
            userToken = UserManager.createSafeCookieId()

        # if webAppUsername already used, block it
        if UserManager.isUsernameInUse(webAppUsername):
            # self.removeUser(userToken)
            flash("Username is already in use")

        # create new email agent for each user
        UserManager.userDatabase[userToken] = User(webAppUsername, webAppPassword, userToken)

    def removeUser(self, userToken):
        """
            \n@Brief: Remove a user
            \n@Param: userToken - The user's unique token
        """
        UserManager.userDatabase[userToken].logoutClient()
        del UserManager.userDatabase[userToken]

    # ------------------------- OBSOLETE CODE ---------------------- #
    # @classmethod
    # def setUserToken(cls, username, password, userObj:User)->str():
    #     """
    #         \n@Param: `username` - The user's webapp login username
    #         \n@Param: `password` - The user's webapp login password
    #         \n@Note: username & password login info is for webApp (NOT for gmail or other email site)
    #         \n@Note: `userToken` is the user's unique token based on browser and cookie data
    #         \n@Return: The user's tokenId/userToken or unique id
    #     """
    #     cookieId = createSafeCookieId()
    #     cookieDataToAdd = {
    #         cookieId: {
    #             "username": username,
    #             "password": password,
    #             "User": userObj
    #         }
    #     }
        
    #     currCookieData = utils.loadJson(cls.__cookieDataPath)
    #     updatedCookieData = utils.mergeDicts(currCookieData, cookieDataToAdd)
    #     utils.writeJson(cls.__cookieDataPath, updatedCookieData)
    #     return cookieId

class User(UserMixin):
    """Custom user class that extends the expected class from LoginManager"""
    def __init__(self, webAppUsername, webAppPassword, userToken):
        """
            \n@Brief: Initializes a User with the most basic info needed
            \n@Param: webAppUsername - The user's username on the site
            \n@Param: webAppPassword - The user's password on the site
            \n@Param: userToken - The user's unique token id
        """
        self.webAppUsername = webAppUsername
        self.webAppPassword = webAppPassword
        self.id = userToken # needed to extend UserMixin
        self.client = emailAgent.EmailAgent(displayContacts=True, isCommandLine=False)

        # vals to be defined later
        self.fname = None
        self.lname = None
        self.emailAddress = None
        self.password = None
        
    def updateEmailLogin(self, firstname, lastname, emailAddress=None, password=None):
        """Updates class info about email/text sender"""
        self.fname = firstname
        self.lname = lastname
        self.emailAddress = emailAddress
        self.password = password
        needDefault = emailAddress == None or password == None
        print("needDefault: {0}".format(needDefault))
        self.client.setDefaultState(needDefault)
        
    def checkPassword(self, password)->bool():
        return self.webAppPassword == password

    def send(self, sendMethod, message):
        """
            \n@Brief: Sends the email/text
            \n@Param: `sendMethod` - "text" or "email"
            \n@Param: `message` - (string) The message to send
            \n@Return: Return code (Success = None, Error = stringified error message)
        """
        receiverContactInfo = self.getContactInfo()
        return self.client.sendMsg(receiverContactInfo, sendMethod=sendMethod, msgToSend=message)
    
    def userReceiveEmailUser(self, numToFetch):
        """
            \n@Brief: Receives the preliminary email data that needs to be parsed more to fully fetch an email
            \n@Param: numToFetch (int) - The number of email descriptors to get
            \n\t@Return: `{
            \n\t    error: bool,
            \n\t    text: str,
            \n\t    idDict: {'<email id>': {idx: '<list index>', desc: ''}}, # dict of email ids mapped to indexes of emailList
            \n\t    emailList: [{To, From, DateTime, Subject, Body, idNum, unread}] # list of dicts with email message data
            \n\t} If error, 'error' key will be true, printed email (or error) will be in 'text' key`
        """
        return self.client.receiveEmail(onlyUnread=False, maxFetchCount=numToFetch)
    
    def selectEmailById(self, idDict, emailList, emailId)->str():
        """
            \n@Brief: Given brief information about user's email selection options, open the correct one (by its id)
            \n@Param: idDict- dict of email ids mapped to indexes of emailList in format {'<email id>': {idx: '<list index>', desc: ''}}
            \n@Param: emailList- list of emailInfo dicts with format [{To, From, DateTime, Subject, Body, idNum, unread}]
            \n@Param: emailId- Selected email's id to open (should be determined by your code prior to calling this)
            \n@Returns: The email's contents
        """
        return self.client.openEmailById(idDict, emailList, emailId)
    
    def addContact(self, firstName, lastName, emailAddress, carrier, phoneNumber):
        """
            \n@Brief: This function is responsible for adding another contact to the contact list by processing the inputs
            \n@Param: firstName - first name of the person being added
            \n@Param: lastName - last name of the person being added
            \n@Param: email - email of the person being added
            \n@Param: carrier - carrier of the person being added
            \n@Param: phoneNumber - phone number of the person being added
        """
        self.client.addContact(firstName, lastName, emailAddress, carrier, phoneNumber)

    def getContactInfo(self):
        """Establish emailAgent client for user based on provided info & return contact info needed for other stuff"""
        # login info error-checking
        try:
            if (len(self.emailAddress) == 0 or len(self.password) == 0):
                self.client.setDefaultState(True)
            else:
                # if no errors and not empty then okay to use non default accoount
                self.client.setDefaultState(False) 
        except Exception as e:
            # if there is an error just use the default sender/receiver
            self.client.setDefaultState(True)
            
        return self.client.getReceiverContactInfo(self.fname, self.lname)

    def getContactList(self):
        return self.client.printContactListPretty(printToTerminal=False)
    
    # def updateContactList(self, firstname, lastname):
    #     self.client.updateContactInfo(firstName=firstname, lastName=lastname, addingExternally=True)

    def logoutClient(self):
        """Logout of EmailAgent"""
        self.client.logoutEmail()