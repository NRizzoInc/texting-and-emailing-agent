#!/usr/bin/python3


#------------------------------STANDARD DEPENDENCIES-----------------------------#
import os, sys
import json # to get data from POST only forms
import urllib.request
import re
import platform
import subprocess
import socket # used to get local network exposible IP
import uuid # used to generate keys for handling private data 
import logging # used to disable printing of each POST/GET request

# This file is responsible for creating a flask Web App UI 
#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
import flask
from flask import Flask, templating, render_template, request, redirect
from flask_socketio import SocketIO

#--------------------------------OUR DEPENDENCIES--------------------------------#
import emailAgent
import utils

class WebApp():
    def __init__(self, isDebug=False):
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
        _urls = utils.loadJson(os.path.join(self.app.static_folder, "urls.json"))
        self.sites = _urls["sites"]
        self.formSites = _urls["formSites"]
        self.infoSites = _urls["infoSites"]

        # create all sites to begin with
        self.initializingStatus = True
        self.generateSites()
        self.createInfoSites()
        self.generateFormResultsSites()
        self.printSites()
        self.initializingStatus = False

        # set logging (hide POST/GET Requests if not debugging)
        self.__isDebug = isDebug
        self._logger = logging.getLogger("werkzeug")
        logLevel = logging.INFO if self.__isDebug == True else logging.ERROR
        self._logger.setLevel(logLevel)

        # start up the web app
        self.app.config["TEMPLATES_AUTO_RELOAD"] = True # refreshes flask if html files change
        self.flaskSocket = SocketIO(self.app, async_mode="threading")
        self.app.run(host=self.host_ip, port=self.host_port, debug=self.__isDebug)
    
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

    def createInfoSites(self):
        @self.app.route(self.infoSites["emailData"], methods=["POST"])
        def getEmailData()->dict():
            # TODO: do a security check (has an authKey field but need to tie it to something)
            emailData = flask.request.get_json()
            toRtn = {}
            emailContents = self.emailAgent.openEmailById(emailData["idDict"], emailData["emailList"], emailData["emailId"])
            toRtn["emailContent"] = emailContents.strip()
            return self.returnSuccessResp(additionalDict=toRtn)

    # form submissions get posted here (only accessible)
    def generateFormResultsSites(self):
        formData = {}
        @self.app.route(self.formSites['textForm'], methods=['POST'])
        def createTextForm():
            optDataDict = {} # add keys to be returned at end of post request
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
                    # responsible for login to get preliminary email data
                    # use ui dropdown to select which email to fully fetch
                    numToFetch = 5 # TODO: stub -- add select box in frontend
                    preliminaryEmailData = self.emailAgent.receiveEmail(onlyUnread=False, maxFetchCount=numToFetch)
                    optDataDict = {**optDataDict, **preliminaryEmailData} # merge dicts
                    optDataDict["authKey"] = str(uuid.uuid4()) # https://docs.python.org/3/library/uuid.html -- safe random uuid

                    # TODO: somehow inform user on webpage of send error (return should have error message)
                    if (optDataDict["error"] == True):
                        print("Failed to receive emails: \n{0}".format(optDataDict["text"]))
                
                elif (formData['task'] == "adding-contact"):
                    carrier = formData['carrier']
                    phoneNumber = formData['phoneNumber']
                    self.emailAgent.addContact(firstName, lastName, email, carrier, phoneNumber)
                else:
                    raise Exception("UNKNOWN TASK")

            # return to original site
            return self.returnSuccessResp(optDataDict)

    def sendToClient(self, messageName, contentJson=None):
        """
            Function to enable communication from backend to front-end via sockets
        """
        if contentJson:
            self.flaskSocket.emit(messageName, contentJson)
        else:
            self.flaskSocket.emit(messageName)

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