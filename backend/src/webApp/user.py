"""
    @file Responsible for handling the individual User class (which extends the emailAgent class)
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from flask_login import UserMixin

#--------------------------------OUR DEPENDENCIES--------------------------------#
from backend.src.emailing.emailAgent import EmailAgent
from backend.src import utils

class User(UserMixin):
    def __init__(self, userId):
        """
            Custom user class that extends the expected class from LoginManager
            \n@Brief: Initializes a User with the most basic info needed
            \n@Param: userId - The user's unique token id
        """
        # needed to extend UserMixin
        self.id = userId
        # Cannot serialize this object if include this class due to SSLContext restrictions
        # define client on as needed basis & set to None on logout
        # self.client = emailAgent.EmailAgent(displayContacts=False, isCommandLine=False)

        # vals to be defined later
        self.numEmailsToFetch = 5 # default to 5

    def send(self, sendMethod:str, message:str, recvFname:str, recvLname:str, emailAddress:str, emailPassword:str):
        """
            \n@Brief: Sends the email/text
            \n@Param: `sendMethod` - "text" or "email"
            \n@Param: `message` -  The message to send
            \n@Param: `recvFname` -  The receiver's first name
            \n@Param: `recvLname` -  The receiver's last name
            \n@Param: `emailAddress` - The email to log into to send the email
            \n@Param: `emailPassword` - The password for the email to log into to send the email
            \n@Return: Return code (Success = None, Error = stringified error message)
            \n@Note: Both emailAddress & emailPassword need to be provided, or else the default account gets used
        """
        client = self.initializeEmailAgent(emailAddress=emailAddress, emailPassword=emailPassword)
        receiverContactInfo = self.getContactInfo(client, recvFname, recvLname)
        toRtn = client.sendMsg(receiverContactInfo, sendMethod=sendMethod, msgToSend=message)
        self.logoutClient(client)
        return toRtn

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
        client = self.initializeEmailAgent()
        toRtn = client.receiveEmail(onlyUnread=False, maxFetchCount=numToFetch)
        self.logoutClient(client)
        return toRtn

    def selectEmailById(self, idDict, emailList, emailId)->str():
        """
            \n@Brief: Given brief information about user's email selection options, open the correct one (by its id)
            \n@Param: idDict- dict of email ids mapped to indexes of emailList in format {'<email id>': {idx: '<list index>', desc: ''}}
            \n@Param: emailList- list of emailInfo dicts with format [{To, From, DateTime, Subject, Body, idNum, unread}]
            \n@Param: emailId- Selected email's id to open (should be determined by your code prior to calling this)
            \n@Returns: The email's contents
        """
        client = self.initializeEmailAgent()
        toRtn = client.openEmailById(idDict, emailList, emailId)
        self.logoutClient(client)
        return toRtn

    def addContact(self, firstName, lastName, emailAddress, carrier, phoneNumber):
        """
            \n@Brief: This function is responsible for adding another contact to the contact list by processing the inputs
            \n@Param: firstName - first name of the person being added
            \n@Param: lastName - last name of the person being added
            \n@Param: email - email of the person being added
            \n@Param: carrier - carrier of the person being added
            \n@Param: phoneNumber - phone number of the person being added
        """
        client = self.initializeEmailAgent()
        client.addContact(firstName, lastName, emailAddress, carrier, phoneNumber)
        self.logoutClient(client)

    def initializeEmailAgent(self, emailAddress:str=None, emailPassword:str=None)->EmailAgent():
        """
            \n@Brief: Helps create an EmailAgent object on demand
            \n@Param: `emailAddress` - The email to log into to
            \n@Param: `emailPassword` - The password for the email to log into to
            \n@Returns: The new EmailAgent object
            \n@Note: Both emailAddress & emailPassword need to be provided, or else the default account gets used
        """
        newClient = EmailAgent(
            displayContacts=False,
            isCommandLine=False,
            userId=self.id,
            emailAddress=emailAddress,
            emailPassword=emailPassword
        )
        return newClient

    def getContactInfo(self, client:EmailAgent, recvFname:str, recvLname:str):
        """
            \n@Brief: Gets the contact info to send msg to a specific person
            \n@Param: client - An EmailAgent obj that has already been created
            \n@Param: recvFname - The receiver's first name
            \n@Param: recvLname - The receiver's last name
        """
        return client.getReceiverContactInfo(recvFname, recvLname)

    def getContactList(self):
        client = self.initializeEmailAgent()
        return client.printContactListPretty(printToTerminal=False)

    def getProvidersList(self)->list():
        """Returns a list of all valid providers that can be texted via email"""
        client = self.initializeEmailAgent()
        return client.getTextableProviders()

    def getNumFetch(self):
        return self.numEmailsToFetch
    
    def setNumFetch(self, newVal):
        self.numEmailsToFetch = newVal
    
    # def updateContactList(self, firstname, lastname):
    #     self.client.updateContactInfo(firstName=firstname, lastName=lastname, addingExternally=True)

    def logoutClient(self, client:EmailAgent):
        """Logout of EmailAgent"""
        client.logoutEmail()
