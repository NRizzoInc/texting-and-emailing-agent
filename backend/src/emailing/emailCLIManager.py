#!/usr/bin/python3

"""
    @file Helps manage the emailAgent's CLI 
    @Note: Will should be imported by it, so be wary of circular included
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import os, sys
import argparse # for CLI Flags

#--------------------------------OUR DEPENDENCIES--------------------------------#
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils

class CLIManager():
    def __init__(self, EmailAgent):
        """
            \n@Brief: This class is responsible for spinning off the email agent via it's CLI Flags4
            \n@Param: EmailAgent - Reference to EmailAgent class (cannot directly import or else get circular chain)
        """
        # prevent magic numbers for service types
        # map class functions for sending & getting emails to a dictionary's keys
        self.serviceTypes = {
            "send": self.sendText,
            "receive": self.getText,
            "None": self.sendText # if non-entered, default to sending
        }
    
        parser = argparse.ArgumentParser(description="Emailing & Texting Application CLI")
    
        ##################################################################################################################
        # contact managing group - should be exclusive (should not add & update contacts at same time)
        ##################################################################################################################
        contactManagerGroup = parser.add_argument_group(
            title="Contacts Managers",
            description="Helps to add, update, & remove contacts"
        )
        contactManagerGroup.add_argument(
            "-a", "--add-contact",
            action="store_true", # defaults to false
            required=False,
            dest="addContact",
            help="Add a contact to the contact list",
        )
        contactManagerGroup.add_argument(
            "-u", "--update-contact",
            action="store_true", # defaults to false
            required=False,
            dest="updateContact",
            help="Update a contact in the contact list",
        )

        ##################################################################################################################
        # Login Group
        # TODO: eventually add flags to specific username & password
        ##################################################################################################################
        contactManagerGroup = parser.add_argument_group(
            title="Login Helpers",
            description="Helps log in to your email account (or use default)"
        )
        # check if using default email account
        contactManagerGroup.add_argument(
            "-d", "--use-default-sender",
            action="store_true", # defaults to false
            required=False,
            dest="useDefault",
            help="If used, will login to default account that does not require user interaction",
        )

        ##################################################################################################################
        # Service Types (Send & Receiving)
        ##################################################################################################################
        serviceDest = "serviceType" # Both send & receive set their value in the args['serviceType']
        serviceGroup = parser.add_argument_group(
            title="Services",
            description="Helps to choose what you want to do",
        )
        serviceGroup.add_argument(
            "-s", "--send",
            action="store_const",
            const="send",
            dest=serviceDest,
            required=False,
            help="Send an email/text messages",
        )
        serviceGroup.add_argument(
            "-r", "--receive",
            action="store_const",
            const="receive",
            dest=serviceDest,
            required=False,
            help="Receive email/text messages",
        )

        ##################################################################################################################
        # Receipient Managers (First & Last Name)
        # If first or last name not entered, stored as None
        ##################################################################################################################
        nameMetaVar="<name>"
        receipientManagerGroup = parser.add_argument_group(
            title="Receipient",
            description="Helps choose who to send the email to",
        )
        receipientManagerGroup.add_argument(
            "-f", "--firstname",
            metavar=nameMetaVar,
            default=None,
            dest="fname",
            required=False,
            help="The receipient's firstname",
        )
        receipientManagerGroup.add_argument(
            "-l", "--lastname",
            metavar=nameMetaVar,
            default=None,
            dest="lname",
            required=False,
            help="The receipient's lastname",
        )

        # Actually Parse Flags (turn into dictionary)
        args = vars(parser.parse_args()) # converts all '-' after '--' to '_' (--add-contact -> 'add_contact')

        # use this phrase to easily add more contacts to the contact list
        if args["addContact"]:
            emailer = EmailAgent(displayContacts=True, isCommandLine=True)
            emailer.simpleAddContact()
            sys.exit(0)
        
        elif args["updateContact"]:
            emailer = EmailAgent(displayContacts=True, isCommandLine=True)
            emailer.updateContactInfo()
            sys.exit(0)

        # Create a class obj for this file
        emailer = EmailAgent(displayContacts=False, isCommandLine=True)

        # based on if CLI flag is used, set the default's state
        emailer.setDefaultState(args["useDefault"])

        # determine what the user wants to use the emailing agent for
        # dont ask if user already specified via CLI flags
        serviceType = args[serviceDest] if utils.keyExists(args, serviceDest) else EmailAgent.getServiceType()

        # each function takes the email agent as first arg, and have optional for the rest
        # firstname, lastname, etc...
        selectedFn = self.serviceTypes[str(serviceType)]
        selectedFn(emailer, firstname=args['fname'], lastname=args['lname'])

        # logout
        emailer.logoutEmail()

        print("Closing Program")


    def sendText(self, emailer, firstname=None, lastname=None):
        # Inform users of who is current in contact list before selecting one (or adding another)
        currContactList = emailer.printContactListPretty(printToTerminal=False)
        contactListPrint = f"The existing contact list includes:\n{currContactList}"
        print(contactListPrint)

        # Check if they want to add a new contact
        addContact = utils.promptUntilSuccess("Do you want to add a new contact to this list(y/n): ")
        if addContact == 'y' or addContact == 'yes': emailer.simpleAddContact()

        # check if user wants to send a message
        sendMsg = utils.promptUntilSuccess(
            "Do you want to send a message to one of these contacts (y/n): ",
            successCondition=utils.containsConfirmation
        )
        if sendMsg == 'y': 
            # First check first & last name were provided
            # Dont need an else (both provided)
            createNamePrompt = lambda x: f"Enter the receipient's {x}: "
            if firstname == None and lastname == None:
                firstname = utils.promptUntilSuccess(createNamePrompt("firstname"))
                lastname = utils.promptUntilSuccess(createNamePrompt("lastname"))
            elif firstname == None:
                firstname = utils.promptUntilSuccess(createNamePrompt("firstname"))
            elif lastname == None:
                lastname = utils.promptUntilSuccess(createNamePrompt("lastname"))

            # get contact info regardless of method to reach this point
            receiverContactInfo = emailer.getReceiverContactInfo(firstname, lastname)

            # acutally send message
            emailer.sendMsg(receiverContactInfo)

        # regardless of if sent a message or not, see if user wants to wait for reply
        waitForReply = utils.promptUntilSuccess(
            "Do you want to wait for a reply (y/n): ", successCondition=utils.containsConfirmation)
        if 'n' not in waitForReply: emailer.receiveEmail(startedBySendingEmail=True, onlyUnread=True)

    def getText(self, emailer, firstname=None, lastname=None):
        # Entering something in the second argument signifies that you want to use the default login
        seeUnopned = utils.promptUntilSuccess(
            "Do you want to see only unopened emails (y/n): ", successCondition=utils.containsConfirmation)
        if filterInput == "y": emailer.receiveEmail(onlyUnread=True)
        elif filterInput == "n": emailer.receiveEmail(onlyUnread=False)
        else: print("Invalid Arg Entered!")
