#!/usr/bin/python3
'''
    The purpose of this file is to be able to send/receive emails
'''
#TODO: If contact list has multiple emails, allow user to pick
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

# 3rd party Dependencies
import fleep # to identify file types

class emailAgent():
    """
        \n@Brief: This class handles the sending and receiving of email/text messages
        \n@Note: The main high level api functions once the class is instantiated are: sendMsg, receiveMsg
        \n@Note:The helper high level api functions are: updateContactList(), self.emailAgent.printContactListPretty(),
        self.emailAgent.setDefaultState(bool), get_receiver_contact_info(firstName, lastName)
    """
    # static helper varaibles to remove magic strings
    _unreadEmailFilter = "(UNSEEN)"
    _allEmailFilter = "ALL"

    def __init__(self, displayContacts=True, commandLine=False, useDefault=False):
        '''
            This class is responsible for sending emails 
        '''
        self.__pathToThisDir = os.path.dirname(os.path.abspath(__file__))
        self.messageTemplatesDir = os.path.join(self.__pathToThisDir, "templates", "emailTemplates")
        self.pathToContactList = os.path.join(self.__pathToThisDir, "emailData", "contacts.json")


        # Open the contact list file (create new file if it does not exist)
        if not os.path.exists(self.pathToContactList):
            with open(self.pathToContactList, 'w+') as writeFile:
                json.dump({}, writeFile) #write empty dictionary to file (creates the file)
        self.contactList = self.loadJson(self.pathToContactList)

        # information to login
        self.emailProvidersInfo = self.loadJson(os.path.join(self.__pathToThisDir, "emailData", "emailProvidersInfo.json"))
        self.sendToPhone = False
        self.context = ssl.SSLContext(ssl.PROTOCOL_SSLv23) 
        self.SMTPClient = smtplib.SMTP
        self.IMAPClient = imaplib.IMAP4 
        self.connectedToServers = False

        # these are the credentials to login to a throwaway gmail account 
        # with lower security that I set up for this program
        self.myEmailAddress = "codinggenius9@gmail.com"
        self.password = "codingisfun1"
        # will be set to true if non-default account is used and login entered
        # allows user to not hav eto tpe login multiple times
        self.loginAlreadySet = False 
        # boolean that when set to True means the program will login
        # to a known email account wihtout extra inputs needed
        self.useDefault = useDefault 

        # this var will get be filled with content printed to terminal
        # retreive information with getPrintedString() such that it gets cleared
        self.printedString = "" 

        # this variable is neccesary for the webApp and anything that wants to 
        # implement this class not using the command line
        self.commandLine = commandLine

        # work around for sending text messages with char limit (wait to add content)
        self.attachmentsList = []
        self.textMsgToSend = ''

        # display contents of the existing contact list
        if displayContacts is True:    
            self.webAppPrintWrapper("The current contact list is:\n")
            printableContactList = pprint.pformat(self.contactList)
            self.webAppPrintWrapper(printableContactList)

    # returns the contact list as it is currently in the contact list file
    def getContactList(self):
        return self.loadJson(self.pathToContactList)

    def sendMsg(self, receiverContactInfo, sendMethod:str='', msgToSend:str=''):
        """
            \n@Brief: Calls all other functions necessary to send an a message (either through text or email)
            \n@Param: receiverContactInfo- a dictionary about the receiver of format: 
            \n    {
            \n        lastName: {
            \n            firstName: {email: "", phoneNumber: "", carrier: ""}
            \n        }
            \n    }
            \n@Param: sendMethod- a string that should either be 'email' or 'text'
            \n@Param: msgToSend- a string that contains the message that is desired to be sent
        """            

        # first check if connected to email servers, if not connect
        if not self.connectedToServers:
            self.connectToEmailServers()

        # second check if valid "sendMethod" is received
        if sendMethod == '': pass
        elif sendMethod == 'email': sendTextBool = False
        elif sendMethod == 'text': sendTextBool = True
        else: raise Exception("Invalid sendMethod Param passed to function!")

        if self.commandLine:
            msg = self.composeMsg(receiverContactInfo, msgToSend=msgToSend)
        else:
            msg = self.composeMsg(receiverContactInfo, sendingText=sendTextBool, msgToSend=msgToSend)
        
        # send the message via the server set up earlier.
        if msg == None: # will only be None if can't send email or text message
            print("Could not send an email or text message")
            
        elif msg == "invalid":
            raise Exception("No valid method of sending a message was chosen!")

        else:
            # method of sending email changes depending on whether it is an email of text
            if self.sendToPhone is True:
                msgList = self.adjustTextMsg(msg)
                
                # send pure text first
                for currMsg in msgList:
                    sms = currMsg.strip() # need to convert message to string
                    # only send text bubble is there is actual text to send
                    if (not sms.isspace() and len(sms) > 0): 
                        self.SMTPClient.sendmail(msg["From"], msg["To"], sms)
                        # add microscopic delay to ensure that messages arrive in correct order
                        time.sleep(10/1000) # input is in seconds (convert to milliseconds)
                        print("Text bubble sent")
                    else:
                        print("Note sending empty message")

                # send attachments last
                for attachments in self.attachmentsList:
                    sms = attachments.as_string()
                    self.SMTPClient.sendmail(msg["From"], msg["To"], sms)
                self.attachmentsList = [] # reset list

            else:
                self.SMTPClient.send_message(msg)
            print("Successfully sent the email/text to {0} {1}".format(
                receiverContactInfo['firstName'], receiverContactInfo['lastName']))

    def composeMsg(self, receiverContactInfo, sendingText:bool=False, msgToSend:str=''):
        '''
            This function is responsible for composing the email message that get sent out
            - Args:
                * sendingText: a bool that tells program if it should be sending a text message
                * msgToSend: a string containing the desired message to be sent

            - Returns:
                * The sendable message 
                * 'invalid' if no type of message was chosen to be send
                * None if selected message could not be sent
        '''
        if self.commandLine:
            # determine if user wants to send an email message or phone text
            if 'n' not in input("Do you want to send a text message if possible (y/n): ").lower():
                msg = self.composeTextMsg(receiverContactInfo)
            else:
                if 'n' not in input("Do you want to send an email message? (y/n): ").lower():
                    msg = self.composeEmailMsg(receiverContactInfo)
                else:
                    msg = 'invalid' # signifies to caller that no message is being sent

        # not sending through command line
        else:
            if sendingText:
                msg = self.composeTextMsg(receiverContactInfo, msgToSend)
            else:
                msg = self.composeEmailMsg(receiverContactInfo, msgToSend)
            

        # check if user added an attachment (either link or path to file) in message
        if (msg != 'invalid' and msg != None):
            self.scanForAttachments()
            
            # check if text payload is empty besides newline (enter to submit)
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':                
                    if (part.get_payload().isspace()):
                        # if so, remove the text payload
                        part.set_payload(None)
        return msg


    def composeTextMsg(self, receiverContactInfo, msgToSend:str=''):
        '''
            @Args:
                - receiverContactInfo: a dictionary containing the following information 
                    {first name, last name, email, carrier, phone number}
                - msgToSend: a string containing the message to be sent (dont fill in if using command line)
        '''
        receiverCarrier = receiverContactInfo['carrier'].lower()        

        # Check if this email provider allows emails to be sent to phone numbers
        lowerCaseList = list(map(lambda x:x.lower(), self.emailProvidersInfo.keys()))
        # use index of lower case match to get actual value of key according to original mapped dict keys
        dictKeysMappedToList = list(map(lambda x:x, self.emailProvidersInfo.keys()))

        if receiverCarrier in lowerCaseList:
            indexInListOfCarrier = lowerCaseList.index(receiverCarrier)
            keyForDesiredCarrier = dictKeysMappedToList[indexInListOfCarrier]

            if 'SMS-Gateways' not in self.emailProvidersInfo[keyForDesiredCarrier]["smtpServer"].keys():
                print("Sending text messages to {0} {1} is not possible due to their cell provider".format(
                        receiverContactInfo['firstName'], receiverContactInfo['lastName']))

                # Since cant send a text message to the person, ask if user want to send email message instead
                if input("Do you want to send an email instead (y/n): ").lower() == 'y':
                    return self.composeEmailMsg()
                
                # If user cant send a text and wont send an email then just return
                else:
                    return None
            else:
                domainName = self.emailProvidersInfo[keyForDesiredCarrier]["smtpServer"]['SMS-Gateways']

        # Remove all non-numerical parts of phone number (should be contiguous 10 digit number)
        actualPhoneNum = ''.join(char for char in receiverContactInfo['phoneNumber'] if char.isdigit())
        
        textMsgAddress = "{0}@{1}".format(actualPhoneNum, domainName)
        print("Sending text message to {0}".format(textMsgAddress))
        
        # Get content to send in text message
        if self.commandLine:
            body = input("Please enter the message you would like to send (Use enter key to finish typing): \n")
        # not using command line
        else: 
            body = msgToSend
        # body += "\n" # have to add newline char at the end of the body


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

    def composeEmailMsg(self, receiverContactInfo, msgToSend:str=''):
        '''
            This function provides the user with a method of choosing which email format to send and entering the desired message.
            @Args:
                - receiverContactInfo: a dictionary containing the following information 
                    {first name, last name, email, carrier, phone number}
                - msgToSend: a string containing the message to be sent (dont fill in if using command line)
        '''
        if self.commandLine:
            # Get a list of all possible message types
            listOfMsgTypes = [types.replace('.txt', '') for types in os.listdir(self.messageTemplatesDir)]
            contents = ''
            
            typeOfMsg = 'default' 
            pathToMsgTemplate = os.path.join(self.messageTemplatesDir, 'default.txt')

            with open(pathToMsgTemplate) as readFile:
                contents = readFile.read()

            for msgType in listOfMsgTypes:
                pathToMsgTemplate = os.path.join(self.messageTemplatesDir, msgType + '.txt')
                with open(pathToMsgTemplate) as readFile:
                    msgContents = readFile.read()
                print("The {0} message type looks like: \n{1}".format(msgType, msgContents))
                if 'y' in input("Would you like to send this message type? (y/n): ").lower():
                    typeOfMsg = msgType   
                    contents = msgContents 
                    break


            # create the body of the email to send
            # read in the content of the text file to send as the body of the email

            # TODO create other elif statements for different cases
            if typeOfMsg == "testMsg":
                receiver = str(receiverContactInfo['firstName'])
                sendableMsg = self.readTemplate(pathToMsgTemplate).substitute(
                    receiverName=receiver, senderName=self.myEmailAddress) 

            elif typeOfMsg == 'inputContent':
                myInput = input("Input what you would like to send in the body of the email: ")
                sendableMsg = self.readTemplate(pathToMsgTemplate).substitute(content=myInput)
            
            # Default to default file 
            else:
                sendableMsg = contents

            # print("Sending message:\n{0}".format(sendableMsg))

        # not using command line
        else:
            sendableMsg = msgToSend
            
        # setup the Parameters of the message
        msg = MIMEMultipart() # create a message object
        msg['From'] = self.myEmailAddress
        msg['To'] = receiverContactInfo['email'] # send message as if it were a text
        msg['Subject'] = "Emailing Application"
        # add in the message body
        msg.attach(MIMEText(sendableMsg, 'plain'))
        return msg


    def readTemplate(self, pathToFile):
        with open(pathToFile, 'r+', encoding='utf-8') as templateFile:
            templateFileContent = templateFile.read()
        return Template(templateFileContent)

    def getReceiverContactInfo(self, myFirstName, myLastName):
        '''
            This function will search the existing database for entries with the input firstName and lastName.\n

            Returns:\n
                Dictionary of format: {first name, last name, email, carrier, phone number}
                The phone number return accepts common type of seperaters or none (ex: '-')             
        '''

        receiverContactInfoDict = {}
        email = ''
        phoneNumber = ''
        carrier = ''

        # Go through the list looking for name matches (case-insensitive)
        for lastName in self.contactList.keys():
            # print(lastName)
            for firstName in self.contactList[lastName].keys():
                # print(firstName)
                if firstName.lower() == myFirstName.lower() and lastName.lower() == myLastName.lower():
                    print("\nFound a match!\n")
                    contactFirstName = firstName
                    contactLastName = lastName
                    # stores contact information in the form {"email": "blah@gmail.com", "carrier":"version"}
                    receiverContactInfoDict = self.contactList[lastName][firstName]
                    email = receiverContactInfoDict['email']
                    phoneNumber = receiverContactInfoDict['phoneNumber']
                    carrier = receiverContactInfoDict['carrier']

        # if values were not initialized then no match was found
        if email == '' and phoneNumber == '' and carrier == '':
            raise Exception("Contact does not exist! \n\nAdd them to the contact \
                list by calling this program followed by 'addContact'")
        
        print("Based on the inputs of: \nfirst name = {0} \nlast name = {1}\n".format(myFirstName, myLastName))
        print("The contact found is:\n{0} {1}\nEmail Address: {2}\nCarrier: {3}\nPhone Number: {4}".format(
            contactFirstName, contactLastName, email, carrier, phoneNumber))

        dictToRtn = {
            'firstName' : contactFirstName,
            'lastName': contactLastName,
            'email': email,
            'carrier': carrier,
            'phoneNumber' : phoneNumber
        }

        return dictToRtn

    def connectToEmailServers(self):
        """
            \n@Brief: This function is responsible for connecting to the email server.
            \n@Param: hostAddress- contains information about host address of email server 
            \n@Param: purpose- str that is either "send" or "receive" which is needed to determine which protocol to use
            \n@Param: portNum- contains information about the port # of email server (defaults to 465)
            \n@Return:No returns, but this function does create a couple 'self' variables
        """

        # Get email login
        if self.useDefault == False and self.loginAlreadySet == False:
            # if false then make user use their own email username and password
            self.myEmailAddress = input("Enter your email address: ")
            self.password = getpass.getpass(prompt="Password for user {0}: ".format(self.myEmailAddress))
            self.loginAlreadySet = True # set to true so next time the user will not have to retype login info
        else:
            print("Using default gmail account created for this program to login to an email\n")
            # I created a dummy gmail account that this program can login to

        
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
            self.connectedToServers = True
            print("Successfully logged into email account!\n")
            
        except Exception as error:
            if '535' in str(error):
                # Sometimes smtp servers wont allow connection becuase the apps trying to connect are not secure enough
                # TODO make connection more secure
                print("\nCould not connect to email server because of error:\n{0}\n".format(error))
                print("Try changing your account settings to allow less secure apps to allow connection to be made.")
                linkToPage = "https://myaccount.google.com/lesssecureapps"
                print("Or try enabling two factor authorization and generating an app-password\n{0}".format(linkToPage))
                print("Quiting program, try connecting again with correct email/password, \
                    after making the changes, or trying a different email")
            else:
                print("\nEncountered error while trying to connect to email server: \n{0}".format(error))
            quit()

    def loadJson(self, pathToJson):
        with open(pathToJson, 'r+') as readFile:
            data = json.load(readFile)
        return data

    def connectSMTP(self, server, portNum):
        print("Connecting to SMTP email server")
        self.SMTPClient = smtplib.SMTP(host=server, port=int(portNum))
        self.SMTPClient.ehlo()
        self.SMTPClient.starttls(context=self.context)
        self.SMTPClient.ehlo()    

    def connectIMAP(self, server, portNum):    
        print("Connecting to IMAP email server")
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
            print("Email Address is: {0}".format(emailServiceProvider))
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
        '''
            This function is responsible for adding another contact to the contact list by processing the inputs
            Args:\n
                firstName: first name of the person being added
                lastName: last name of the person being added
                email: email of the person being added
                carrier: carrier of the person being added
                phoneNumber: phone number of the person being added
        '''
        
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

                print("Found user: {0} {1} with the following information: \
                    \nEmail: {2}\nPhone Number: {3}\nCell Carrier: {4}\n".format(
                    actualLastName, actualFirstName, user['email'], user['phoneNumber'], user['carrier']))
                update = input("Do you want to update their information (y/n): ")

                if (update == 'y'):
                    newContactList = self.updateContactInfo(firstName=actualFirstName, lastName=actualLastName, addingExternally=False)
       
        # If last name doesnt exist in contact list yet, then add it
        else:
            newContactList[lastName] = {}
            newContactList[lastName][firstName] = commonDataDict

        # Update existing variable used by rest of program so it constantly stays up to date
        self.contactList = newContactList
        print("The updated contacts list is:\n")
        pprint.pprint(self.contactList)

        # In either case, write updated version of contact list to the json file
        with open(self.pathToContactList, 'w+') as writeFile:
            json.dump(newContactList, writeFile, indent=4)

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

        updateFirstName = input("\nTheir first name is '{0}', would you like to change it (y/n): ".format(actualFirstName))
        updateLastName = input("Their last name is '{0}', would you like to change it (y/n): ".format(actualLastName))
        updateEmail = input("Their email is '{0}', would you like to change it (y/n): ".format(user['email']))
        updateCarrier = input("Their cell phone carrier is '{0}', would you like to change it (y/n): ".format(user['carrier']))
        updatephoneNumber = input("Their phone number is '{0}', would you like to change it (y/n): ".format(user['phoneNumber']))
        print('') # space the text out in terminal

        newFirstName = firstName
        newLastName = lastName
        commonDataDict['email'] = user['email']
        commonDataDict['carrier'] = user['carrier']
        commonDataDict['phoneNumber'] = user['phoneNumber']
        updatePhrase = "What would you like to change the <field> to: "
        if (updateFirstName == 'y'):
            newFirstName = input(updatePhrase.replace('<field>', 'first name'))
        if (updateLastName == 'y'):
            newLastName = input(updatePhrase.replace('<field>', 'last name'))
        if (updateEmail == 'y'):
            commonDataDict['email'] = input (updatePhrase.replace('<field>', 'email'))
        if (updateCarrier == 'y'):
            commonDataDict['carrier'] = input(updatePhrase.replace('<field>', 'cell carrier'))
        if (updatephoneNumber == 'y'):
            commonDataDict['phoneNumber'] = input(updatePhrase.replace('<field>', 'phone number'))
        
        if (len(updatedContactList[actualLastName]) == 1):
            del updatedContactList[actualLastName]
            updatedContactList[newLastName] = {}
            updatedContactList[newLastName][newFirstName] = commonDataDict
        else:
            if (updateLastName):
                # get a copy of everything past the last name
                updatedContactList[newLastName] = dict(updatedContactList[actualLastName])
                del updatedContactList[actualLastName]
                actualLastName = newLastName
            if (updateFirstName):
                updatedContactList[actualLastName][newFirstName] = dict(updatedContactList[actualLastName][actualFirstName])
                del updatedContactList[actualLastName][actualFirstName]
                actualFirstName = newFirstName
            if (updateEmail or updateCarrier or updatephoneNumber):
                updatedContactList[actualLastName][actualFirstName] = commonDataDict
        
        # handled by other function if internal
        if (addingExternally):
            # Update existing variable used by rest of program so it constantly stays up to date
            self.contactList = updatedContactList
            print("The updated contacts list is:\n")
            pprint.pprint(self.contactList)

            with open(self.pathToContactList, 'w+') as writeFile:
                json.dump(updatedContactList, writeFile, indent=4)

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
        emailAgent(displayContacts=False).addContact(
            firstName, lastName, myEmail, carrier, phoneNumber)

    def _waitForNewMessage(self, startedBySendingEmail:bool):
        """
            \n@Brief: This function halts the program until a new message is detected in the inbox
            \n@Param: startedBySendingEmail- bool that informs program if the first action taken was to send
        """
        # Ask if they want to wait for a reply (only if user didnt start off by sending an email)
        waitForMsg = ''
        if startedBySendingEmail == False:
            if self.commandLine:
                while 'y' not in waitForMsg:
                    waitForMsg = input("Do you want to wait for a new message (y/n): ")
            else: 
                raise Exception("IMPLEMENT NON-COMMAND LINE '_waitForNewMessage'")
        else:
            waitForMsg = 'y'

        if 'y' not in waitForMsg:
            return # quit function if dont want to wait

        # wait for new message
        else:
            keepCheckingInbox = True # allows function to look at emails to repeat

            startNumEmails = len(self.getEmailListIDs())
            numEmails = startNumEmails
            unreadEmailList = []
            
            self.webAppPrintWrapper("waiting for new message...\n")
            while startNumEmails - numEmails == 0:
                # Defaults to only look for unread emails
                unreadEmailList = self.getEmailListIDs()
                numEmails = len(unreadEmailList)
                # check intermittenly
                time.sleep(10) # in seconds
                print("{0} - No New Message".format(str(datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S"))))
            
            # if this point is reached, new email detected and can end function so program can continue!
            self.webAppPrintWrapper("{0} - New email message detected!".format(str(datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S"))))
            self.receiveEmail(onlyUnread=True, recursiveCall=True) # return to main receive function but have it stop early to not recur
            

    def getEmailListIDs(self, emailFilter:str=_unreadEmailFilter)->list():
        """
            \n@brief: Helper function that gets all the email ids (belonging to emailFilter)
            \n@Param: emailFilter(str): either 'ALL' or '(UNSEEN)' for only unread emails 
            \n@return: List of email ids matching the filter
        """
        # first check if connected to email servers, if not connect
        if not self.connectedToServers:
            self.connectToEmailServers()

        # verify correct input entered
        if emailFilter != emailAgent._unreadEmailFilter and emailFilter != emailAgent._allEmailFilter:
            print("WARNING UNKNOWN EMAIL FILTER ENTERED- may result in undefined behavior")

        # opens folder/label you want to read from
        self.IMAPClient.select('INBOX')
        # self.webAppPrintWrapper("Successfully Opened Inbox")
                    
        # get all the emails and their id #'s that match the filter
        rtnCode, data = self.IMAPClient.search(None, emailFilter) 
        if rtnCode != "OK":
            self.webAppPrintWrapper("Bad return code from inbox!")

        numEmails = len(data[0].decode()) 
        msgIds = data[0].decode() # convert byte to string

        # convert to descending ordered list (msgIds is a str with the msgIds seperated by spaces)
        idList = list(map(lambda x:int(x), list(msgIds.split()))) 
        idList.sort(reverse = True) # sort() performs operation on the same variable
        # self.webAppPrintWrapper("idList: {0}".format(idList))
        
        return idList

    def fetchEmail(self, emailIdNum:int, leaveUnread:bool=False)->bytearray():
        """
            \n@Brief: Helper function that fetches and returns emails of the specified id number
            \n@Param: emailIdNum- the id number of the email to fetch
            \n@Param: leaveUnread- Dont open the email (leave as unread)
            \n@Return: A raw email byte string that can be converted into a Message object (need to use email.message_from_bytes())
            \n@Note: call 'processRawEmail(rawEmail, emailIdNum)' to convert to usable form

        """
        if leaveUnread:     openCode = '(BODY.PEEK[])'
        else:               openCode = '(RFC822)'
        rtnCode, emailData = self.IMAPClient.fetch(str(emailIdNum).encode(), openCode) 
        if (rtnCode != "OK"):
            self.webAppPrintWrapper("Bad email return code received!!")
            
        rawEmail = emailData[0][1]
        return rawEmail



    def getEmailListWithContent(self, emailFilter:str=_unreadEmailFilter,  leaveUnread=False)->list():
        """
            \n@brief: Helper function that fetches the data for all emails (matching the filter) and returns the list
            \n@Param: emailFilter(str): either 'ALL' or '(UNSEEN)' for only unread emails 
            \n@Param: leaveUnread- Dont open the email (leave as unread)
            \n@return: List of dictionaries: {To, From, DateTime, Subject, Body, idNum, unread}} 
            \n@Note: call 'printProcessedEmailDict()' on the returned list to print the emails and their ids nicely
        """
        # Get both types of lists so that if reading all emails, can mark ones as unread
        idListUnread = self.getEmailListIDs(emailFilter=emailAgent._unreadEmailFilter)
        idListALL = self.getEmailListIDs(emailFilter=emailAgent._allEmailFilter)
        if emailFilter == emailAgent._unreadEmailFilter:
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
            \n@Note: call 'printProcessedEmailDict()' on the returned dict to print the email nicely
        """
        emailList = self.getEmailListWithContent(emailFilter=emailAgent._allEmailFilter)
        return emailList

    def getUnreadEmails(self)->list():
        """
            \n@brief: Fetches all unread emails and lists them by id number
            \n@return: List of dictionaries: {To, From, DateTime, Subject, Body, idNum, unread}} 
            \n@Note: call 'printProcessedEmailDict()' on the returned dict to print the email nicely
        """
        emailList = self.getEmailListWithContent(emailFilter=_unreadEmailFilter)
        return emailList

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

    def _printEmailDescriptor(self, emailMsg:dict):
        """
            \n@Brief: Internal function which helps print useful messages about an email for a user to access
            \n@Param: emailMsg(dict)- a dictionary of the email with format {To, From, DateTime, Subject, Body, idNum, unread}
            \n@Return: None (prints stuff)
        """
        # if unread, print it
        if emailMsg["unread"] == True:  unreadText = "(unread)"
        else:                           unreadText = ""

        # get terminal size to make message appear on one line (subtract to make comfortable)
        columns, rows = shutil.get_terminal_size(fallback=(80, 24))
        spaceCushion = len(emailMsg["DateTime"]) + len(" - #) ") + len(unreadText) + 5 # last 5 comes from email id reaching up to 99999 (might need to make more) 
        if (emailMsg['Subject'].strip().isspace() or emailMsg['Subject'] == '' or emailMsg['Subject'] == None):
            # there is no subject, show part of message instead
            print("{0} - #{1}) {2}...{3}".format(emailMsg['DateTime'] , emailMsg['idNum'], emailMsg['Body'][:columns-spaceCushion], unreadText))

        # there is an actual subject in the message
        else:
            overflow = columns - len(emailMsg["Subject"]) - spaceCushion
            moreToMsg = "" # leave empty, if not enough space, add them
            if overflow < 0: 
                emailMsg = emailMsg[:overflow]
                moreToMsg = "..."
            print("{0} - #{1}) {2}{3}{4}".format(emailMsg['DateTime'] , emailMsg['idNum'], emailMsg['Subject'], moreToMsg, unreadText))


    def getEmailsGradually(self, emailFilter:str=_unreadEmailFilter, printDescriptors:bool=True, leaveUnread=False)->(list(), dict()):
        """
            \n@Brief- Takes email dict and prints out email nicely for user
            \n@Param: emailFilter(str): either 'ALL' or '(UNSEEN)' for only unread emails 
            \n@Param: printDescriptors(bool)- if true, print "<email id>) <email subject>" for all emails
            \n@Param: leaveUnread- Dont open the email (leave as unread)
            \n@Return- Touple(emailMsgLlist, idList) 
            \n@emailMsgLlist: list of dicts with email message data. Format [{To, From, DateTime, Subject, Body, idNum, unread}]
            \n@idDict: dict of email ids mapped to indexes of emailMsgLlist in format {'<email id>', '<list index>'}
        """
        # Get both types of lists so that if reading all emails, can mark ones as unread
        idListUnread = self.getEmailListIDs(emailFilter=emailAgent._unreadEmailFilter)
        idListALL = self.getEmailListIDs(emailFilter=emailAgent._allEmailFilter)
        if emailFilter == emailAgent._unreadEmailFilter:
            idList = idListUnread
        else:
            idList = idListALL

        print("ctrl-c to stop fetching...")
        emailList = []
        idDict = {}
        try:
            for idNum in idList:
                rawEmail = self.fetchEmail(idNum, leaveUnread=leaveUnread)
                emailUnreadBool = idNum in idListUnread 
                emailMsg = self.processRawEmail(rawEmail, idNum, unread=emailUnreadBool)
                idDict[idNum] = len(emailList) # right before append (list size at first =0, and first entry in 0)
                emailList.append(emailMsg)
                if printDescriptors:
                    self._printEmailDescriptor(emailMsg)
        except KeyboardInterrupt:
            print("Stopped fetching")
        return (emailList, idDict)

    def _openEmail(self, idDict:dict, emailList:list)->(str(), dict()):
        """
            \n@Brief: Helper function that determines which email the user wants to open, printing and returning it
            \n@Param: idDict- dict of email ids mapped to indexes of emailList in format {'<email id>', '<list index>'}
            \n@Param: emailList- list of emailInfo dicts with format [{To, From, DateTime, Subject, Body, idNum, unread}]
            \n@Return(touple): (printedStr, emailDict)
            \n@Return: printedStr- string of what is printed to the terminal
            \n@Return: emailDict- email info dict of format {To, From, DateTime, Subject, Body, idNum, unread}
            \n@Note: If no emails in list, return touple of ("", {})
        """
        idSelected = -1
        if self.commandLine:
            # making sure there is an email to open
            if len(idDict) == 0:
                # return empty values for callers if nothing found
                printedStr = "No Emails Found!"
                emailDict = {}
                print(printedStr)
                return (printedStr, emailDict)

            # error checking for valid email id
            while not idSelected in idDict.keys():
                idSelected = input("Enter email id to open: ").replace('\n', '').strip()
                if idSelected.isspace() or not idSelected.isdigit(): idSelected = -1
                idSelected = int(idSelected)
        else: 
            raise Exception("IMPLEMENT NON-COMMAND LINE '_openEmail'")

        # open selected email
        emailListIndex = idDict[idSelected]
        emailDict = emailList[emailListIndex]
        printedStr = self.printProcessedEmailDict(emailDict)
        return (printedStr, emailDict)

    def _reply(self, startedBySendingEmail:bool, emailMsgDict:dict):
        """
            \n@Brief: Helper function that determines if user wants to reply to email
            \n@Param: startedBySendingEmail- bool that informs program if the first action taken was to send
            \n@Param: emailMsgDict- dict of info about email of format {To, From, DateTime, Subject, Body, idNum, unread}
        """
        # only ask this question if user didnt start off by sending emails
        if startedBySendingEmail == False: 
            if self.commandLine:
                replyBool = input("Do you want to reply to this email (y/n): ")
            else:
                raise Exception("IMPLEMENT NON-COMMAND LINE '_reply'")
        else:
            replyBool = 'n'

        if 'y' in replyBool:
            # send response to the information of "from" from the received email
            contactInfo = self.numberToContact(emailMsgDict["From"])

            # if contactInfo is None, then sender of email not in contact list. Resort to other methods
            if contactInfo == None:
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

    def receiveEmail(self, startedBySendingEmail=False, onlyUnread:bool=True, recursiveCall:bool=False):
        """
            \n@Brief: High level api function which allows user to receive an email
            \n@Param: startedBySendingEmail- True if started off by sending email and want to wait for users reponse
            \n@Param: onlyUnread- When set to true, no command line input needed to tell which messages to read
            \n@Param: recursiveCall- bool used to prevent infinite recursion when waiting for new email
        """
        # first check if connected to email servers, if not connect
        if not self.connectedToServers:
            self.connectToEmailServers()
            
        # input error checking                
        if onlyUnread:
            emailList, idDict = self.getEmailsGradually(emailFilter=emailAgent._unreadEmailFilter)
        elif not onlyUnread: 
            emailList, idDict = self.getEmailsGradually(emailFilter=emailAgent._allEmailFilter)

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
            \n\t"unread": bool
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

        # Get date and time of email
        dataTuple = email.utils.parsedate_tz(emailMsg['Date'])
        if dataTuple:
            local_date = datetime.datetime.fromtimestamp(
                email.utils.mktime_tz(dataTuple))
            dateTime = local_date.strftime("%a, %d %b %Y %H:%M:%S")

        emailMsgDict = {
            "To":           emailMsg['To'],
            "From":         emailMsg['From'],
            "DateTime":     dateTime,
            "Subject":      emailMsg['Subject'],
            "Body":         body,
            "idNum":        idNum,
            "unread":       unread
        }

        return emailMsgDict

    def printProcessedEmailDict(self, emailDict:dict)->str():
        """
            \n@brief: Convience function which passes preformatted dictionary to printProcessedEmail 
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
            "unread": bool()
        }
        if (emailDict.keys() != sampleDict.keys()):
            raise Exception("Incorrectly Passed Dictionary, needs this format: {0}".format(sampleDict))
        
        return self.printProcessedEmail(emailDict["To"], emailDict["From"], emailDict["DateTime"], emailDict["Subject"], emailDict["Body"])

    def printProcessedEmail(self, To:str, From:str, DateTime:str, Subject:str, Body:str)->str():
        """
            \n@brief: Prints the processed email
            \n@Param: To- Who the is receiving the message (usually the user using this code)
            \n@Param: From- Who the message is from 
            \n@Param: dateTime- Timestamp of when the message was sent
            \n@Param: subject- The subject
            \n@Param: body- The actual message
            \n@Return: string of what's printed to the terminal
        """
        # email delineator (get column size)
        columns, rows = shutil.get_terminal_size(fallback=(80, 24))
        delineator = columns - 2 # have to account for '<' and '>' chars on either end 
        deliniatorStr = "\n<{0}>\n".format('-'*delineator)
        
        strToPrint = ""
        strToPrint += deliniatorStr
        strToPrint += """Email:\n
        To: {0}
        From: {1}
        DateTime: {2}
        Subject: {3}

        Body: {4}
        """.format(To, From, DateTime, Subject, Body)
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
            regexPaths = r"([/|~/][^.]+..[^\s]+)" # <~/ or /><words>.<extension><space>
        else:
            raise Exception( + " is currently unsupported")
        attachmentFilePaths = re.findall(regexPaths, self.textMsgToSend)
        attachmentList.extend(attachmentFilePaths)
        
        # check for urls
        regexUrl = r"(http[s]?://[^\s]+)" # <http(s)://<until space or newline-not url valid>
        attachmentUrls = re.findall(regexUrl, self.textMsgToSend)
        # make sure links arent links to regular webpages
        for url in attachmentUrls:
            attachmentList.append(url)

        # add attachments that were found9-
        print("Checking if the following items are valid:\n{0}".format(attachmentList))
        for toAttach in attachmentList:
            self.addAttachment(toAttach)
        print("Done checking if attachments are valid")

    def addAttachment(self, toAttach:str):
        '''
            @breif: adds new attachment to self.attachmentsList for future sending
            @Param: toAttach: a string that can either be a path to a local file or a url 
            
        '''
        # check if valid file path
        isValidPath = os.path.exists(toAttach)
        if (isValidPath):
            # read the attachment and add it
            attachmentName = os.path.basename(toAttach)
            with open(toAttach, 'rb') as attachment:
                attachable = MIMEApplication(attachment.read(), Name=attachmentName)
            
            attachable['Content-Disposition'] = 'attachment; filename={0}'.format(attachmentName)
            self.attachmentsList.append(attachable)

        # check if valid url
        isValidUrl = self.isURLValid(toAttach)
        if (isValidUrl):
            # use an agent or else browser will block it
            request = urllib.request.Request(toAttach, headers={'User-Agent': 'Mozilla/5.0'})
            attachable = MIMEApplication(urllib.request.urlopen(request).read(), Name="URL Link")
            attachable['Content-Disposition'] = 'attachment; filename={0}'.format("URL Link")
            self.attachmentsList.append(attachable)
           
        if (isValidPath or isValidUrl):
            # remove text from payload that was attachment
            self.textMsgToSend = self.textMsgToSend.replace(toAttach, '', 1)
        else:
            print("NOT A VALID PATH OR URL!")

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
            if (returnCode != 200): return False # 200 return code means success!
            
            # check if file type is media (pic/video/gif)
            # full list from fleep.supported_types: 
            #  ['3d-image', 'archive', 'audio', 'database', 'document', 'executable', 'font',
            #     'raster-image', 'raw-image', 'system', 'vector-image', 'video']
            validTypes = ['3d-image', 'audio', 'raster-image', 'raw-image', 'vector-image', 'video']
            urlContent = urllib.request.urlopen(request).read() # return is bytes
            info = fleep.get(urlContent)
            if info.type[0] in validTypes: 
                return True
            else: 
                print("Type {0} is not accepted".format(info.type[0]))
                return False

        except:
            print("NOT A VALID URL")
            return False
    
    # this functions purpose is to take a string argument (toPrint) 
    # and both print it to terminal and store it so it can be accessed by "getPrintedString()"
    def webAppPrintWrapper(self, toPrint:str): 
        print(toPrint)
        self.printedString += toPrint + "\n" # have to add newline bc normally automatically there

    def getPrintedString(self):
        tempStr = self.printedString
        self.printedString = ""
        return tempStr

    # prints the contact list and returns the printed string nicely printed
    def printContactListPretty(self, printToTerminal=True):
        self.contactList = self.getContactList()
        formatedContactList = pprint.pformat(self.contactList)
        if printToTerminal:
           print(formatedContactList)
        return formatedContactList

    def logoutEmail(self):
        '''
            This function is responsible for having the email server close connections with the server.
            Need to make it a function due to the fact that logging out requires different code depening on the type of server 
        '''
        # depending on situation, one of them might not have logged in in the first place
        try:
            self.SMTPClient.quit()
        except Exception as e:
            pass

        try:
            self.IMAPClient.logout()
        except Exception as e:
            pass
        self.connectedToServers = False

    def start(self):
        '''
            Wrapper around run() function that jump starts the email process
        '''
        run()
        

def run():
    argLength = len(sys.argv)
    # the order of arguments is: 
    # 0-file name, 1-first name, 2-last name, 3-skip login(optional- only activates if anything is typed)
    # "add contact" will help user to add a contact to the contact list
    # "update contact" will help user update a contact's info


    # use this phrase to easily add more contacts to the contact list
    if 'addContact' in sys.argv:
        emailer = emailAgent(displayContacts=True, commandLine=True)
        emailer.simpleAddContact()
        sys.exit()
    
    if 'updateContact' in sys.argv:
        emailer = emailAgent(displayContacts=True, commandLine=True)
        emailer.updateContactInfo()
        sys.exit()

    # Create a class obj for this file
    emailer = emailAgent(displayContacts=False, commandLine=True)

    if 'default' in ''.join(sys.argv):
        emailer.setDefaultState(True)
    else:
        emailer.setDefaultState(False)

    # determine what the user wants to use the emailing agent for
    serviceType = input("\nTo send an email type 'send'. To check your inbox type 'get': ").lower()

    if "send" in serviceType:

        # First check that enough arguments were provided (if not do it manually)
        if argLength < 3: 
            print("""\
                \nInvalid number of arguments entered! \
                \nProvide first and last name seperated by spaces when running this script!""")

            emailer.webAppPrintWrapper("\nThe existing contact list includes:")
            emailer.printContactListPretty()

            addContact = input("Do you want to add a new contact to this list(y/n): ")
            if addContact == 'y' or addContact == 'yes': emailer.simpleAddContact()
            
            sendMsg = input("Do you want to send a message to one of these contacts (y/n): ")
            # error check for invalid input
            if sendMsg == 'n': sys.exit(0)
            else:
                fullName = list()
                while len(fullName) < 2:
                    fullName = input("Enter their first name followed by their last name: ").split(' ')
                
                firstName = fullName[0]
                lastName = fullName[1]
                
        else:
            # Get arguments from when script is called
            firstName = sys.argv[1]
            lastName = sys.argv[2]
            # receiverContactInfo contains firstName, lastName, email, carrier, phone number

        # get contact info regardless of method to reach this point
        receiverContactInfo = emailer.getReceiverContactInfo(firstName, lastName)

        # argLength- if all arguments given when calling script
        if argLength == 4:
            # if there is a third argument, then use default email account (dont need to login)
            emailer.setDefaultState(True)

        emailer.sendMsg(receiverContactInfo)
    
        waitForReply = input("Do you want to wait for a reply (y/n): ")
        if 'n' not in waitForReply:
            emailer.receiveEmail(startedBySendingEmail=True, onlyUnread=True)

    elif "get" in serviceType:
        # Entering something in the second argument signifies that you want to use the default login
        filterInput = ""
        while filterInput != "n" and filterInput != "y":
            filterInput = input("Do you want to see only unopened emails (y/n): ")
            if filterInput == "y": emailer.receiveEmail(onlyUnread=True)
            elif filterInput == "n": emailer.receiveEmail(onlyUnread=False)
            else: print("Invalid Arg Entered!")

        
            
    else:
        print("Please Enter a Valid Option!")

    # logout
    emailer.logoutEmail()

    print("Closing Program")
    

if __name__ == "__main__":
    run() # starts the code

