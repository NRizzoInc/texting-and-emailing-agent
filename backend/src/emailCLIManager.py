#!/usr/bin/python3

"""
    @file Helps manage the emailAgent's CLI 
    @Note: Will should be imported by it, so be wary of circular included
"""

import utils

class CLIManager():
    def __init__(self):
        pass # stub

    @classmethod
    def sendText(cls, emailer, firstname=None, lastname=None):
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

    @classmethod
    def getText(cls, emailer, firstname=None, lastname=None):
        # Entering something in the second argument signifies that you want to use the default login
        seeUnopned = utils.promptUntilSuccess(
            "Do you want to see only unopened emails (y/n): ", successCondition=utils.containsConfirmation)
        if filterInput == "y": emailer.receiveEmail(onlyUnread=True)
        elif filterInput == "n": emailer.receiveEmail(onlyUnread=False)
        else: print("Invalid Arg Entered!")
