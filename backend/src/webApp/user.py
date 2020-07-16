"""
    @file Responsible for handling the individual User class (which extends the emailAgent class)
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from flask_login import UserMixin

#--------------------------------OUR DEPENDENCIES--------------------------------#
from emailing.emailAgent import EmailAgent

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
        self.fname = None
        self.lname = None
        self.emailAddress = None
        self.password = None
        self.numEmailsToFetch = 5 # default to 5

    def updateEmailLogin(self, firstname, lastname, emailAddress=None, password=None):
        """Updates class info about email/text sender"""
        self.fname = firstname
        self.lname = lastname
        self.emailAddress = emailAddress
        self.password = password

    def send(self, sendMethod, message):
        """
            \n@Brief: Sends the email/text
            \n@Param: `sendMethod` - "text" or "email"
            \n@Param: `message` - (string) The message to send
            \n@Return: Return code (Success = None, Error = stringified error message)
        """
        client = self.initializeEmailAgent()
        receiverContactInfo = self.getContactInfo(client)
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

    def initializeEmailAgent(self)->EmailAgent():
        """
            \n@Brief: Helps create an EmailAgent object on demand
            \n@Returns: The new EmailAgent object
        """
        newClient = EmailAgent(displayContacts=False, isCommandLine=False, userId=self.id)
        return newClient

    def getContactInfo(self, client:EmailAgent):
        """Establish emailAgent client for user based on provided info & return contact info needed for other stuff"""
        # login info error-checking
        try:
            if (len(self.emailAddress) == 0 or len(self.password) == 0):
                client.setDefaultState(True)
            else:
                # if no errors and not empty then okay to use non default accoount
                client.setDefaultState(False) 
        except Exception as e:
            # if there is an error just use the default sender/receiver
            client.setDefaultState(True)
            
        return client.getReceiverContactInfo(self.fname, self.lname)

    def getContactList(self):
        client = self.initializeEmailAgent()
        return client.printContactListPretty(printToTerminal=False)
    
    def getNumFetch(self):
        return self.numEmailsToFetch
    
    def setNumFetch(self, newVal):
        self.numEmailsToFetch = newVal
    
    # def updateContactList(self, firstname, lastname):
    #     self.client.updateContactInfo(firstName=firstname, lastName=lastname, addingExternally=True)

    def logoutClient(self, client:EmailAgent):
        """Logout of EmailAgent"""
        client.logoutEmail()
