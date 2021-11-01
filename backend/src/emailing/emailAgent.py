#!/usr/bin/python3
'''
    The purpose of this file is to be able to send/receive emails
'''
#TODO: If contact list has multiple emails, allow user to pick

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import os
import sys
import json
import pprint
import getpass
import time
import datetime
import shutil
import re
import platform
from signal import signal, SIGINT # to catch control-c
# Email imports
import ssl
import smtplib # to send emails- Simple Mail Transfer Protocol
import imaplib # to receive emails- Internet Access Message Protocol
import email
from email.mime.application import MIMEApplication 
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template # needed to send a template txt file
# url imports to attach urls links
import urllib
from urllib import request 
from urllib.parse import urlparse # WARNING: python3 only

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
import fleep # to identify file types

#--------------------------------OUR DEPENDENCIES--------------------------------#
from backend.src import utils
from backend.src.database.databaseManager import DatabaseManager

class EmailAgent(DatabaseManager):
    """
        \n@Brief: This class handles the sending and receiving of email/text messages
        \n@Note: The main high level api functions once the class is instantiated are: sendMsg, receiveEmail/openEmailById
        \n@Note:The helper high level api functions are: updateContactInfo(), self.EmailAgent.printContactListPretty(),
        self.EmailAgent.setDefaultState(bool), getReceiverContactInfo(firstName, lastName)
    """
    # static helper varaibles to remove magic strings
    _unreadEmailFilter = "(UNSEEN)"
    _allEmailFilter = "ALL"
    __success = 0
    __error = -1

    def __init__(self,
                 displayContacts:bool=True,
                 isCommandLine:bool=False,
                 useDefault:bool=False,
                 userId:str="",
                 emailAddress:str=None,
                 emailPassword:str=None
                ):
        """
            \n@Brief: This class is responsible for sending & receiving emails
            \n@input: displayContacts- If true, print the contact list during init
            \n@input: isCommandLine- True if using through the command line
            \n@input: useDefault- True to use the default email account to send/receive texts & emails
            \n@Param: userId - (optional) The UUID belonging to the user for non-command line uses
            \n@Param: emailAddress - (optional) The email address of the account you want to log in to
            \n@Param: emailPassword - (optional) The email password of the account you want to log in to
            \n@Note: Both emailAddress & emailPassword need to be provided, or else the default account gets used
            \n@Note: useDefault will be automically set to true if another login is not provided
        """
        # this variable is neccesary for the webApp and anything that wants to 
        # implement this class not using the command line
        self.isCommandLine = isCommandLine

        # Inheret all functions and 'self' variables
        DatabaseManager.__init__(self, printCollectionCreation=not self.isCommandLine)

        self.__pathToThisDir = os.path.dirname(os.path.abspath(__file__))
        self.__srcDir = os.path.join(self.__pathToThisDir, "..")
        self.__backendDir = os.path.join(self.__srcDir, "..")
        self.__emailDataDir = os.path.join(self.__backendDir, "emailData")

        # information to login
        self.emailProvidersInfo = utils.loadJson(os.path.join(self.__emailDataDir, "emailProvidersInfo.json"))
        self.sendToPhone = False
        self.context = ssl.SSLContext(ssl.PROTOCOL_SSLv23) 
        self.SMTPClient = smtplib.SMTP
        self.IMAPClient = imaplib.IMAP4 
        self.isConnectedToServers = False

        # these are the credentials to login to a throwaway gmail account 
        # with lower security that I set up for this program
        # contained within gitignored json that I will only give to contributors
        dummyEmailLoginPath = os.path.join(self.__emailDataDir, "defaultLogin.json")
        dummyLogin = utils.loadJson(dummyEmailLoginPath)["dummy-email"]
        # only use provided login if all pieces present
        isLoginProvided = utils.isNonEmptyStr(emailAddress) and utils.isNonEmptyStr(emailPassword)
        self.myEmailAddress =   emailAddress  if isLoginProvided else dummyLogin["email-address"]
        self.password =         emailPassword if isLoginProvided else dummyLogin["password"]

        # boolean that when set to True means the program will login
        # to a known email account without extra inputs needed
        # will be set to true if non-default account is used and login entered
        self.useDefault = useDefault and not isLoginProvided

        # allows user to not have to type login multiple times
        self.loginAlreadySet = False 

        # if running via CLI, access account meant for CLI user
        self._userId = self._cliUserId if self.isCommandLine else userId

        # text to match on receive side
        self.username = self.configureLogin()
        self._uniqueUserEmailSignature = f"Dest: {self.username}"

        # Fetch the contact list from the database
        self.contactList = self.getContactList(self._userId)

        # work around for sending text messages with char limit (wait to add content)
        self.attachmentsList = []
        self.textMsgToSend = ''

        # display contents of the existing contact list
        if displayContacts: self.printContactListPretty()


    def chooseEmailFilter(self, onlyUnread:bool):
        """
            \n@Brief: Helper function to determine which filter to use
            \n@Param: onlyUnread - True if only want unread emails
        """
        return EmailAgent._unreadEmailFilter if onlyUnread else EmailAgent._allEmailFilter

    def configureLogin(self, overrideUsername:bool=False, overridePassword:bool=False):
        """
            \n@Brief: Helper function that sets username & password if needed
            \n@Param: (optional - default = False) overrideUsername - Update the username?
            \n@Param: (optional - default = False) overridePassword - Update the password?
            \n@Return: The current user's username
        """
        # if not command line, just return with the username
        if not self.isCommandLine: return self.getUsernameById(self._userId)

        # Create user document in database if it doesn't already exist
        self._createUserDocIfIdDNE(self._userId)

        # will only be the case for command line (myUsername == "" if first time doing command line)
        myUsername = self.getUsernameById(self._userId)
        myPassword = self.getPasswordFromId(self._userId)
        needToSetUsername = overrideUsername or myUsername == ""
        needToSetPassword = overridePassword or myPassword == ""

        if needToSetUsername:
            while True:
                newUsername = utils.promptUntilSuccess("Enter your display name when sending texts (can be updated later): ")
                if self.isUsernameInUse(newUsername):
                    useWebLogin = utils.promptUntilSuccess(
                        f"Username {newUsername} is already taken, attempt to login (y/n): ",
                        utils.containsConfirmation
                    )
                    if useWebLogin:
                        newAcctPass = self.getPasswordFromUsername(newUsername)
                        inputPass = utils.promptUntilSuccess("Enter the password: ", hideInput=True)
                        validLogin = newAcctPass == inputPass
                        if not validLogin: print("Invalid password") # repeat loop
                        else: 
                            # update localhost password to match
                            self.setPasswordById(self._userId, newAcctPass)
                            break # exit loop
                else: break # not taken, so break out of loop
            self.setUsernameById(self._userId, newUsername)
            myUsername = newUsername

        if needToSetPassword and self.countNumUsernameMatch(myUsername) > 1:
            print("Cannot change password since using web app login")
        elif needToSetPassword:
            while True:
                newPassword = utils.promptUntilSuccess(
                    "Enter your password (to login via the web GUI - can be updated later): ", hideInput=True)
                newPasswordConfirm = utils.promptUntilSuccess(
                    "Re-Enter your password: ", hideInput=True)
                if newPassword == newPasswordConfirm:   break
                else:                                   print("Passwords do not match, please try again")
            self.setPasswordById(self._userId, newPassword)

        # finally return the username
        return myUsername

    def createTextReturnInstructions(self)->str():
        """Helper function for telling receiver how to send a message back so it can be received"""
        myUsername = self.getUsernameById(self._userId)
        # Note: Text will not send if you do 'To: <username>' -- probably interferes with native email code
        msgToAppend = f"\n\nAdd '{self._uniqueUserEmailSignature}' if you want them to be able to see your response"
        return msgToAppend

    def getTextableProviders(self)->list():
        """
            \n@Brief: Returns list containing all cell service providers that allow texts via email
            \n@Note: Based on self.emailProvidersInfo
        """
        filterPossibleSms = lambda name: utils.keyExists(self.emailProvidersInfo[name]["smtpServer"], "SMS-Gateways")
        return list(filter(filterPossibleSms, self.emailProvidersInfo.keys()))

    def sendMsg(self, receiverContactInfo, sendMethod:str=None, msgToSend:str=None)->str():
        """
            \n@Brief: Calls all other functions necessary to send an a message (either through text or email)
            \n@Param: receiverContactInfo- a dictionary about the receiver of format: 
            \n    {
            \n        lastName: {
            \n            firstName: {email: "", phoneNumber: "", carrier: ""}
            \n        }
            \n    }
            \n@Param: sendMethod- (optional) a string that should either be 'email' or 'text'
            \n@Param: msgToSend- (optional - None) a string that contains the message that is desired to be sent
            \n@Return: String of error message if error occurs (None if success)
        """
        # Check if passed contact info is valid
        isContactValid = receiverContactInfo != None and len(receiverContactInfo) > 0
        if not isContactValid: return "Invalid Contact (probably does not exist)"

        # check if connected to email servers, if not connect
        if not self.isConnectedToServers:
            err = self.connectToEmailServers()
            hasError = err != None
            if (hasError): return err

        # second check if valid "sendMethod" is received
        if sendMethod == None or sendMethod == '': sendTextBool = None
        elif sendMethod == 'email': sendTextBool = False
        elif sendMethod == 'text': sendTextBool = True
        else: raise Exception("Invalid sendMethod Param passed to function!")

        if self.isCommandLine:
            msg = self.composeMsg(receiverContactInfo, sendingText=sendTextBool, msgToSend=msgToSend)
        else:
            msg = self.composeMsg(receiverContactInfo, sendingText=sendTextBool, msgToSend=msgToSend)
        
        # send the message via the server set up earlier.
        if msg == None: # will only be None if can't send email or text message
            print("Could not send an email or text message")
            
        elif msg == "invalid":
            print("No valid method of sending a message was chosen!")

        else:
            # method of sending email changes depending on whether it is an email of text
            if self.sendToPhone is True:
                msgList = self.adjustTextMsg(msg)
                msgList[-1] += self.createTextReturnInstructions() # add instructions to end of msg

                # send pure text first
                for currMsg in msgList:
                    smsText = currMsg.strip() # need to convert message to string
                    # only send text bubble is there is actual text to send
                    if (not smsText.isspace() and len(smsText) > 0): 
                        self.SMTPClient.sendmail(msg["From"], msg["To"], smsText)
                        # add microscopic delay to ensure that messages arrive in correct order
                        time.sleep(10/1000) # input is in seconds (convert to milliseconds)
                    else:
                        print("Note sending empty message")

                # send attachments last
                for attachments in self.attachmentsList:
                    sms = attachments.as_string()
                    self.SMTPClient.sendmail(msg["From"], msg["To"], sms)
                self.attachmentsList = [] # reset list

            else:
                self.SMTPClient.send_message(msg)
            if self.isCommandLine: print("Successfully sent the email/text to {0} {1}".format(
                receiverContactInfo['firstName'], receiverContactInfo['lastName']))
        return None

    def composeMsg(self, receiverContactInfo, sendingText:bool=False, msgToSend:str=None):
        '''
            This function is responsible for composing the email message that get sent out
            - Args:
                * sendingText: (optional) a bool that tells program if it should be sending a text message
                If None provded, user will be asked 
                * msgToSend: (optional - None) a string containing the desired message to be sent

            - Returns:
                * The sendable message 
                * 'invalid' if no type of message was chosen to be send
                * None if selected message could not be sent
        '''

        # user did not provide method before hand
        sendMethod="invalid" # either "text" or "email" (default to "invalid" incase incase of error)
        if sendingText == None:
            isText = utils.promptUntilSuccess("Send text message if possible (y/n): ", utils.containsConfirmation) == "y"
            if isText: sendMethod = "text"
            elif not isText:
                isEmail = utils.promptUntilSuccess("Send email message (y/n): ", utils.containsConfirmation) == "y"
                if isEmail: sendMethod = "email" 
                else: msg = 'invalid' # signifies to caller that no message is being sent
        elif sendingText: sendMethod = "text"
        else:             sendMethod = "email"

        # actually compose the message (for either email or text)
        sendFn = {
            "text": self.composeTextMsg,
            "email": self.composeEmailMsg,
            "invalid": lambda *args: "invalid" # set msg = "invalid" to show bad inputs
        }
        msg = sendFn[sendMethod](receiverContactInfo, msgToSend)

        # check if user added an attachment (either link or path to file) in message
        if (msg != 'invalid' and msg != None):
            # DO NOT scan for attachment on remote machine if a user can input something malicious
            if self.isCommandLine: self.scanForAttachments()

            # check if text payload is empty besides newline (enter to submit)
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    if (part.get_payload().isspace()):
                        # if so, remove the text payload
                        part.set_payload(None)
        return msg

    def composeTextMsg(self, receiverContactInfo, msgToSend:str=None):
        '''
            \n@Param: receiverContactInfo - a dictionary containing the following information:
            \n\t{
            \n\t    firstName: str,
            \n\t    lastName: str,
            \n\t    email: str,
            \n\t    carrier: str,
            \n\t    phoneNumber: str
            \n\t}
            \n@Param: msgToSend - (optional) message string to be sent (dont fill in if want to querry for it later)
        '''
        receiverCarrier = receiverContactInfo['carrier'].lower()

        # Check if this email provider allows emails to be sent to phone numbers
        # use index of lower case match to get actual value of key according to original list
        possibleProviders = self.getTextableProviders()
        lowerCaseProviders = list(map(lambda x:x.lower(), possibleProviders))

        if receiverCarrier in lowerCaseProviders:
            indexInListOfCarrier = lowerCaseProviders.index(receiverCarrier)
            keyForDesiredCarrier = possibleProviders[indexInListOfCarrier]
            domainName = self.emailProvidersInfo[keyForDesiredCarrier]["smtpServer"]['SMS-Gateways']

        else:
            # if carrier cannot accepts texts as emaisl
            print("Sending text messages to {0} {1} is not possible due to their cell provider".format(
                receiverContactInfo['firstName'], receiverContactInfo['lastName']))

            # Since cant send a text message to the person, ask if user want to send email message instead
            emailInstead = utils.promptUntilSuccess(
                "Do you want to send an email instead (y/n): ", successCondition=utils.containsConfirmation)

            if emailInstead == 'y': return self.composeEmailMsg()
            # If user cant send a text and wont send an email then just return
            else: return None

        # Remove all non-numerical parts of phone number (should be contiguous 10 digit number)
        actualPhoneNum = ''.join(char for char in receiverContactInfo['phoneNumber'] if char.isdigit())
        
        textMsgAddress = "{0}@{1}".format(actualPhoneNum, domainName)
        if self.isCommandLine: print("Sending text message to {0}".format(textMsgAddress))
        
        # Get content to send in text message
        if msgToSend != None:
            # not using command line or message already provided
            body = msgToSend
            
        elif self.isCommandLine:
            # dynamically initialize keyboard class as it causes issues on ubuntu 18.04 LTS Server
            from backend.src.emailing.keyboardHandler import KeyboardMonitor
            keyboardMonitor = KeyboardMonitor()
            body = keyboardMonitor._getMultiLineInput("Please enter the message you would like to send")

        # setup the Parameters of the message
        msg = MIMEMultipart() # create a message object with the body
        msg['From'] = self.myEmailAddress
        msg['To'] = textMsgAddress
        msg['Subject'] = "" # keep newline
        self.textMsgToSend = body # dont add body yet bc text message
        
        self.sendToPhone = True

        return msg

    def adjustTextMsg(self, msg:MIMEMultipart):
        """
            @Brief: 
                Text messages are limited to 120 characters each.
                This function will split a long message into multiple ones.
                Keeps words together in same text.
            @Args: msg (string)
            Return: a list of messages(strings) to send
        """
        msgList = []
        
        text = self.textMsgToSend
        subject = msg['Subject']
        totalMsg = str(subject) + str(text)
        totalLength = len(totalMsg)
        charLimit = 120

        # message is over character limit (and is not one giant word/url)
        if totalLength > charLimit and text.count(' ') > 0:
            count = 0
            lastIndex = 0
            toAppend = ''

            # split long message into multiple messages
            while lastIndex < totalLength:
                # check there is at least the charLimit # of chars left in string
                if (totalLength-lastIndex > charLimit):

                    # find the first space occuring prior to 120 char mark (go in reverse during search)
                    for index, thisChar in enumerate(reversed(totalMsg[lastIndex:lastIndex+charLimit])):
                        if (thisChar == ' '): 
                            # new position is start + charLimit - # left shifts
                            endPos = lastIndex + charLimit - index  
                            toAppend = totalMsg[lastIndex:endPos]
                            lastIndex = endPos 
                            print("Appending: {0}".format(toAppend))
                            break # break for loop to begin next message search

                # less chars than limit, string to append equals remaining
                else:
                    toAppend = totalMsg[lastIndex:]
                    lastIndex = totalLength # exit while-loop condition

                tempMsg = toAppend.strip() # create a message object with the body

                # add to list
                msgList.append(tempMsg)

        # normal (send one message)
        elif (not text.isspace()):
            msgList.append(text.strip())

        return msgList

    def composeEmailMsg(self, receiverContactInfo, msgToSend:str=None):
        '''
            This function provides the user with a method of choosing which email format to send and entering the desired message.
            @Args:
                - receiverContactInfo: a dictionary containing the following information 
                    {first name, last name, email, carrier, phone number}
                - msgToSend: (optional) message string to be sent (dont fill in if want to querry for it later)
        '''
        if msgToSend == None and self.isCommandLine:
            # dynamically initialize keyboard class as it causes issues on ubuntu 18.04 LTS Server
            from backend.src.emailing.keyboardHandler import KeyboardMonitor
            keyboardMonitor = KeyboardMonitor()
            # create the body of the email to send
            msgToSend = keyboardMonitor._getMultiLineInput("Please enter the message you would like to send")

        # setup the Parameters of the message
        msg = MIMEMultipart() # create a message object
        msg['From'] = self.myEmailAddress
        msg['To'] = receiverContactInfo['email'] # send message as if it were a text
        msg['Subject'] = "Emailing Application"
        # add in the message body
        msg.attach(MIMEText(msgToSend, 'plain'))
        return msg


    def readTemplate(self, pathToFile):
        with open(pathToFile, 'r+', encoding='utf-8') as templateFile:
            templateFileContent = templateFile.read()
        return Template(templateFileContent)

    def getReceiverContactInfo(self, myFirstName:str, myLastName:str)->dict():
        """
            \n@Brief: This function will search the existing database for entries with the input firstName and lastName.
            \n@Param: myFirstName - The receiver's firstname
            \n@Param: myLastName - The receiver's lastname
            \n@Returns: Dictionary of format: {firstname: "", lastname: "", email: "", carrier: "", phoneNumber: ""}
            (Will be an empty dict receiver DNE in contact list)
            \n@Note: The phone number return accepts common type of seperaters or none (ex: '-')
        """

        receiverContactInfoDict = {}
        email = ''
        phoneNumber = ''
        carrier = ''

        # Go through the list looking for name matches (case-insensitive)
        for lastName in self.contactList.keys():
            for firstName in self.contactList[lastName].keys():
                if firstName.lower() == myFirstName.lower() and lastName.lower() == myLastName.lower():
                    if self.isCommandLine: print("\nFound a match!\n")
                    contactFirstName = firstName
                    contactLastName = lastName
                    # stores contact information in the form {"email": "blah@gmail.com", "carrier":"version"}
                    receiverContactInfoDict = self.contactList[lastName][firstName]
                    email = receiverContactInfoDict['email']
                    phoneNumber = receiverContactInfoDict['phoneNumber']
                    carrier = receiverContactInfoDict['carrier']

        # if values were not initialized then no match was found
        if email == '' and phoneNumber == '' and carrier == '':
            toPrint = [
                f"\nContact '{myFirstName} {myLastName}' does not exist!",
                f"Add them to the contact list by calling this program followed by 'using the --add-contact flag'",
                "\n"
            ]
            # print immediately and return
            # Return an empty dict to signify DNE
            if self.isCommandLine: print("\n".join(toPrint))
            return {}

        foundContactPrint = [
            f"Based on the inputs of:",
            f"first name = {myFirstName}",
            f"last name = {myLastName}",
            f"\nThe contact found is: {contactFirstName} {contactLastName}",
            f"Email Address: {email}",
            f"Carrier: {carrier}",
            f"Phone Number: {phoneNumber}",
        ]

        # print messages (if command line)
        if self.isCommandLine: print("\n".join(foundContactPrint))

        dictToRtn = {
            'firstName' : contactFirstName,
            'lastName': contactLastName,
            'email': email,
            'carrier': carrier,
            'phoneNumber' : phoneNumber
        }

        return dictToRtn

    def connectToEmailServers(self, emailAddr=None, password=None, endPastConnection=True)->str():
        """
            \n@Brief: This function is responsible for connecting to the email server.
            \n@Param: emailAddr- (optional) The email address to connect to
            \n@Param: password- (optional) The password for the email address
            \n@Param: endPastConnection- (optional) If object already logged in, should it logout before logging in
            \n@Return: None if success. String error message if error
        """

        if endPastConnection: self.logoutEmail()

        # Get email login
        if emailAddr != None and password != None:
            self.myEmailAddress = emailAddr
            self.password = password
        elif self.loginAlreadySet == False:
            # already have logins, don't need to ask for it again
            pass
        elif self.useDefault == False:
            # if false then make user use their own email username and password
            self.myEmailAddress = input("Enter your email address: ")
            self.password = getpass.getpass(prompt="Password for user {0}: ".format(self.myEmailAddress))
        else:
            print("Using default gmail account created for this program to login to an email\n")
            # I created a dummy gmail account that this program can login to
        self.loginAlreadySet = True # set to true so next time the user will not have to retype login info

        
        emailServiceProviderInfo = self.getEmailProviderInfo(emailWebsite=self.myEmailAddress)
        smtpInfo = emailServiceProviderInfo["smtpServer"]
        imapInfo = emailServiceProviderInfo["imapServer"]

        imapHostAddr = imapInfo['hostAddress']
        smtpHostAddr = smtpInfo['hostAddress']
        imapPort = imapInfo['portNum']
        smtpPort = smtpInfo['portNum']

        # Establish connection to both email servers using self.myEmailAddress and password given by user
        # Have to choose correct protocol for what the program is trying to do(IMAP-receive, SMTP-send)
        self.connectSMTP(smtpHostAddr, smtpPort)
        self.connectIMAP(imapHostAddr, imapPort)

        # Try to login to email server, if it fails then catch exception
        try:
            self.SMTPClient.login(self.myEmailAddress, self.password)
            self.IMAPClient.login(self.myEmailAddress, self.password)
            self.isConnectedToServers = True
            if self.isCommandLine: print("Successfully logged into email account!\n")
            return None
            
        except smtplib.SMTPAuthenticationError as rawError:
            errCode = str(rawError.smtp_code)
            errorMsg = str(rawError.smtp_error.decode()).replace("\n", "")
            formattedErr = f"Error code {errCode} - {errorMsg}"
            linkToPage = "https://myaccount.google.com/lesssecureapps"
            errorMsg = ""

            # Only print custom message if can copy on command line
            if '535' in formattedErr and self.isCommandLine:
                # Sometimes smtp servers wont allow connection becuase the apps trying to connect are not secure enough
                # TODO make connection more secure
                errorMsg = "\n".join([
                    "\nCould not connect to email server because of error:\n{0}\n".format(formattedErr),
                    "Try changing your account settings to allow less secure apps to allow connection to be made.",
                    "Or try enabling two factor authorization and generating an app-password\n{0}".format(linkToPage),
                    "Quiting program, try connecting again with correct email/password",
                    "after making the changes, or trying a different email\n"
                ])
            else:
                errorMsg = "\nEncountered error while trying to connect to email server: \n{0}".format(formattedErr)

            if (self.isCommandLine):
                print(errorMsg)
                sys.exit(EmailAgent.__error)
            else:
                return errorMsg

    def connectSMTP(self, server, portNum):
        if self.isCommandLine: print("Connecting to SMTP email server")
        self.SMTPClient = smtplib.SMTP(host=server, port=int(portNum))
        self.SMTPClient.ehlo()
        self.SMTPClient.starttls(context=self.context)
        self.SMTPClient.ehlo()    

    def connectIMAP(self, server, portNum):    
        if self.isCommandLine: print("Connecting to IMAP email server")
        self.IMAPClient = imaplib.IMAP4_SSL(host=server, port=int(portNum), ssl_context=self.context)

    def getEmailProviderInfo(self, emailWebsite:str="")->dict():
        """
            \n@Brief: This function returns a dictionary containing information 
            about a host address and port number of an email company.
            \n@Param: emailWebsite(str)- the email company/website(like name@gmail.com, name@verizon.net, etc...)
            \n\t(optional)- used to guess some information w/o user input
            \n@Return: emailServiceProviderInfo(dict)- Email company info necessary for logging in with format:
            \n\t{
            \n\t    "smtpServer": {"hostAddress": "smtp.gmail.com", "portNum": "587"},
            \n\t    "imapServer": {"hostAddress": "imap.gmail.com", "portNum": "993"}   
            \n\t}
        """
        # convert the dictionary to all lower case to make searching easier
        lowerCaseList = list(map(lambda x:x.lower(), self.emailProvidersInfo.keys()))
        dictKeysMappedToList = list(map(lambda x:x, self.emailProvidersInfo.keys()))

        # helper variables while searching
        foundValidEmailProvider = False
        emailServiceProviderInfo = {}
        emailServiceProvider = ""

        # use email name (if possible) to guess provider to skip user input
        if len(emailWebsite) > 0 and not emailWebsite.isspace():
            emailServiceProvider = (emailWebsite[emailWebsite.find("@")+1:emailWebsite.find('.')])
            if self.isCommandLine: print("Email Provider: {0}".format(emailServiceProvider))
            if emailServiceProvider.lower() in lowerCaseList:
                foundValidEmailProvider = True


        while foundValidEmailProvider is False and self.useDefault is False:
            print("The available list of providers you can login to is: \n{0} \
                  \nSelect 'Default' if you dont want to skip logging in.".format(list(self.emailProvidersInfo.keys())))
            emailServiceProvider = input("\nWhich email service provider do you want to login to: ")

            # see if email service provider exists in the list (case-insensitive)
            # -use lambda function to turn list to lowercase
            if emailServiceProvider.lower() in lowerCaseList:
                break
            else:
                print("The desired email service provider not supported! Try using another one")
            
        # get the index of name match in the list (regardless of case)
        index = lowerCaseList.index(emailServiceProvider.lower())

        # Using the index of where the correct key is located, 
        # use the dict which contains all entries of original dict to get exact key name
        dictKeyName = dictKeysMappedToList[index]

        # Get the information pertaining to this dict key
        emailServiceProviderInfo = self.emailProvidersInfo[dictKeyName]
        foundValidEmailProvider = True
            
        # if user wants to use the pre-setup gmail accoun,
        # then program needs to change which smtp server it is trying to access
        if self.useDefault is True or emailServiceProvider.lower() == "default":
            emailServiceProviderInfo = self.emailProvidersInfo['Default']
            # set to true for case of user opting into default during runtime
            self.useDefault = True 

        return emailServiceProviderInfo
    
    def addContact(self, firstName, lastName, email, carrier, phoneNumber):
        """
            \n@Brief: This function is responsible for adding another contact to the contact list by processing the inputs
            \n@Param: firstName - first name of the person being added
            \n@Param: lastName - last name of the person being added
            \n@Param: email - email of the person being added
            \n@Param: carrier - carrier of the person being added
            \n@Param: phoneNumber - phone number of the person being added
        """
        
        commonDataDict = {
            'email': email,
            'phoneNumber': phoneNumber,
            'carrier': carrier
        }

        # store existing contact list so it can be modified
        newContactList = self.contactList

        # check to see if the person's last name already exists.
        lastNameLowerCaseList = list(map(lambda x:x.lower(), newContactList.keys()))
        # use index of lower case match to get actual value of key according to original mapped dict keys
        keysMappedToList = list(map(lambda x:x, newContactList.keys()))

        # If so, just modify it instead of creating an entirely new last name section
        if lastName.lower() in lastNameLowerCaseList:
            # get the actual last name (with correct capitalization)
            indexOfLastName = lastNameLowerCaseList.index(lastName.lower())
            actualLastName = keysMappedToList[indexOfLastName]

            # check if need to add the person
            firstNameLowerCaseList = list(map(lambda x:x.lower(), newContactList[actualLastName].keys()))
            if firstName.lower() not in firstNameLowerCaseList:
                newContactList[lastName][firstName] = commonDataDict
            else: 
                # if already in list, ask user if they want to update the info
                firstNameKeysMappedToList = list(map(lambda x:x, newContactList[actualLastName].keys()))
                indexOfFirstName = firstNameLowerCaseList.index(firstName.lower())
                actualFirstName = firstNameKeysMappedToList[indexOfFirstName]

                user = newContactList[actualLastName][actualFirstName]

                print(f"""\nFound user {actualLastName} {actualFirstName} with the following information: \
                          \nEmail: {user['email']} \
                          \nPhone Number: {user['phoneNumber']} \
                          \nCell Carrier: {user['carrier']} \
                    """)
                update = input("Do you want to update their information (y/n): ")

                if (update == 'y'):
                    newContactList = self.updateContactInfo(firstName=actualFirstName, lastName=actualLastName, addingExternally=False)
       
        # If last name doesnt exist in contact list yet, then add it
        else:
            newContactList[lastName] = {}
            newContactList[lastName][firstName] = commonDataDict

        # Update existing variable used by rest of program so it constantly stays up to date
        self.contactList = self.setContactList(self._userId, newContactList)

    def updateContactInfo(self, firstName=None, lastName=None, addingExternally=True):
        '''
            Returns an updated version of the contact list
            Param "addingExternally" is true if this is being called as a stand alone function
        '''

        commonDataDict = {
            'email': '',
            'phoneNumber': '',
            'carrier': ''
        }
        updatedContactList = self.contactList

        if (firstName == None or lastName == None):
            firstName = input("Enter the person's first name you want to update: ")
            lastName = input("Enter the person's last name you want to update: ")

        # check to see if the person's last name already exists.
        lastNameLowerCaseList = list(map(lambda x:x.lower(), updatedContactList.keys()))
        # use index of lower case match to get actual value of key according to original mapped dict keys
        keysMappedToList = list(map(lambda x:x, updatedContactList.keys()))

        if lastName.lower() in lastNameLowerCaseList:
            # get the actual last name (with correct capitalization)
            indexOfLastName = lastNameLowerCaseList.index(lastName.lower())
            actualLastName = keysMappedToList[indexOfLastName]

            # get the actual first name
            firstNameLowerCaseList = list(map(lambda x:x.lower(), updatedContactList[actualLastName].keys()))
            if firstName.lower() not in firstNameLowerCaseList:
                print("user not found!")
                return None
            else: 
                firstNameKeysMappedToList = list(map(lambda x:x, updatedContactList[actualLastName].keys()))
                indexOfFirstName = firstNameLowerCaseList.index(firstName.lower())
                actualFirstName = firstNameKeysMappedToList[indexOfFirstName]
                user = updatedContactList[actualLastName][actualFirstName]
        else:
            # last name not found
            print("user not found!")
            return None

        updateFirstName = utils.promptUntilSuccess(
            f"\nTheir first name is '{actualFirstName}', would you like to change it (y/n): ",
            utils.containsConfirmation
        ) =="y"
        updateLastName = utils.promptUntilSuccess(
            f"Their last name is '{actualLastName}', would you like to change it (y/n): ",
            utils.containsConfirmation
        ) =="y"
        updateEmail = utils.promptUntilSuccess(
            f"Their email is '{user['email']}', would you like to change it (y/n): ",
            utils.containsConfirmation
        ) =="y"
        updateCarrier = utils.promptUntilSuccess(
            f"Their cell phone carrier is '{user['carrier']}', would you like to change it (y/n): ",
            utils.containsConfirmation
        ) =="y"
        updatephoneNumber = utils.promptUntilSuccess(
            f"Their phone number is '{user['phoneNumber']}', would you like to change it (y/n): ",
            utils.containsConfirmation
        ) =="y"
        print('') # space the text out in terminal

        newFirstName = firstName
        newLastName = lastName
        commonDataDict['email'] = user['email']
        commonDataDict['carrier'] = user['carrier']
        commonDataDict['phoneNumber'] = user['phoneNumber']
        updatePhrase = "What would you like to change the <field> to: "
        if (updateFirstName):
            newFirstName = utils.promptUntilSuccess(updatePhrase.replace('<field>', 'first name'))
        if (updateLastName):
            newLastName = utils.promptUntilSuccess(updatePhrase.replace('<field>', 'last name'))
        if (updateEmail):
            commonDataDict['email'] = utils.promptUntilSuccess(updatePhrase.replace('<field>', 'email'))
        if (updateCarrier):
            commonDataDict['carrier'] = utils.promptUntilSuccess(updatePhrase.replace('<field>', 'cell carrier'))
        if (updatephoneNumber):
            commonDataDict['phoneNumber'] = utils.promptUntilSuccess(updatePhrase.replace('<field>', 'phone number'))
        
        if (len(updatedContactList[actualLastName]) == 1):
            del updatedContactList[actualLastName]
            updatedContactList[newLastName] = {}
            updatedContactList[newLastName][newFirstName] = commonDataDict
        else:
            # update these in reverse order (go from branches -> root) to make saving data easy
            if (updateEmail or updateCarrier or updatephoneNumber):
                updatedContactList[actualLastName][actualFirstName] = commonDataDict
            if (updateFirstName):
                updatedContactList[actualLastName][newFirstName] = dict(updatedContactList[actualLastName][actualFirstName])
                del updatedContactList[actualLastName][actualFirstName]
                actualFirstName = newFirstName
            if (updateLastName):
                # get a copy of everything past the last name
                updatedContactList[newLastName] = dict(updatedContactList[actualLastName])
                del updatedContactList[actualLastName]
                actualLastName = newLastName

        
        # handled by other function if internal
        if (addingExternally):
            # Update existing variable used by rest of program so it constantly stays up to date
            self.contactList = self.setContactList(self._userId, updatedContactList)
            self.printContactListPretty()

        return updatedContactList

    def simpleAddContact(self):
        '''
            This function is responsible for adding another contact to the contact list 
            (no args needed because it will ask for inputs).
        '''

        firstName = input("Please enter their first name: ")
        lastName = input("Please enter their last name: ")
        myEmail = input("Please enter their email: ")
        carrier = input("Please enter their cell phone carrier this person uses: ")
        phoneNumber = input("Please enter their phone number: ")

        # call function that handles the actual adding
        self.addContact(firstName, lastName, myEmail, carrier, phoneNumber)

    def getNumRelevantNewEmails(self):
        """
            \n@Brief: Gets all current unread emails and filters by if they are relevant to user
            \n@Returns: {
            \n\t"numUnread": int,
            \n\t"relevantEmailsInfo": dict # matches return from self.getEmailsGradually()
            \n}
        """
        allUnreadEmailsInfo = self.getEmailsGradually(
            emailFilter=EmailAgent._unreadEmailFilter, printEmails=False, leaveUnread=True)

        # iterate through unread emails and filter to get only relevant ones
        for idx, emailInfo in enumerate(allUnreadEmailsInfo["emailList"]):
            # remove from emailList & dict if not relevant
            if emailInfo["belongsToUser"] == False:
                # since idDict maps emailId to emailList idx, need to reverse search to get dict key to remove
                keyList = list(allUnreadEmailsInfo["idDict"].keys())
                valList = list(allUnreadEmailsInfo["idDict"].values())
                dictIdxToRemove = valList.index(idx)
                dictKeyToRemove = keyList[dictIdxToRemove]
                del allUnreadEmailsInfo["idDict"][dictKeyToRemove]

                # normal
                del allUnreadEmailsInfo["emailList"][idx]

        return {
            "numUnread": len(allUnreadEmailsInfo["emailList"]),
            "relevantEmailsInfo": allUnreadEmailsInfo
        }

    def _waitForNewMessage(self, startedBySendingEmail:bool):
        """
            \n@Brief: This function halts the program until a new message is detected in the inbox
            \n@Param: startedBySendingEmail- bool that informs program if the first action taken was to send
        """
        # Ask if they want to wait for a reply (only if user didnt start off by sending an email)
        waitForMsg = ''
        if startedBySendingEmail == False:
            if self.isCommandLine:
                while ('y' not in waitForMsg and 'n' not in waitForMsg):
                    waitForMsg = input("\nDo you want to wait for a new message (y/n): ")
            else: 
                raise Exception("IMPLEMENT NON-COMMAND LINE '_waitForNewMessage'")
        else:
            waitForMsg = 'y'

        if 'y' not in waitForMsg:
            return # quit function if dont want to wait

        # wait for new message
        else:
            print("waiting for new message...\n")
            normalEmailInfoRtn = {}
            while True:
                # Check for emails
                # Defaults to only look for unread emails
                relevantUnreadDict = self.getNumRelevantNewEmails()
                numEmails = relevantUnreadDict["numUnread"]
                normalEmailInfoRtn = relevantUnreadDict["relevantEmailsInfo"]

                if numEmails > 0: break
                else:
                    print("{0} - No New Message".format(str(datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S"))))
                    # check intermittenly
                    time.sleep(10) # in seconds

            # if this point is reached, new email detected and can end function so program can continue!
            print("{0} - New email message detected!".format(str(datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S"))))

            # return to main receive function but have it stop early to not recur
            self.receiveEmail(onlyUnread=True, recursiveCall=True, fetchedEmailsDict=normalEmailInfoRtn)


    def getEmailListIDs(self, emailFilter:str=_unreadEmailFilter)->list():
        """
            \n@brief: Helper function that gets all the email ids (belonging to emailFilter)
            \n@Param: emailFilter(str): either 'ALL' or '(UNSEEN)' for only unread emails 
            \n@return: List of email ids matching the filter
        """
        # first check if connected to email servers, if not connect
        if not self.isConnectedToServers:
            err = self.connectToEmailServers()
            hasError = err != None
            if (hasError):
                # return "Error connecting to email server: \n\n{0}".format(err)
                return [] # return empty list to not cause other errors

        # verify correct input entered
        if emailFilter != EmailAgent._unreadEmailFilter and emailFilter != EmailAgent._allEmailFilter:
            print("WARNING UNKNOWN EMAIL FILTER ENTERED- may result in undefined behavior")

        # opens folder/label you want to read from
        self.IMAPClient.select('INBOX', readonly=False)
        # print("Successfully Opened Inbox")
                    
        # get all the emails and their id #'s that match the filter
        rtnCode, data = self.IMAPClient.search(None, emailFilter) 
        if rtnCode != "OK":
            print("Bad return code from inbox!")

        msgIdsList = data[0].decode().split()
        msgIdsList.reverse()
        return msgIdsList

    def fetchEmail(self, emailIdNum:int, leaveUnread:bool=True)->bytearray():
        """
            \n@Brief: Helper function that fetches and returns emails of the specified id number
            \n@Param: emailIdNum- the id number of the email to fetch
            \n@Param: leaveUnread- Dont open the email (leave as unread)
            \n@Return: A raw email byte string that can be converted into a Message object (need to use email.message_from_bytes())
            \n@Note: call 'processRawEmail(rawEmail, emailIdNum)' to convert to usable form

        """
        openCode = self.openUnread if leaveUnread else self.openMarkRead
        rtnCode, emailData = self.IMAPClient.fetch(emailIdNum, openCode) 
        if (rtnCode != "OK"):
            print("Bad email return code received!!")
            
        rawEmail = emailData[0][1]
        return rawEmail



    def getEmailListWithContent(self, emailFilter:str=_unreadEmailFilter,  leaveUnread=True)->list():
        """
            \n@brief: Helper function that fetches the data for all emails (matching the filter) and returns the list
            \n@Param: emailFilter(str): either 'ALL' or '(UNSEEN)' for only unread emails 
            \n@Param: leaveUnread- Dont open the email (leave as unread)
            \n@return: List of dictionaries: {To, From, DateTime, Subject, Body, idNum, unread}} 
            \n@Note: call 'processEmailDict()' on the returned list to print the emails and their ids nicely
        """
        # Get both types of lists so that if reading all emails, can mark ones as unread
        idListUnread = self.getEmailListIDs(emailFilter=EmailAgent._unreadEmailFilter)
        idListALL = self.getEmailListIDs(emailFilter=EmailAgent._allEmailFilter)
        if emailFilter == EmailAgent._unreadEmailFilter:
            idList = idListUnread
        else:
            idList = idListALL
    

        # get all emails
        emailList = []
        for idNum in idList:
            rawEmail = self.fetchEmail(idNum, leaveUnread=leaveUnread)

            # function returns (To, From, DateTime, Subject, Body)
            emailUnreadBool = idNum in idListUnread 
            emailMsg = self.processRawEmail(rawEmail, idNum, unread=emailUnreadBool)
            emailList.append(emailMsg)

        return emailList

    def getListAllEmails(self)->list():
        """
            \n@brief: Fetches all emails and lists them by id number
            \n@return: List of dictionaries: {To, From, DateTime, Subject, Body, idNum, unread}} 
            \n@Note: call 'processEmailDict()' on the returned dict to print the email nicely
        """
        emailList = self.getEmailListWithContent(emailFilter=EmailAgent._allEmailFilter)
        return emailList

    def getUnreadEmails(self)->list():
        """
            \n@brief: Fetches all unread emails and lists them by id number
            \n@return: List of dictionaries: {To, From, DateTime, Subject, Body, idNum, unread}} 
            \n@Note: call 'processEmailDict()' on the returned dict to print the email nicely
        """
        emailList = self.getEmailListWithContent(emailFilter=_unreadEmailFilter)
        return emailList

    ############################# Mark as (un)read functions ##################################################
    # Note: +/-FLAGS either adds or removes flag (Dont work due to "unexpected response")
    # Warning: These will throw exceptions if the email is already in the state you are trying to set it to
    # Catch the error as that means you are trying to set them to the state they are in
    ###########################################################################################################
    def markAsUnread(self, emailId:str):
        """
            Mark an email (based on its 'emailId') as unread
            WARNING: Only works if email is not ALREADY unread
        """
        try:
            # need to connect & open inbox to mark as read
            if not self.isConnectedToServers: self.connectToEmailServers()
            self.IMAPClient.select('INBOX', readonly=False)
            self.IMAPClient.store(str(int(emailId)), "-FLAGS", "\SEEN")
        except Exception as err:
            print(f"error marking {emailId} as read: {err}")
            return

    def markAsRead(self, emailId:str):
        """
            Mark an email (based on its 'emailId') as read
            WARNING: Only works if email is not ALREADY read 
        """
        try:
            # need to connect & open inbox to mark as read
            if not self.isConnectedToServers: self.connectToEmailServers()
            self.IMAPClient.select('INBOX', readonly=False)
            self.IMAPClient.store(str(int(emailId)), "+FLAGS", "\SEEN")
        except Exception as err:
            print(f"error marking {emailId} as read: {err}")
            return

    ###########################################################################################################

    def printEmailListPretty(self, emailList:list, lowerBound:int=0, upperBound:int=-1):
        """
            \n@Brief- Takes email list and prints: "Mail Id #: <subject> "
            \n@Param- emailDict(list): [{To, From, DateTime, Subject, Body, idNum, unread}]
            \n@Param- lowerBound(int): the index to start printing ids from 
            \n@Param- upperBound(int): the index to stop printing ids 
            \n@Return- None
        """
        if emailList == None or len(emailList) == 0: 
            print("No emails!")
            return
        # shrink list according to function args
        if (upperBound != -1): 
            emailList = emailList[lowerBound:upperBound]
        else:
            emailList = emailList[lowerBound:]
        for emailDict in emailList:
            print("{0}) {1}".format(emailDict["idNum"], emailDict["Subject"]))

    def _getEmailDescriptor(self, emailMsg:dict)->str():
        """
            \n@Brief: Internal function which returns useful messages about an email for a user to access
            \n@Param: emailMsg(dict)- a dictionary of the email with format 
            {To, From, DateTime, Subject, Body, idNum, unread}
            \n@Return: String of printed line content
        """
        # if unread, print it
        unreadText = "(unread)" if emailMsg["unread"] == True else ""

        # get terminal size to make message appear on one line (subtract to make comfortable)
        columns, rows = shutil.get_terminal_size(fallback=(80, 24))
        # last 5 comes from email id reaching up to 99999 (might need to make more)
        spaceCushion = len(emailMsg["DateTime"]) + len(" - #) ") + len(unreadText) + 5

        # actually format the brief description string 
        descStr = ""
        if (emailMsg['Subject'].strip().isspace() or emailMsg['Subject'] == '' or emailMsg['Subject'] == None):
            # there is no subject, show part of message instead
            descStr = "{0} - #{1}) {2}...{3}".format(
                emailMsg['DateTime'] , emailMsg['idNum'], emailMsg['Body'][:columns-spaceCushion], unreadText)

        # there is an actual subject in the message
        else:
            overflow = columns - len(emailMsg["Subject"]) - spaceCushion
            moreToMsg = "" # leave empty, if not enough space, add them
            if overflow < 0: 
                emailMsg = emailMsg[:overflow]
                moreToMsg = "..."
            descStr = "{0} - #{1}) {2}{3}{4}".format(
                emailMsg['DateTime'],  emailMsg['idNum'], emailMsg['Subject'], moreToMsg, unreadText)

        return descStr


    def getEmailsGradually(self,
            emailFilter:str=_unreadEmailFilter,
            printDescriptors:bool=True,
            leaveUnread:int=True,
            maxFetchCount=-1,
            printEmails:bool=True
        )->dict():
        """
            \n@Brief- Takes email dict and prints out email nicely for user
            \n@Param: emailFilter(str): either 'ALL' or '(UNSEEN)' for only unread emails 
            \n@Param: printDescriptors(bool)- if true, print "<email id>) <email subject>" for all emails
            \n@Param: leaveUnread- Dont open the email (leave as unread)
            \n@Param: maxFetchCount- The maximum number of emails to fetch (default to -1 = no limit)
            \n@Param: printEmails - Should each email be printed out (note, if not command line, always False)
            \n@Return- {
            \n\t"emailList": list({To, From, DateTime, Subject, Body, idNum, unread, belongsToUser}),
            \n\t"idDict": dict({'[insert email id]': {idx: '[list index]', desc: ''})
            \n}
            \n@emailList: list of dicts with email message data
            \n@idDict: dict of email ids mapped to indexes of emailList
        """
        # Get both types of lists so that if reading all emails, can mark ones as unread
        idListUnread = self.getEmailListIDs(emailFilter=EmailAgent._unreadEmailFilter)
        idListALL = self.getEmailListIDs(emailFilter=EmailAgent._allEmailFilter)
        if emailFilter == EmailAgent._unreadEmailFilter:
            idList = idListUnread
        else:
            idList = idListALL

        emailList = []
        idDict = {}
        if not self.isCommandLine: print(f"Fetching x{maxFetchCount} emails -- {self.username}")
        def fetchEmailsWorker():
            numFetched = 0
            for idx, idNum in enumerate(idList):
                rawEmail = self.fetchEmail(idNum, leaveUnread=leaveUnread)
                emailUnreadBool = idNum in idListUnread 
                emailMsg = self.processRawEmail(rawEmail, idNum, unread=emailUnreadBool)
                if emailMsg["belongsToUser"] == True:
                    emailList.append(emailMsg)
                    emailDescLine = "" # default to empty string 
                    if printDescriptors:
                        emailDescLine = self._getEmailDescriptor(emailMsg)
                        if (self.isCommandLine and printEmails): print(emailDescLine)
                    idDict[idNum] = {"idx": numFetched, "desc": emailDescLine}
                    numFetched+=1

                # exit for loop if fetched enough
                if (maxFetchCount != -1 and numFetched >= maxFetchCount): return
            return

        # if command line, do special trick to get user to stop the fetching
        if self.isCommandLine:
            # dynamically initialize keyboard class as it causes issues on ubuntu 18.04 LTS Server
            from backend.src.emailing.keyboardHandler import KeyboardMonitor
            keyboardMonitor = KeyboardMonitor()
            keyboardMonitor._stopOnKeypress(
                fetchEmailsWorker,
                prompt="stop fetching emails (this may take awhile)",
                toPrintOnStop="Stopped fetching\n",
                printPrompts=printEmails
            )
        else: fetchEmailsWorker()

        return {"emailList": emailList, "idDict": idDict}

    def _openEmail(self, idDict:dict, emailList:list, idSelected:int=-1)->(str(), dict()):
        """
            \n@Brief: Helper function that determines which email the user wants to open, printing and returning it
            \n@Param: idDict- dict of email ids mapped to indexes of emailList in format {'<email id>': {idx: '<list index>', desc: ''}}
            \n@Param: emailList- list of emailInfo dicts with format [{To, From, DateTime, Subject, Body, idNum, unread}]
            \n@Param: idSelected- (optional) pre-selected email id to open (usually used for non-command line applications)
            \n@Return(touple): (printedStr, emailDict)
            \n@Return: printedStr- string of what is printed to the terminal
            \n@Return: emailDict- email info dict of format {To, From, DateTime, Subject, Body, idNum, unread}
            \n@Note: If no emails in list, return touple of ("", {})
        """
        emailListIdx = -1
        if self.isCommandLine and idSelected == -1:
            # making sure there is an email to open
            if len(idDict) == 0:
                # return empty values for callers if nothing found
                printedStr = "No Emails Found!"
                emailDict = {}
                print(printedStr)
                return (printedStr, emailDict)

            # error checking for valid email id
            idListInt = utils.convertToIntList(idDict.keys())
            while not idSelected in idListInt:
                idSelected = input("Enter email id to open: ").replace('\n', '').strip()
                if idSelected.isspace() or not idSelected.isdigit(): idSelected = -1
                idSelected = int(idSelected)

        # open selected email
        relevantInfo = idDict[str(idSelected)]
        emailListIdx = relevantInfo["idx"]
        emailDict = emailList[emailListIdx]
        printedStr = self.processEmailDict(emailDict)

        # if the email is not ALREADY unread, mark it as read
        if emailDict["unread"] == True: self.markAsRead(emailDict["idNum"])
        return (printedStr, emailDict)

    def _reply(self, startedBySendingEmail:bool, emailMsgDict:dict):
        """
            \n@Brief: Helper function that determines if user wants to reply to email
            \n@Param: startedBySendingEmail- bool that informs program if the first action taken was to send
            \n@Param: emailMsgDict- dict of info about email of format {To, From, DateTime, Subject, Body, idNum, unread}
        """
        # only ask this question if user didnt start off by sending emails
        if startedBySendingEmail == False: 
            if self.isCommandLine:
                replyBool = input("Do you want to reply to this email (y/n): ")
            else:
                raise Exception("IMPLEMENT NON-COMMAND LINE '_reply'")
        else:
            replyBool = 'n'

        if 'y' in replyBool:
            # send response to the information of "from" from the received email
            contactInfo = self.numberToContact(emailMsgDict["From"])

            # if contactInfo is None/empty, then sender of email not in contact list. Resort to other methods
            if contactInfo == None or len(contactInfo) == 0:
                # signifies sender was a cell phone
                if '@' in emailMsgDict["From"]:
                    # get phoneNumber/carrier info
                    tempDict = self.phoneNumberToParts(emailMsgDict["From"])
                    # if it was a text message then only need this piece of information
                    contactInfo['phoneNumber'] = tempDict['phoneNumber']
                    contactInfo['carrier'] = tempDict['carrier']

                # message was from an actual email
                else:
                    contactInfo['email'] = emailMsgDict['From']


            self.sendMsg(contactInfo)

    def receiveEmail(self,
                     startedBySendingEmail=False,
                     onlyUnread:bool=True,
                     recursiveCall:bool=False,
                     maxFetchCount:int=-1,
                     fetchedEmailsDict:dict=None
                    )->dict():
        """
            \n@Brief: High level api function which allows user to receive an email
            \n@Note: If called by non-command line application, need to parse return & call `openEmailById()`
            - return["emailList"]["desc"] for each emails' brief summary. Id is stored in return["emailList"]
            \n@Param: startedBySendingEmail- True if started off by sending email and want to wait for users reponse
            \n@Param: onlyUnread- When set to true, no command line input needed to tell which messages to read
            \n@Param: recursiveCall- bool used to prevent infinite recursion when waiting for new email
            \n@Param: maxFetchCount- The maximum number of emails to fetch (default to -1 = no limit)
            \n@Param: fetchedEmailsDict - (optional) Only set this to a return from 'getEmailsGradually'
            (Bypasses calling this function locally, hence prevents redundancy)
            \n\t@Return: `{
            \n\t    error: bool,
            \n\t    text: str,
            \n\t    idDict: {'<email id>': {idx: '<list index>', desc: ''}}, # dict of email ids mapped to indexes of emailList
            \n\t    emailList: [{To, From, DateTime, Subject, Body, idNum, unread}] # list of dicts with email message data
            \n\t} If error, 'error' key will be true, printed email (or error) will be in 'text' key`
        """
        toRtn = {"error": False, "text": "", "idDict": {}, "emailList": []}

        # first check if connected to email servers, if not connect
        if not self.isConnectedToServers:
            err = self.connectToEmailServers()
            hasError = err != None
            if (hasError):
                toRtn["error"] = True
                toRtn["text"] = err
                return toRtn

        # only get email dict if not already provided
        if fetchedEmailsDict == None or len(fetchedEmailsDict) == 0:
            emailFilter = self.chooseEmailFilter(onlyUnread)
            fetchedEmailsDict = self.getEmailsGradually(emailFilter=emailFilter, maxFetchCount=maxFetchCount)
        else:
            # print out each description
            for currMsg in fetchedEmailsDict["idDict"].values():
                currMsgDesc = currMsg["desc"]
                print(currMsgDesc)

        # due to depth of fetchedEmailsDict, have to manually set values of toRtn
        toRtn = utils.mergeDicts(toRtn, fetchedEmailsDict)

        # if command line, can just ask user, otherwise need to call another function to select & open email by id
        if (self.isCommandLine):
            self.recvCommandLine(startedBySendingEmail, recursiveCall, toRtn["emailList"], toRtn["idDict"])
        return toRtn

    def openEmailById(self, idDict, emailList, emailId)->str():
        """
            \n@Brief: High-level api helper function for non-command line applications that get email message by its id
            \n@Note: Call `receiveEmail()` to get idDict & emailList which contains summaries
            that need to be proccessed to determine which one to select and get its full content
            \n@Param: idDict- dict of email ids mapped to indexes of emailList in format {'<email id>': {idx: '<list index>', desc: ''}}
            \n@Param: emailList- list of emailInfo dicts with format [{To, From, DateTime, Subject, Body, idNum, unread}]
            \n@Param: emailId- Selected email's id to open (should be determined by your code prior to calling this)
            \n@Returns: String containing the email's contents
        """
        printedStr, emailInfoDict = self._openEmail(idDict, emailList, idSelected=emailId)
        return printedStr

    def recvCommandLine(self, startedBySendingEmail, recursiveCall, emailList, idDict):
        """
            \n@Brief: Lower level api function which allows user to receive an email via command line
            \n@Param: startedBySendingEmail- True if started off by sending email and want to wait for users reponse
            \n@Param: recursiveCall- bool used to prevent infinite recursion when waiting for new email
            \n@Param: emailList- List of all email messages
            \n@emailList: list of dicts with email message data. Format [{To, From, DateTime, Subject, Body, idNum, unread}]
            \n@idDict: dict of email ids mapped to indexes of emailList in format {'<email id>': {idx: '<list index>', desc: ''}}
            \n@Return: String of error message if error occurs (None if success)
        """
        # intially set to True but immediately set to False in loop
        # only set to True again if you wait for new messages
        keepCheckingInbox = True 
        while keepCheckingInbox: 
            keepCheckingInbox = False
            printedStr, emailInfoDict = self._openEmail(idDict, emailList)

            # check to make sure there are actual emails to open
            if len(emailInfoDict) > 0:
                self._reply(startedBySendingEmail, emailInfoDict)
            else:
                # no emails, maybe user wants to wait for them
                break 
            
            # check if user wants to continue opening emails 
            if 'y' in input("Continue opening emails (y/n): "):
                keepCheckingInbox = True
            else: 
                keepCheckingInbox = False

        # check to make sure this function wasnt called by one of the functions called in this function
        # trying to prevent infinite recursion (just want to get to the _openEmail part for _waitForNewMessage)
        if recursiveCall:
            return
        self._waitForNewMessage(startedBySendingEmail)
            
        print("Done Receiving Emails")
        return None

    def numberToContact(self, fullPhoneNumber:str)->dict():
        """
            \n@Brief: This function will attempt to match a phone number to an existing contact
            \n@Return: fullPhoneNumber- Contact info dictionary of format: {first name, last name, email, carrier, phone number}
            \n@Note: The phone number return accepts common type of seperaters or none (ex: '-')
        """
        # seperate phone number into parts (phoneNumber and carrier)
        dataDict = self.phoneNumberToParts(fullPhoneNumber) 

        # iterate through contact list and check if phone number matches
        for lastNames in self.contactList.keys():
            for firstNames in self.contactList[lastNames].keys():
                # check if phone number matches
                if self.contactList[lastNames][firstNames]["phoneNumber"].replace('-', '') == dataDict['phoneNumber']:
                    print("Matched received email to an existing contact!!")
                    return self.getReceiverContactInfo(firstNames, lastNames)

        # if reached this point then did not find number in contact list
        return None

    def phoneNumberToParts(self, fullPhoneNumber:str):
        '''
            Args:
                -fullPhoneNumber: a string of format xxxyyyzzzz@carrier.com

            Returns: Dictionary of format {phoneNumber, carrier}
                -phoneNumber
                -carrier
        '''

        # only keep part of number before the '@'
        phoneNumber = fullPhoneNumber[0:fullPhoneNumber.index('@')]

        # keep everything after the '@'
        smsGatewayTag = fullPhoneNumber[fullPhoneNumber.index('@'):]
        
        # check if sms-gateway exists in email providers list
        for provider in self.emailProvidersInfo.keys():
            # check if provider has an sms-gateway
            if 'SMS-Gateway' in self.emailProvidersInfo[provider]['smtpServer'].keys():
                # check if gateway matches
                if self.emailProvidersInfo[provider]['smtpServer']['SMS-Gateway'].lower() == smsGatewayTag:
                    carrier = provider
                    return {'phoneNumber':phoneNumber, 'carrier':carrier}
        
        # if code gets here, return phoneNumber but carrier is None
        return {'phoneNumber':phoneNumber, 'carrier': None}


    def setDefaultState(self, newState:bool):
        ''' 
            This function is responsible for changing the 'self' variable "useDefault" 
            to whatever the argument newState is.
        '''
        self.useDefault = newState

    
    def getDefaultState(self):
        ''' 
            This function is responsible for getting the 'self' variable "useDefault" 
        '''
        return self.useDefault 


    def processRawEmail(self, rawEmail:bytearray, idNum:int, unread:bool=False)->dict():
        """
            \n@Brief: This function returns the body of the raw email. The raw email needs to be processed because it contains alot of junk that makes it illegible 
            \n@Param: rawEmail: a byte string that can be converted into a Message object
            \n@Param: idNum: the id number associated with the email from the imap server
            \n@Param: unread(optional): bool that user can use tells program this email is unread if True
            \n@Return: refinedEmail(dict):  Dictionary with format: 
            \n{
            \n\t"To": "", 
            \n\t"From": "", 
            \n\t"DateTime": "", 
            \n\t"Subject": "", 
            \n\t"body": "", 
            \n\t"idNum": "", 
            \n\t"unread": bool,
            \n\t"belongsToUser": bool # true if this email is relevant to the logged in user
            \n}
        """
        # convert byte literal to string removing b''
        emailMsg = email.message_from_bytes(rawEmail)      

        # If message is multi part we only want the text version of the body
        # This walks the message and gets the body.
        body = ""
        if emailMsg.is_multipart():
            for part in emailMsg.walk():       
                if part.get_content_type() == "text/plain":
                    #to control automatic email-style MIME decoding (e.g., Base64, uuencode, quoted-printable)
                    body = part.get_payload(decode=True) 
                    body = body.decode()

                elif part.get_content_type() == "text/html":
                    continue

        # check if the email is relevant to the logged in user
        # remove special footer if there
        belongsToUser = body.find(self._uniqueUserEmailSignature) != -1
        if belongsToUser: body = body.replace(self._uniqueUserEmailSignature, "").strip()

        # Get date and time of email
        dataTuple = email.utils.parsedate_tz(emailMsg['Date'])
        if dataTuple:
            local_date = datetime.datetime.fromtimestamp(
                email.utils.mktime_tz(dataTuple))
            dateTime = local_date.strftime("%a, %d %b %Y %H:%M:%S")

        emailMsgDict = {
            "To":               emailMsg['To'],
            "From":             emailMsg['From'],
            "DateTime":         dateTime,
            "Subject":          emailMsg['Subject'],
            "Body":             body,
            "idNum":            idNum,
            "unread":           unread,
            "belongsToUser":    belongsToUser
        }

        return emailMsgDict

    def processEmailDict(self, emailDict:dict)->str():
        """
            \n@brief: Convience function which passes preformatted dictionary to processedEmail 
            \n@Param: emailDict(dict) = {
                    "To": "", 
                    "From": "", 
                    "DateTime": "", 
                    "Subject": "", 
                    "Body": "",
                    "idNum": ""
                }
            \n@Return: string of what is printed to the terminal
        """
        sampleDict = {
            "To": "", 
            "From": "", 
            "DateTime": "", 
            "Subject": "", 
            "Body": "",
            "idNum": "",
            "unread": bool(),
            "belongsToUser": bool()
        }
        if (emailDict.keys() != sampleDict.keys()):
            raise Exception("Incorrectly Passed Dictionary, needs this format: {0}".format(sampleDict))
        
        return self.processedEmail(emailDict["To"], emailDict["From"], emailDict["DateTime"], emailDict["Subject"], emailDict["Body"])

    def processedEmail(self, To:str, From:str, DateTime:str, Subject:str, Body:str)->str():
        """
            \n@brief: Prints the processed email
            \n@Param: To- Who the is receiving the message (usually the user using this code)
            \n@Param: From- Who the message is from 
            \n@Param: dateTime- Timestamp of when the message was sent
            \n@Param: subject- The subject
            \n@Param: body- The actual message
            \n@Return: string of what's printed to the terminal
            \n@note: Delinator is only put on message if in command line
        """
        # email delineator (get column size)
        columns, rows = shutil.get_terminal_size(fallback=(80, 24))
        delineator = columns - 2 # have to account for '<' and '>' chars on either end 
        deliniatorStr = "\n<{0}>\n".format('-'*delineator)
        
        strToPrint = ""
        if(self.isCommandLine): strToPrint += deliniatorStr
        strToPrint += """
        \nEmail:\n
        \nTo: {0}
        \nFrom: {1}
        \nDateTime: {2}
        \nSubject: {3}
        \n\nBody: \n\n{4}
        """.format(To, From, DateTime, Subject, Body)

        if (self.isCommandLine):
            strToPrint += deliniatorStr
            print(strToPrint)
        return strToPrint

    def scanForAttachments(self):
        '''
            @brief: scans self.textMsgToSend for attachments that it can add on to self.attachmentsList
            @Param: None
            @return: None
        '''

        attachmentList = []
        # check for file paths (starts with /, C:\, or D:\)- more thorough checks done later
        myPlatform = platform.system()
        if myPlatform == "Windows":
            regexPaths = r"([a-z, A-Z]:\\[^.]+.[^\s]+)" # <drive-letter>:\<words>.<extension><space>
        elif myPlatform == "Linux":
            regexPaths = r"(.*[/|~/][^.]+..[^\s]+)" # <~/ or /><words>.<extension><space>
        else:
            raise Exception( + " is currently unsupported")
        attachmentFilePaths = re.findall(regexPaths, self.textMsgToSend)
        attachmentList.extend(attachmentFilePaths)
        
        # add attachments that were found
        if len(attachmentList) > 0:
            print("Checking if the following items are valid: {0}".format(attachmentList))
            for toAttach in attachmentList:
                self.addAttachment(toAttach)

    def addAttachment(self, toAttach:str):
        '''
            @breif: adds new attachment to self.attachmentsList for future sending
            @Param: toAttach: a string that can either be a path to a local file or a url 
            
        '''
        # check if valid file path
        isValidPath = os.path.exists(toAttach)
        if (isValidPath):
            print("File " + toAttach + " exists")
            # read the attachment and add it
            attachmentName = os.path.basename(toAttach)
            with open(toAttach, 'rb') as attachment:
                attachable = MIMEApplication(attachment.read(), Name=attachmentName)
            
            attachable['Content-Disposition'] = 'attachment; filename={0}'.format(attachmentName)
            self.attachmentsList.append(attachable)

        # check if valid url (dangeroud for remote execution)
        # isValidUrl = self.isURLValid(toAttach)
        # if (isValidUrl):
        #     # use an agent or else browser will block it
        #     request = urllib.request.Request(toAttach, headers={'User-Agent': 'Mozilla/5.0'})
        #     attachable = MIMEApplication(urllib.request.urlopen(request).read(), Name="URL Link")
        #     attachable['Content-Disposition'] = 'attachment; filename={0}'.format("URL Link")
        #     print("Adding url '" + toAttach + "' to attachmentsList")
        #     self.attachmentsList.append(attachable)
           
        if (isValidPath):
            # remove text from payload that was attachment
            self.textMsgToSend = self.textMsgToSend.replace(toAttach, '', 1)

    def isURLValid(self, url:str):
        '''
            @brief: determines if a url is valid syntactically, is a link to media (gif, video, picture), and it exists
            @args: url: a string containing the url
            @return: bool (true if valid, false if invalid)
        '''
        try: 
            # check if syntax of url is valid before GET requesting it (saves time)
            result = urlparse(url)
            syntacticallyValid = all([result.scheme, result.netloc, result.path])
            if (not syntacticallyValid): return False

            # check if url exists (use an agent or else browser will block)
            request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            returnCode = urllib.request.urlopen(request).getcode()
            if (returnCode != 200):
                print("bad http code, rejecting url " + url)
                return False
            else:
                return True
            
            # check if file type is media (pic/video/gif)
            # full list from fleep.supported_types: 
            #  ['3d-image', 'archive', 'audio', 'database', 'document', 'executable', 'font',
            #     'raster-image', 'raw-image', 'system', 'vector-image', 'video']
            # validTypes = ['3d-image', 'audio', 'raster-image', 'raw-image', 'vector-image', 'video']
            # urlContent = urllib.request.urlopen(request).read() # return is bytes
            # info = fleep.get(urlContent)
            # if info.type[0] in validTypes: 
            #     return True
            # else: 
            #     print("Type {0} is not accepted".format(info.type[0]))
            #     return False

        except:
            print("NOT A VALID URL: " + url)
            return False

    # prints the contact list and returns the printed string nicely printed
    def printContactListPretty(self, printToTerminal=True):
        self.contactList = self.getContactList(self._userId)
        formattedContactList = pprint.pformat(self.contactList)
        if self.isCommandLine and printToTerminal:  print(f"The current contacts list is:\n{formattedContactList}")
        else:                                       return formattedContactList

    def logoutEmail(self):
        '''
            This function is responsible for having the email server close connections with the server.
            Need to make it a function due to the fact that logging out requires different code depening on the type of server 
        '''
        # depending on situation, one of them might not have logged in in the first place
        if self.isConnectedToServers:
            try:
                self.SMTPClient.quit()
            except Exception as e:
                pass

            try:
                self.IMAPClient.logout()
            except Exception as e:
                pass
        self.isConnectedToServers = False
