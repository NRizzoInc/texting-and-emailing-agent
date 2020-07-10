#!/usr/bin/python3

import os, sys
import json # to get data from POST only forms
import urllib.request
import re
import platform
import subprocess
import socket # used to get local network exposible IP

# This file is responsible for creating a flask Web App UI 
#-----------------------------DEPENDENCIES-----------------------------#
import flask
from flask import Flask, templating, render_template, request, redirect

import emailAgent # need to call functions
class WebApp():
    def __init__(self):
        self.emailAgent = emailAgent.emailAgent(displayContacts=True, isCommandLine=False)
        self.host_ip = self.getIP()
        self.host_port = '5000' # port 5000 allowed through firewall
        self.host_address = 'http://' + self.host_ip + ':' + self.host_port
        self.app = Flask(__name__)

        # change location of where the html, css, and js code lives
        self.__pathToThisDir = os.path.dirname(os.path.abspath(__file__))
        self.app.static_folder = os.path.join(self.__pathToThisDir, "frontend", "static") 
        self.app.template_folder = os.path.join(self.__pathToThisDir, "frontend", "htmlTemplates")
        # needs to be kept within the static folder so it can be loaded
        _urls = emailAgent.emailAgent.loadJson(os.path.join(self.app.static_folder, "urls.json"))
        self.sites = _urls["sites"]
        self.formSites = _urls["formSites"]
        self.infoSites = _urls["infoSites"]

        # store terminal data for frontend (used for receiving emails)
        # WARNING: should get cleared after use
        self._terminalData = ""

        # create all sites to begin with
        self.initializingStatus = True
        self.generateSites()
        self.generateFormResultsSites()
        self.printSites()
        self.createInfoPages()
        self.initializingStatus = False

        # start up the web app
        self.__debugOn = False
        self.app.run(host=self.host_ip, port=self.host_port, debug=self.__debugOn)
    
    def getIP(self):
        myPlatform = platform.system()
        if myPlatform == "Windows":
            hostname = socket.gethostname()
            IPAddr = socket.gethostbyname(hostname)
            return IPAddr
        elif myPlatform == "Linux":
            ipExpr = r'inet ([^.]+.[^.]+.[^.]+.[^\s]+)'
            output = subprocess.check_output("ifconfig").decode()
            matches = re.findall(ipExpr, output)
            for ip in matches:
                print("Found ip: {0}".format(ip))
                return ip


    def generateSites(self):
        '''
            This function is a wrapper around all the other functions which actually create pages.
            Hence, by calling this function all sites will be initialized.
        '''
        # wrap pages in generateSites function so that 'self' can be used
        # for each function render the sidebar so that there is a single source of truth for its design
        @self.app.route(self.sites['landingpage'], methods=["GET", "POST"])
        def createMainPage():
            return render_template("mainPage.html", title="Texting App Main Page", links=self.sites)

        @self.app.route(self.sites['textpage'], methods=["GET", "POST"])
        def createTextPage():
            contactList = self.emailAgent.printContactListPretty(printToTerminal=False)
            return render_template("textPage.html", title="Texting App Texting Page", 
                links=self.sites, forms=self.formSites, contacts=contactList)

        @self.app.route(self.sites['emailpage'], methods=["GET", "POST"])
        def createEmailPage():
            self.emailAgent.updateContactList()
            contactList = self.emailAgent.printContactListPretty(printToTerminal=False)
            return render_template("emailPage.html", title="Texting App Email Page", 
                links=self.sites, forms=self.formSites, contacts=contactList)

        @self.app.route(self.sites['aboutpage'], methods=["GET", "POST"])
        def createAboutPage():
            return render_template("aboutPage.html", title="Texting App About Page", links=self.sites)

        @self.app.route('/crash')
        def test():
            raise Exception()
    
    # form submissions get posted here (only accessible)
    def generateFormResultsSites(self):
        formData = {}
        @self.app.route(self.formSites['textForm'], methods=['POST'])
        def createTextForm():
            # if form is given data
            if (not self.initializingStatus):
                url = self.host_address + self.formSites['textForm']
                formData = flask.request.get_json()
                # collect all form information
                firstName = formData['firstName']
                lastName = formData['lastName']

                # login info error-checking
                try:
                    email = formData['emailAddress']
                    password = formData['password']
                    if (len(email) == 0 or len(password) == 0):
                        self.emailAgent.setDefaultState(True)
                    else:
                        # if no errors and not empty then okay to use non default accoount
                        self.emailAgent.setDefaultState(False) 
                except Exception as e:
                    # if there is an error just use the default sender/receiver
                    self.emailAgent.setDefaultState(True)

                # check if receive if sending/receiving message form
                if (formData['task'] == "sending"):
                    print("Sending Text")
                    message = formData['message']
                    receiverContactInfo = self.emailAgent.getReceiverContactInfo(firstName, lastName)
                    
                    sendErr = self.emailAgent.sendMsg(receiverContactInfo, sendMethod='text', msgToSend=message)
                    if (sendErr != None):
                        print(sendErr)
                        # TODO: somehow inform user on webpage of send error (return should have error message)
                
                elif (formData['task'] == "receiving"):
                    print("Receiving Text")
                    numToFetch = 5 # TODO: stub -- add select box in frontend
                    recvDict = self.emailAgent.receiveEmail(onlyUnread=False, maxFetchCount=numToFetch)
                    if (recvDict["error"] == True):
                        print("Failed to receive emails: \n{0}".format(recvDict["text"]))
                        # TODO: somehow inform user on webpage of send error (return should have error message)
                    else:
                        # clear old data & set new
                        self._terminalData = recvDict["text"]
                
                elif (formData['task'] == "adding-contact"):
                    carrier = formData['carrier']
                    phoneNumber = formData['phoneNumber']
                    self.emailAgent.addContact(firstName, lastName, email, carrier, phoneNumber)
                else:
                    raise Exception("UNKNOWN TASK")

            # return to original site
            return self.returnSuccessResp()

    # this function helps siphon stuff meant to print to terminal to a webpage to get 
    def createInfoPages(self):
        @self.app.route(self.infoSites["terminalText"], methods=["GET", "POST"])
        def managerTerminalText():
            # just return 
            if flask.request.method == "GET":
                return self.returnSuccessResp({"terminalData": self._terminalData})
            elif flask.request.method == "POST":
                # recv = str(flask.request.get_data(as_text=True))
                # do something... (eventually use post to trigger something)
                return "POST not implemented\n"

    def printSites(self):
        '''
            Helper function to tell user the location of each site
        '''
        print("\nAll the created sites are: \n")
        for site in self.sites.keys():
            print("{0}{1}".format(self.host_address, self.sites[site]))
        print() # newline
    
    def returnSuccessResp(self, additionalDict={}):
        """
            Helper function for flask app route request to tell frontend success and additional data
        """
        flaskResponseDict = {'success':True}
        dataDict = {**flaskResponseDict, **additionalDict} # merge dictionaries
        return json.dumps(dataDict), 200, {'ContentType':'application/json'}



if __name__ == "__main__":
    ui = WebApp()