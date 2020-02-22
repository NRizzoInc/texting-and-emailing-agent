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

path_to_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path_to_this_dir)


class emailAgent():
    def __init__(self, display_contacts=True, commandLine=False):
        '''
            This class is responsible for sending emails 
        '''
        self.messageTemplates_dir = os.path.join(path_to_this_dir, "/templates/messageTemplates")
        self.path_to_contactList = os.path.join(path_to_this_dir, "contacts.json")


        # Open the contact list file (create new file if it does not exist)
        if not os.path.exists(self.path_to_contactList):
            with open(self.path_to_contactList, 'w+') as writeFile:
                json.dump({}, writeFile) #write empty dictionary to file (creates the file)
        self.contactList = self.load_json(self.path_to_contactList)

        # information to login
        self.email_providers_info = self.load_json(os.path.join(path_to_this_dir, 'email_providers_info.json'))
        self.send_to_phone = False
        self.context = ssl.SSLContext(ssl.PROTOCOL_SSLv23) 
        self.mode = None # usually set to 'SMTP' or 'IMAP'
        self.pastSMTPServerAddress = None
        self.pastIMAPServerAddress = None
        self.pastSMTPPort = None
        self.pastIMAPPort = None

        # these are the credentials to login to a throwaway gmail account 
        # with lower security that I set up for this program
        self.my_email_address = "codinggenius9@gmail.com"
        self.password = "codingisfun1"
        # will be set to true if non-default account is used and login entered
        # allows user to not hav eto tpe login multiple times
        self.loginAlreadySet = False 
        # boolean that when set to True means the program will login
        # to a known email account wihtout extra inputs needed
        self.use_default = False 

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
        if display_contacts is True:    
            self.webAppPrintWrapper("The current contact list is:\n")
            printableContactList = pprint.pformat(self.contactList)
            self.webAppPrintWrapper(printableContactList)

    # returns the contact list as it is currently in the contact list file
    def getContactList(self):
        return self.load_json(self.path_to_contactList)

    def sendMsg(self, receiver_contact_info, sendMethod:str='', msgToSend:str=''):
        '''
            Calls all other functions necessary to send an a message (either through text or email)

            Args:
                -receiver_contact_info: a dictionary about the receiver of format:
                        last_name: {
                            first_name: {
                                "email": "",
                                "phoneNumber": "",
                                "carrier": ""
                            }
                        },
                - sendMethod: a string that should either be 'email' or 'text'
                - msgToSend: a string that contains the message that is desired to be sent
        '''            

        # first check if valid "sendMethod" is received
        if sendMethod == '': pass
        elif sendMethod == 'email': sendTextBool = False
        elif sendMethod == 'text': sendTextBool = True
        else: raise Exception("Invalid sendMethod param passed to function!")

        email_service_provider_info = self.get_email_info("send")['smtp_server']

        self.connect_to_email_server("send", host_address=email_service_provider_info['host_address'],
            port_num=email_service_provider_info['port_num'])

        if self.commandLine:
            msg = self.compose_msg(email_service_provider_info, receiver_contact_info, msgToSend=msgToSend)
        else:
            msg = self.compose_msg(email_service_provider_info, receiver_contact_info, sendingText=sendTextBool, msgToSend=msgToSend)
        
        # send the message via the server set up earlier.
        if msg == None: # will only be None if can't send email or text message
            print("Could not send an email or text message")
            
        elif msg == "invalid":
            raise Exception("No valid method of sending a message was chosen!")

        else:
            # method of sending email changes depending on whether it is an email of text
            if self.send_to_phone is True:
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
                    self.email_server.sendmail(msg["From"], msg["To"], sms)
                self.attachmentsList = [] # reset list

            else:
                self.email_server.send_message(msg)
            print("Successfully sent the email/text to {0} {1}".format(
                receiver_contact_info['first_name'], receiver_contact_info['last_name']))

    def compose_msg(self, email_service_provider_info, receiver_contact_info, sendingText:bool=False, msgToSend:str=''):
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
                msg = self.compose_text_msg(receiver_contact_info)
            else:
                if 'n' not in input("Do you want to send an email message? (y/n): ").lower():
                    msg = self.compose_email_msg(receiver_contact_info)
                else:
                    msg = 'invalid' # signifies to caller that no message is being sent

        # not sending through command line
        else:
            if sendingText:
                msg = self.compose_text_msg(receiver_contact_info, msgToSend)
            else:
                msg = self.compose_email_msg(receiver_contact_info, msgToSend)
            

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


    def compose_text_msg(self, receiver_contact_info, msgToSend:str=''):
        '''
            @Args:
                - receiver_contact_info: a dictionary containing the following information 
                    {first name, last name, email, carrier, phone number}
                - msgToSend: a string containing the message to be sent (dont fill in if using command line)
        '''
        receiver_carrier = receiver_contact_info['carrier'].lower()        

        # Check if this email provider allows emails to be sent to phone numbers
        lower_case_list = list(map(lambda x:x.lower(), self.email_providers_info.keys()))
        # use index of lower case match to get actual value of key according to original mapped dict keys
        dict_keys_mapped_to_list = list(map(lambda x:x, self.email_providers_info.keys()))

        if receiver_carrier in lower_case_list:
            index_in_list_of_carrier = lower_case_list.index(receiver_carrier)
            key_for_desired_carrier = dict_keys_mapped_to_list[index_in_list_of_carrier]

            if 'SMS-Gateways' not in self.email_providers_info[key_for_desired_carrier]["smtp_server"].keys():
                print("Sending text messages to {0} {1} is not possible due to their cell provider".format(
                        receiver_contact_info['first_name'], receiver_contact_info['last_name']))

                # Since cant send a text message to the person, ask if user want to send email message instead
                if input("Do you want to send an email instead (y/n): ").lower() == 'y':
                    return self.compose_email_msg()
                
                # If user cant send a text and wont send an email then just return
                else:
                    return None
            else:
                domain_name = self.email_providers_info[key_for_desired_carrier]["smtp_server"]['SMS-Gateways']

        # Remove all non-numerical parts of phone number (should be contiguous 10 digit number)
        actual_phoneNumber = ''.join(char for char in receiver_contact_info['phoneNumber'] if char.isdigit())
        
        text_msg_address = "{0}@{1}".format(actual_phoneNumber, domain_name)
        print("Sending text message to {0}".format(text_msg_address))
        
        # Get content to send in text message
        if self.commandLine:
            body = input("Please enter the message you would like to send (Use enter key to finish typing): \n")
        # not using command line
        else: 
            body = msgToSend
        # body += "\n" # have to add newline char at the end of the body


        # setup the parameters of the message
        msg = MIMEMultipart() # create a message object with the body
        msg['From'] = self.my_email_address
        msg['To'] = text_msg_address
        msg['Subject'] = "" # keep newline
        self.textMsgToSend = body # dont add body yet bc text message
        
        self.send_to_phone = True

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

    def compose_email_msg(self, receiver_contact_info, msgToSend:str=''):
        '''
            This function provides the user with a method of choosing which email format to send and entering the desired message.
            @Args:
                - receiver_contact_info: a dictionary containing the following information 
                    {first name, last name, email, carrier, phone number}
                - msgToSend: a string containing the message to be sent (dont fill in if using command line)
        '''
        if self.commandLine:
            # Get a list of all possible message types
            list_of_msg_types = [types.replace('.txt', '') for types in os.listdir(self.messageTemplates_dir)]
            contents = ''
            
            type_of_msg = 'default' 
            path_to_msg_template = os.path.join(self.messageTemplates_dir, 'default.txt')

            with open(path_to_msg_template) as read_file:
                contents = read_file.read()

            for msg_type in list_of_msg_types:
                path_to_msg_template = os.path.join(self.messageTemplates_dir, msg_type + '.txt')
                with open(path_to_msg_template) as read_file:
                    msg_contents = read_file.read()
                print("The {0} message type looks like: \n{1}".format(msg_type, msg_contents))
                if 'y' in input("Would you like to send this message type? (y/n): ").lower():
                    type_of_msg = msg_type   
                    contents = msg_contents 
                    break


            # create the body of the email to send
            # read in the content of the text file to send as the body of the email

            # TODO create other elif statements for different cases
            if type_of_msg == "test_msg":
                receiver = str(receiver_contact_info['first_name'])
                sendable_msg = self.read_template(path_to_msg_template).substitute(
                    receiver_name=receiver, sender_name=self.my_email_address) 

            elif type_of_msg == 'input_content':
                my_input = input("Input what you would like to send in the body of the email: ")
                sendable_msg = self.read_template(path_to_msg_template).substitute(content=my_input)
            
            # Default to default file 
            else:
                sendable_msg = contents

            # print("Sending message:\n{0}".format(sendable_msg))

        # not using command line
        else:
            sendable_msg = msgToSend
            
        # setup the parameters of the message
        msg = MIMEMultipart() # create a message object
        msg['From'] = self.my_email_address
        msg['To'] = receiver_contact_info['email'] # send message as if it were a text
        msg['Subject'] = "Emailing Application"
        # add in the message body
        msg.attach(MIMEText(sendable_msg, 'plain'))
        return msg


    def read_template(self, path_to_file):
        with open(path_to_file, 'r+', encoding='utf-8') as template_file:
            template_file_content = template_file.read()
        return Template(template_file_content)

    def get_receiver_contact_info(self, my_first_name, my_last_name):
        '''
            This function will search the existing database for entries with the input first_name and last_name.\n

            Returns:\n
                Dictionary of format: {first name, last name, email, carrier, phone number}
                The phone number return accepts common type of seperaters or none (ex: '-')             
        '''

        receiver_contact_info_dict = {}
        email = ''
        phoneNumber = ''
        carrier = ''

        # Go through the list looking for name matches (case-insensitive)
        for last_name in self.contactList.keys():
            # print(last_name)
            for first_name in self.contactList[last_name].keys():
                # print(first_name)
                if first_name.lower() == my_first_name.lower() and last_name.lower() == my_last_name.lower():
                    print("\nFound a match!\n")
                    contact_first_name = first_name
                    contact_last_name = last_name
                    # stores contact information in the form {"email": "blah@gmail.com", "carrier":"version"}
                    receiver_contact_info_dict = self.contactList[last_name][first_name]
                    email = receiver_contact_info_dict['email']
                    phoneNumber = receiver_contact_info_dict['phoneNumber']
                    carrier = receiver_contact_info_dict['carrier']

        # if values were not initialized then no match was found
        if email == '' and phoneNumber == '' and carrier == '':
            raise Exception("Contact does not exist! \n\nAdd them to the contact \
                list by calling this program followed by 'add_contacts'")
        
        print("Based on the inputs of: \nfirst name = {0} \nlast name = {1}\n".format(my_first_name, my_last_name))
        print("The contact found is:\n{0} {1}\nEmail Address: {2}\nCarrier: {3}\nPhone Number: {4}".format(
            contact_first_name, contact_last_name, email, carrier, phoneNumber))

        dict_to_return = {
            'first_name' : contact_first_name,
            'last_name': contact_last_name,
            'email': email,
            'carrier': carrier,
            'phoneNumber' : phoneNumber
        }

        return dict_to_return

    def connect_to_email_server(self, purpose:str, host_address=None, port_num=465):
        '''
            This function is responsible for connecting to the email server.
            Args:
                - host_address: contains information about host address of email server 
                - purpose: A str that is either "send" or "receive" which is needed to determine which protocol to use
                - port_num: contains information about the port # of email server (defaults to 465)
            Return:
                - No returns, but this function does create a couple 'self' variables (self.email_server)
        '''

        # Get email login
        if self.use_default is False and self.loginAlreadySet == False:
            # if false then make user use their own email username and password
            self.my_email_address = input("Enter your email address: ")
            self.password = getpass.getpass(prompt="Password for user {0}: ".format(self.my_email_address))
            self.loginAlreadySet = True # set to true so next time the user will not have to retype login info
        else:
            print("Using default gmail account created for this program to login to an email\n")
            # I created a dummy gmail account that this program can login to

        # starts off set to None
        if self.pastIMAPServerAddress == None and purpose == 'receive':
            server = host_address
            self.pastIMAPServerAddress = server
            self.pastIMAPPort = port_num

        elif self.pastSMTPServerAddress == None and purpose == 'send':
            server = host_address
            self.pastSMTPServerAddress = server
            self.pastSMTPPort = port_num
        
        # cases when trying to relogin
        elif self.pastIMAPServerAddress != None and purpose == 'receive':
            server = self.pastIMAPServerAddress

        elif self.pastSMTPServerAddress != None and purpose == 'send':
            server = self.pastSMTPServerAddress

        else:
            raise Exception("Unhandled Case when getting server address in 'connect_to_email_server()'")
        
        if purpose == "send":
            my_port_num = 587
        elif purpose == "receive":
            my_port_num = 993
        else:
            raise Exception("Unhandled Case when getting port number in 'connect_to_email_server()'")


        # Establish connection to email server using self.my_email_address and password given by user
        # Have to choose correct protocol for what the program is trying to do(IMAP-receive, SMTP-send)        
        if purpose == "send":
            self.connectSMTP(server, my_port_num)
        
        elif purpose == "receive":
            self.connectIMAP(server, my_port_num)


        # Try to login to email server, if it fails then catch exception
        try:
            self.email_server.login(self.my_email_address, self.password)
            print("Successfully logged into email account!\n")
            
        except Exception as error:
            if '535' in str(error):
                # Sometimes smtp servers wont allow connection becuase the apps trying to connect are not secure enough
                # TODO make connection more secure
                print("\nCould not connect to email server because of error:\n{0}\n".format(error))
                print("Try changing your account settings to allow less secure apps to allow connection to be made.")
                link_to_page = "https://myaccount.google.com/lesssecureapps"
                print("Or try enabling two factor authorization and generating an app-password\n{0}".format(link_to_page))
                print("Quiting program, try connecting again with correct email/password, \
                    after making the changes, or trying a different email")
            else:
                print("Encountered error while trying to connect to email server: \n{0}".format(error))
            quit()

    def load_json(self, path_to_json=None):
        if path_to_json == None:
            path_to_json = self.path_to_contactList

        with open(path_to_json, 'r+') as read_file:
            data = json.load(read_file)
        return data

    def connectSMTP(self, server, portNum):
        print("Connecting to SMTP email server")

        # if email_server is already logged to either version, log it out
        if self.loginAlreadySet != None:
            self.logoutEmail()

        self.mode = "SMTP"
        self.email_server = smtplib.SMTP(host=server, port=int(portNum))
        self.email_server.ehlo()
        self.email_server.starttls(context=self.context)
        self.email_server.ehlo()    

    def connectIMAP(self, server, portNum):    
        print("Connecting to IMAP email server")

        # if email_server is already logged to either version, log it out
        if self.loginAlreadySet != None:
            self.logoutEmail()

        self.mode = "IMAP"
        self.email_server = imaplib.IMAP4_SSL(host=server, port=int(portNum), ssl_context=self.context)

    def get_email_info(self, purpose:str):
        '''
            This function returns a dictionary containing information 
            about a host address and port number of an email company.

            Args:
                -purpose: (string) Either "send" or "receive"
            Return:
                -email_service_provider_info: (Dict) Contains info about the email company necessary for logging in.
                    I.E.: {"host_address": "smtp.gmail.com", "port_num": "587"}
        '''
        # Based on input about which email service provider the user wants to login to determine info for server

        # concert the dictionary to all lower case to make searching easier
        lower_case_list = list(map(lambda x:x.lower(), self.email_providers_info.keys()))
        dict_keys_mapped_to_list = list(map(lambda x:x, self.email_providers_info.keys()))

        # narrow down content of list based on if it can fit the "purpose" (send/receive)
        # if "host_address" is empty then not valid for this purpose
        if purpose == "send":
            possible_providers = [i for i in self.email_providers_info.keys() if 
                    len(self.email_providers_info[i]["smtp_server"]["host_address"]) != 0]   
        elif purpose == "receive":
            possible_providers = [i for i in self.email_providers_info.keys() if 
                    len(self.email_providers_info[i]["imap_server"]["host_address"]) != 0]  

        else:
            # error check myself incase I forget about this in the future
            raise Exception("Either use a valid 'purpose' or add another option")

        found_valid_email_provider = False
        email_service_provider_info = {}

        print("default state: {0}\nLogin already set{1}".format(self.use_default, self.loginAlreadySet))

        while found_valid_email_provider is False and self.use_default is False:
            print("The available list of providers you can login to is: \n{0} \
                  \nSelect 'Default' if you dont want to skip logging in.".format(list(possible_providers)))
            email_service_provider = input("\nWhich email service provider do you want to login to: ")

            # see if email service provider exists in the list (case-insensitive)
            # -use lambda function to turn list to lowercase
            if email_service_provider.lower() in lower_case_list:
                # get the index of name match in the list (regardless of case)
                index = lower_case_list.index(email_service_provider.lower())

                # Using the index of where the correct key is located, 
                # use the dict which contains all entries of original dict to get exact key name
                dict_key_name = dict_keys_mapped_to_list[index]

                # Get the information pertaining to this dict key
                email_service_provider_info = self.email_providers_info[dict_key_name]
                found_valid_email_provider = True
            else:
                print("The desired email service provider not supported! Try using another one")
            
        # if user wants to use the pre-setup gmail accoun,
        # then program needs to change which smtp server it is trying to access
        if self.use_default is True or email_service_provider.lower() == "default":
            email_service_provider_info = self.email_providers_info['Default']
            # set to true for case of user opting into default during runtime
            self.use_default = True 

        return email_service_provider_info
    
    def add_contacts_to_contacts_list(self, first_name, last_name, email, carrier, phoneNumber):
        '''
            This function is responsible for adding another contact to the contact list by processing the inputs
            Args:\n
                first_name: first name of the person being added
                last_name: last name of the person being added
                email: email of the person being added
                carrier: carrier of the person being added
                phoneNumber: phone number of the person being added
        '''
        
        common_data_dict = {
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
        if last_name.lower() in lastNameLowerCaseList:
            # get the actual last name (with correct capitalization)
            indexOfLastName = lastNameLowerCaseList.index(last_name.lower())
            actualLastName = keysMappedToList[indexOfLastName]

            # check if need to add the person
            firstNameLowerCaseList = list(map(lambda x:x.lower(), newContactList[actualLastName].keys()))
            if first_name.lower() not in firstNameLowerCaseList:
                newContactList[last_name][first_name] = common_data_dict
            else: 
                # if already in list, ask user if they want to update the info
                firstNameKeysMappedToList = list(map(lambda x:x, newContactList[actualLastName].keys()))
                indexOfFirstName = firstNameLowerCaseList.index(first_name.lower())
                actualFirstName = firstNameKeysMappedToList[indexOfFirstName]

                user = newContactList[actualLastName][actualFirstName]

                print("Found user: {0} {1} with the following information: \
                    \nEmail: {2}\nPhone Number: {3}\nCell Carrier: {4}\n".format(
                    actualLastName, actualFirstName, user['email'], user['phoneNumber'], user['carrier']))
                update = input("Do you want to update their information (y/n): ")

                if (update == 'y'):
                    newContactList = self.updateContactInfo(first_name=actualFirstName, last_name=actualLastName, addingExternally=False)
       
        # If last name doesnt exist in contact list yet, then add it
        else:
            newContactList[last_name] = {}
            newContactList[last_name][first_name] = common_data_dict

        # Update existing variable used by rest of program so it constantly stays up to date
        self.contactList = newContactList
        print("The updated contacts list is:\n")
        pprint.pprint(self.contactList)

        # In either case, write updated version of contact list to the json file
        with open(self.path_to_contactList, 'w+') as write_file:
            json.dump(newContactList, write_file, indent=4)

    def updateContactInfo(self, first_name=None, last_name=None, addingExternally=True):
        '''
            Returns an updated version of the contact list
            Param "addingExternally" is true if this is being called as a stand alone function
        '''

        common_data_dict = {
            'email': '',
            'phoneNumber': '',
            'carrier': ''
        }
        updatedContactList = self.contactList

        if (first_name == None or last_name == None):
            first_name = input("Enter the person's first name you want to update: ")
            last_name = input("Enter the person's last name you want to update: ")

        # check to see if the person's last name already exists.
        lastNameLowerCaseList = list(map(lambda x:x.lower(), updatedContactList.keys()))
        # use index of lower case match to get actual value of key according to original mapped dict keys
        keysMappedToList = list(map(lambda x:x, updatedContactList.keys()))

        if last_name.lower() in lastNameLowerCaseList:
            # get the actual last name (with correct capitalization)
            indexOfLastName = lastNameLowerCaseList.index(last_name.lower())
            actualLastName = keysMappedToList[indexOfLastName]

            # get the actual first name
            firstNameLowerCaseList = list(map(lambda x:x.lower(), updatedContactList[actualLastName].keys()))
            if first_name.lower() not in firstNameLowerCaseList:
                print("user not found!")
                return None
            else: 
                firstNameKeysMappedToList = list(map(lambda x:x, updatedContactList[actualLastName].keys()))
                indexOfFirstName = firstNameLowerCaseList.index(first_name.lower())
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

        newFirstName = first_name
        newLastName = last_name
        common_data_dict['email'] = user['email']
        common_data_dict['carrier'] = user['carrier']
        common_data_dict['phoneNumber'] = user['phoneNumber']
        updatePhrase = "What would you like to change the <field> to: "
        if (updateFirstName == 'y'):
            newFirstName = input(updatePhrase.replace('<field>', 'first name'))
        if (updateLastName == 'y'):
            newLastName = input(updatePhrase.replace('<field>', 'last name'))
        if (updateEmail == 'y'):
            common_data_dict['email'] = input (updatePhrase.replace('<field>', 'email'))
        if (updateCarrier == 'y'):
            common_data_dict['carrier'] = input(updatePhrase.replace('<field>', 'cell carrier'))
        if (updatephoneNumber == 'y'):
            common_data_dict['phoneNumber'] = input(updatePhrase.replace('<field>', 'phone number'))
        
        if (len(updatedContactList[actualLastName]) == 1):
            del updatedContactList[actualLastName]
            updatedContactList[newLastName] = {}
            updatedContactList[newLastName][newFirstName] = common_data_dict
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
                updatedContactList[actualLastName][actualFirstName] = common_data_dict
        
        # handled by other function if internal
        if (addingExternally):
            # Update existing variable used by rest of program so it constantly stays up to date
            self.contactList = updatedContactList
            print("The updated contacts list is:\n")
            pprint.pprint(self.contactList)

            with open(self.path_to_contactList, 'w+') as write_file:
                json.dump(updatedContactList, write_file, indent=4)

        return updatedContactList

    def simpleAddContact(self):
        '''
            This function is responsible for adding another contact to the contact list 
            (no args needed because it will ask for inputs).
        '''

        first_name = input("Please enter their first name: ")
        last_name = input("Please enter their last name: ")
        my_email = input("Please enter their email: ")
        carrier = input("Please enter their cell phone carrier this person uses: ")
        phoneNumber = input("Please enter their phone number: ")

        # call function that handles the actual adding
        emailAgent(display_contacts=False).add_contacts_to_contacts_list(
            first_name, last_name, my_email, carrier, phoneNumber)

    def waitForNewMessage(self, msgFilter='(UNSEEN)'):
        '''
            This function halts the program until a new message is detected in the inbox

            Args:
                -msgFilter: Defaults to unseen emails but can be set to a value 
                    that will narrow down what is considered a valid email
        '''
        #first verify mode is IMAP
        if self.mode != "IMAP": self.connect_to_email_server("receive")
        
        num_emails = 0 # initialize to zero, actual calcs done in while loop
        search_code = 'OK'
        self.webAppPrintWrapper("waiting for new message...\n")
        
        while num_emails < 1 and search_code == 'OK':
            # Defaults to only look for unread emails
            self.email_server.select('INBOX')
            search_code, data = self.email_server.search(None, msgFilter) 
            num_emails = len(data[0].decode())
        
        # if this point is reached, new email detected and can end function so program can continue!
        self.webAppPrintWrapper("New email message detected!")       


    def receive_email(self, startedBySendingEmail=False):
        '''
            Args:
                -startedBySendingEmail:
                    True if started off by sending email and want to wait for users reponse
        '''

        email_service_provider_info = self.get_email_info("receive")['imap_server']

        self.connect_to_email_server("receive", host_address=email_service_provider_info['host_address'],
            port_num=email_service_provider_info['port_num'])

        if startedBySendingEmail == False:
            # input error checking
            filterInput = ""
            while filterInput != "n" and filterInput != "y":
                # search the inbox for all valid emails (first argument is 'charset' and second is 'filter')
                # "ALL" returns all emails without any filter
                # (UNSEEN) filter to all unread emails
                filterInput = input("Do you want to see only unopened emails (y/n): ")
                if filterInput == "n":
                    emailFilter = "ALL"
                elif filterInput == "y":
                    emailFilter = "(UNSEEN)"
                else:
                    raise Exception("Please enter a valid answer!\n")
        else:
            emailFilter = '(UNSEEN)'    
        
        # intially set to True but immediately set to False in loop
        # only set to True again if you wait for new messages
        keepCheckingInbox = True 
        while keepCheckingInbox: 

            keepCheckingInbox = False

            # opens folder/label you want to read from
            self.email_server.select('INBOX')
            self.webAppPrintWrapper("Successfully Opened Inbox")
            
            # get all the emails and their id #'s that match the filter
            search_code, data = self.email_server.search(None, emailFilter) 

            # Only try to check message data if return code is valid and there are emails matching the filter
            num_emails = len(data[0].decode()) 
            if search_code == "OK" and num_emails > 0:
                mail_ids = data[0].decode() # convert byte to string

                # convert to descending ordered list (mail_ids is a str with the mail_ids seperated by spaces)
                id_list = list(map(lambda x:int(x), list(mail_ids.split()))) 
                id_list.sort(reverse = True) # sort() performs operation on the same variable

                # fetch the emails in order of most recent to least recent
                # most recent email has the highest id number
                self.webAppPrintWrapper("id_list: {}".format(id_list))
                for id_num in id_list:
                    if id_num == max(id_list):
                        self.webAppPrintWrapper("Fetching most recent email")

                    # Check if mode is still in IMAP (might have changed if sent reply)
                    if self.mode == "SMTP": # if true then switch back and prime code to fetch
                        self.connect_to_email_server("receive")
                        self.email_server.select('INBOX')

                    return_code, data = self.email_server.fetch(str(id_num).encode(), '(RFC822)') 
                    raw_email = data[0][1]

                    # function returns (To, From, DateTime, Subject, Body)
                    emailTouple = self.process_raw_email(raw_email)
                    email_msg = {
                        "To": emailTouple[0],
                        "From": emailTouple[1],
                        "DateTime": emailTouple[2],
                        "Subject": emailTouple[3],
                        "Body": emailTouple[4]
                    }

                    # only ask this question if user didnt start off by sending emails
                    if startedBySendingEmail == False: 
                        replyBool = input("Do you want to reply to this email (y/n): ")
                    else:
                        replyBool = 'n'

                    if 'y' in replyBool:

                        # format of 'contactInfo'
                        contactInfo = {
                            'first_name' : '',
                            'last_name': '',
                            'email': '',
                            'carrier': '',
                            'phoneNumber' : ''
                        }

                        # send response to the information of "from" from the received email
                        contactInfo = self.numberToContact(email_msg["From"])

                        # if contactInfo is None, then sender of email not in contact list. Resort to other methods
                        if contactInfo == None:
                            # signifies sender was a cell phone
                            if '@' in email_msg["From"]:
                                # get phoneNumber/carrier info
                                tempDict = self.phoneNumberToParts(email_msg["From"])
                                # if it was a text message then only need this piece of information
                                contactInfo['phoneNumber'] = tempDict['phoneNumber']
                                contactInfo['carrier'] = tempDict['carrier']

                            # message was from an actual email
                            else:
                                contactInfo['email'] = email_msg['From']


                        self.sendMsg(contactInfo)

                    # Ask if they want to wait for a reply (only if user didnt start off by sending an email)
                    if startedBySendingEmail == False:
                        waitForMsg = input("Do you want to wait for a reply (yes/no): ")
                    else:
                        waitForMsg = 'y'

                    if 'y' in waitForMsg:
                        self.waitForNewMessage()
                        id_num += 1 # if a new message pops up then there must be another email
                        keepCheckingInbox = True # allows function to look at emails to repeat

                    # only give prompt if this is not the last email
                    if id_num != min(id_list):
                        next_email = input("Do you want to see the next email (yes/no): ")
                        if "n" in next_email:
                            break
                    else:
                        self.webAppPrintWrapper("That was the last email!")

            elif num_emails == 0:
                self.webAppPrintWrapper("No new emails in the inbox!")
                # Ask if they want to wait for a reply so long as user didnt start off by sending an email
                if startedBySendingEmail == False:
                    waitForMsg = input("\nDo you want to wait for a new message (yes/no): ")
                else:
                    waitForMsg = 'y'

                if 'y' in waitForMsg:
                    self.waitForNewMessage()
                    keepCheckingInbox = True # allows function to look at emails to repeat

            else:
                self.webAppPrintWrapper("Invalid return code from inbox!")

            # this var should only be set to True the first time it goes through if input starts as True.
            startedBySendingEmail = False
            

    def numberToContact(self, fullPhoneNumber:str):
        '''
            This function will attempt to match a phone number to an existing contact
            
            Returns:\n
                Contact info dictionary of format: {first name, last name, email, carrier, phone number}
                The phone number return accepts common type of seperaters or none (ex: '-')
        '''
        # seperate phone number into parts (phoneNumber and carrier)
        dataDict = self.phoneNumberToParts(fullPhoneNumber) 

        # iterate through contact list and check if phone number matches
        for last_names in self.contactList.keys():
            for first_names in self.contactList[last_names].keys():
                # check if phone number matches
                if self.contactList[last_names][first_names]["phoneNumber"].replace('-', '') == dataDict['phoneNumber']:
                    print("Matched recieved email to an existing contact!!")
                    return self.get_receiver_contact_info(first_names, last_names)

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
        for provider in self.email_providers_info.keys():
            # check if provider has an sms-gateway
            if 'SMS-Gateway' in self.email_providers_info[provider]['smtp_server'].keys():
                # check if gateway matches
                if self.email_providers_info[provider]['smtp_server']['SMS-Gateway'].lower() == smsGatewayTag:
                    carrier = provider
                    return {'phoneNumber':phoneNumber, 'carrier':carrier}
        
        # if code gets here, return phoneNumber but carrier is None
        return {'phoneNumber':phoneNumber, 'carrier': None}


    def setDefaultState(self, newState:bool):
        ''' 
            This function is responsible for changing the 'self' variable "use_default" 
            to whatever the argument newState is.
        '''
        self.use_default = newState

    
    def getDefaultState(self):
        ''' 
            This function is responsible for getting the 'self' variable "use_default" 
        '''
        return self.use_default 


    def process_raw_email(self, raw_email):
        '''
            This function returns the body of the raw email.
            The raw email needs to be processed because it contains alot of junk that makes it illegible 

            Args:
                -raw_email: a byte string that can be converted into a Message object
            Return:
                -refined_email(touple): The touple will contain (To, From, DateTime, Subject, body) 
        '''
        # convert byte literal to string removing b''
        email_msg = email.message_from_bytes(raw_email)      


        # If message is multi part we only want the text version of the body
        # This walks the message and gets the body.
        if email_msg.is_multipart():
            for part in email_msg.walk():       
                if part.get_content_type() == "text/plain":
                    #to control automatic email-style MIME decoding (e.g., Base64, uuencode, quoted-printable)
                    body = part.get_payload(decode=True) 
                    body = body.decode()

                elif part.get_content_type() == "text/html":
                    continue

        # Get date and time of email
        date_tuple = email.utils.parsedate_tz(email_msg['Date'])
        if date_tuple:
            local_date = datetime.datetime.fromtimestamp(
                email.utils.mktime_tz(date_tuple))
            dateTime = local_date.strftime("%a, %d %b %Y %H:%M:%S")

        # email delineator (get column size)
        columns, rows = shutil.get_terminal_size(fallback=(80, 24))
        delineator = columns - 2 # have to account for '<' and '>' chars on either end 
        print("\n<{0}>\n".format('-'*delineator)) 

        self.webAppPrintWrapper("""Email:\n
        To: {0}
        From: {1}
        DateTime: {2}
        Subject: {3}

        Body: {4}
        """.format(email_msg['To'], email_msg['From'], dateTime, email_msg['Subject'], body))

        self.webAppPrintWrapper("\n<{0}>\n".format('-'*delineator)) # email delineator

        return (email_msg['To'], email_msg['From'], dateTime, email_msg['Subject'], body)

    def scanForAttachments(self):
        '''
            @brief: takes in the current MEME msg object, scans for attachments that it can add on, 
                and returns the obj with the desired attachment
            @param: msg = the current msg object with all fields handled besides the attachment
            @return: the msg object with the attachments
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

        # add attachments that were found
        print("Checking if the following items are valid:\n{0}".format(attachmentList))
        for toAttach in attachmentList:
            self.addAttachment(toAttach)
        print("Done checking if attachments are valid")

    def addAttachment(self, toAttach:str):
        '''
            @breif: adds new attachment to existing message object
            @param: currentMsg: the current msg object with all fields handled besides the attachment
            @param: toAttach: a string that can either be a path to a local file or a url 
            
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
            @brief: determines if a url is valid syntactically and it exists
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
        if self.mode == "SMTP": self.email_server.quit()
        elif self.mode == "IMAP": self.email_server.logout()

    def start(self):
        '''
            Wrapper around run() function that jump starts the email process
        '''
        run()
        

def run():
    arg_length = len(sys.argv)
    # the order of arguments is: 
    # 0-file name, 1-first name, 2-last name, 3-skip login(optional- only activates if anything is typed)
    # "add contact" will help user to add a contact to the contact list
    # "update contact" will help user update a contact's info


    # use this phrase to easily add more contacts to the contact list
    if 'add_contact' in sys.argv:
        emailer = emailAgent(display_contacts=True, commandLine=True)
        emailer.simpleAddContact()
        sys.exit()
    
    if 'update_contact' in sys.argv:
        emailer = emailAgent(display_contacts=True, commandLine=True)
        emailer.updateContactInfo()
        sys.exit()

    # Create a class obj for this file
    emailer = emailAgent(display_contacts=False, commandLine=True)

    if 'default' in ''.join(sys.argv):
        emailer.setDefaultState(True)
    else:
        emailer.setDefaultState(False)

    # determine what the user wants to use the emailing agent for
    service_type = input("\nTo send an email type 'send'. To check your inbox type 'get': ").lower()

    if "send" in service_type:

        # First check that enough arguments were provided (if not do it manually)
        if arg_length < 3: 
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
                
                first_name = fullName[0]
                last_name = fullName[1]
                
        else:
            # Get arguments from when script is called
            first_name = sys.argv[1]
            last_name = sys.argv[2]
            # receiver_contact_info contains first_name, last_name, email, carrier, phone number

        # get contact info regardless of method to reach this point
        receiver_contact_info = emailer.get_receiver_contact_info(first_name, last_name)

        # arg_length- if all arguments given when calling script
        if arg_length == 4:
            # if there is a third argument, then use default email account (dont need to login)
            emailer.setDefaultState(True)

        emailer.sendMsg(receiver_contact_info)
    
        waitForReply = input("Do you want to wait for a reply (y/n): ")
        if 'n' not in waitForReply:
            emailer.receive_email(startedBySendingEmail=True)

    elif "get" in service_type:
        # Entering something in the second argument signifies that you want to use the default login
        emailer.receive_email()
            
    else:
        print("Please Enter a Valid Option!")

    # logout
    emailer.logoutEmail()

    print("Closing Program")
    

if __name__ == "__main__":
    run() # starts the code

