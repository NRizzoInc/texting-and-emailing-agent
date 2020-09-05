#!/usr/bin/python3

"""
    @file Helps manage the emailAgent's CLI 
    @Note: Will should be imported by it, so be wary of circular included
"""

#------------------------------STANDARD DEPENDENCIES-----------------------------#
import os, sys
import argparse # for CLI Flags
import functools

#--------------------------------OUR DEPENDENCIES--------------------------------#
# make sure to include 'backend' dir to get access to module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from backend.src import utils
from backend.src.emailing.emailAgent import EmailAgent

class CLIManager(EmailAgent):
    def __init__(self):
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
            "-list", "--contact-list",
            action="store_true",
            dest="shouldPrintContacts",
            required=False,
            help="Print the contact list",
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
        receipientManagerGroup.add_argument(
            "--available-provider-list",
            action="store_true",
            dest="getProviderList",
            required=False,
            help="Print out all cell service providers that can be texted with this program & exit",
        )

        ##################################################################################################################
        # Message Content
        ##################################################################################################################
        contentGroup = parser.add_argument_group(
            title="Message Content",
            description="Helps craft email/text to send via command line without needing input later on"
        )
        contentGroup.add_argument(
            "-m,", "--message",
            metavar="<message>",
            default=None,
            required=False,
            help="The message to send",
        )
        contentGroup.add_argument(
            "-x,", "--send-method",
            metavar="<method>",
            dest="sendMethod",
            default=None,
            required=False,
            help="How the message should be sent (via 'text' or 'email')",
        )

        ##################################################################################################################
        # Login Managers
        ##################################################################################################################
        loginManagersGroup = parser.add_argument_group(
            title="Login",
            description="Helps update login information & log in to your email account (or use default)"
        )
        loginManagersGroup.add_argument(
            "-user", "--username",
            action="store_true",
            dest="setUsername",
            required=False,
            help="Set what username (display name) when sending text messages and exit",
        )
        loginManagersGroup.add_argument(
            "-p", "--password",
            action="store_true",
            dest="setPassword",
            required=False,
            help="Set your password when logging in and exit",
        )
        loginManagersGroup.add_argument(
            "-ea", "--email-address",
            default=None,
            dest="emailAddress",
            required=False,
            help="What is your actual (i.e. gmail) email address",
        )
        loginManagersGroup.add_argument(
            "-ep", "--email-password",
            default=None,
            dest="emailPassword",
            required=False,
            help="What is your actual (i.e. gmail) email address's password",
        )
        # check if using default email account
        loginManagersGroup.add_argument(
            "-nd", "--non-default",
            action="store_false", # defaults to true
            required=False,
            dest="useDefault",
            help="If used, will make user login to the non-default account that requires user interaction to login"
        )

        # Actually Parse Flags (turn into dictionary)
        args = vars(parser.parse_args()) # converts all '-' after '--' to '_' (--add-contact -> 'add_contact')

        # use this phrase to easily add more contacts to the contact list
        # trigger EmailAgent init based on the situation (this point forward, 'self' will contain EmailAgent attributes)
        if args["addContact"]:
            super().__init__(displayContacts=True, isCommandLine=True, useDefault=args["useDefault"],
                emailAddress=args["emailAddress"], emailPassword=args["emailPassword"])
            self.simpleAddContact()
            sys.exit(0)
        
        elif args["shouldPrintContacts"]:
            super().__init__(displayContacts=False, isCommandLine=True, useDefault=args["useDefault"],
                emailAddress=args["emailAddress"], emailPassword=args["emailPassword"])
            self.printContactListPretty(printToTerminal=True)
            sys.exit(0)
        elif args["updateContact"]:
            super().__init__(displayContacts=True, isCommandLine=True, useDefault=args["useDefault"],
                emailAddress=args["emailAddress"], emailPassword=args["emailPassword"])
            self.updateContactInfo()
            sys.exit(0)
        elif args["setUsername"] or args["setPassword"]:
            super().__init__(displayContacts=False, isCommandLine=True, useDefault=args["useDefault"],
                emailAddress=args["emailAddress"], emailPassword=args["emailPassword"])
            self.configureLogin(overrideUsername=args["setUsername"], overridePassword=args["setPassword"])
            sys.exit(0)
        elif args["getProviderList"]:
            super().__init__(displayContacts=False, isCommandLine=True, useDefault=args["useDefault"],
                emailAddress=args["emailAddress"], emailPassword=args["emailPassword"])
            cellProviders = self.getTextableProviders()
            formatProviders = lambda x, y: f"{x}\n{y}" 
            formattedProviders = functools.reduce(formatProviders, cellProviders)
            print(f"The possible cell providers are:\n{formattedProviders}")
            sys.exit(0)

        # Create a class obj for this file
        super().__init__(displayContacts=False, isCommandLine=True, useDefault=args["useDefault"],
            emailAddress=args["emailAddress"], emailPassword=args["emailPassword"])

        # based on if CLI flag is used, set the default's state
        self.setDefaultState(args["useDefault"])

        # determine what the user wants to use the emailing agent for
        # dont ask if user already specified via CLI flags
        serviceType = args[serviceDest] if utils.keyExists(args, serviceDest) else self.getServiceType()

        # each function takes the email agent as first arg, and have optional for the rest
        # firstname, lastname, etc...
        selectedFn = self.serviceTypes[str(serviceType)]
        selectedFn(firstname=args['fname'], lastname=args['lname'], sendMethod=args["sendMethod"], message=args["message"])

        # logout
        self.logoutEmail()

        print("Closing Program")


    def sendText(self, firstname=None, lastname=None,
                sendMethod=None, message=None,
                *args, **kwargs
        ):

        # If first and last name not provided, have to manually ask for it
        receiveInfoProvided = firstname != None and lastname != None
        if not receiveInfoProvided:
            # Inform users of who is current in contact list before selecting one (or adding another)
            currContactList = self.printContactListPretty(printToTerminal=False)
            contactListPrint = f"The existing contact list includes:\n{currContactList}"
            print(contactListPrint)

            # Check if they want to add a new contact
            addContact = utils.promptUntilSuccess("Do you want to add a new contact to this list(y/n): ")
            if addContact == 'y' or addContact == 'yes': self.simpleAddContact()

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
            else: return

        # get contact info regardless of method to reach this point
        receiverContactInfo = self.getReceiverContactInfo(firstname, lastname)

        # acutally send message
        self.sendMsg(receiverContactInfo, sendMethod=sendMethod, msgToSend=message)

        # regardless of if sent a message or not, see if user wants to wait for reply
        waitForReply = utils.promptUntilSuccess(
            "Do you want to wait for a new message (y/n): ", successCondition=utils.containsConfirmation)
        if 'n' not in waitForReply: self.receiveEmail(startedBySendingEmail=True, onlyUnread=True)

    def getText(self, firstname=None, lastname=None, message=None, *args, **kwargs):
        # Entering something in the second argument signifies that you want to use the default login
        seeUnopned = utils.promptUntilSuccess(
            "Do you want to see only unopened emails (y/n): ", successCondition=utils.containsConfirmation)
        if seeUnopned == "y": self.receiveEmail(onlyUnread=True)
        elif seeUnopned == "n": self.receiveEmail(onlyUnread=False)
        else: print("Invalid Arg Entered!")

    def getServiceType(self):
        """Helps to determine what user wants to do via terminal inputs"""
        createPrompt = lambda currKey, nextKey: f"{currKey} or {nextKey}"
        keysString = reduce(createPrompt, list(serviceTypes.keys()))
        prompt = "Type {0}".format(keysString)

        isValidType = False
        while not isValidType:
            serviceType = input(prompt).lower()
            isValidType = utils.keyExists(cls.serviceTypes, serviceType)
            # return or print error based on if entered value is valid
            if (not isValidType):   print("Please Enter a Valid Option!")
            else:                   return serviceType

if __name__ == "__main__":
    # Create all CLI Flags & spin off code
    emailCLI = CLIManager()
