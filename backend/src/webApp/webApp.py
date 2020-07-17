#!/usr/bin/python3


#------------------------------STANDARD DEPENDENCIES-----------------------------#
import os, sys
import json # to get data from POST only forms
import urllib.request
import subprocess
import logging # used to disable printing of each POST/GET request
import secrets # needed to generate secure secret key for flask app
import webbrowser # allows opening of new tab on start
import argparse # for CLI Flags

# This file is responsible for creating a flask Web App UI 
#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
import flask
from flask import Flask, templating, render_template, request, redirect, flash, url_for
from flask_socketio import SocketIO
import werkzeug.serving # needed to make production worthy app that's secure

# decorate app.route with "@login_required" to make sure user is logged in before doing anything
# https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader -- "flask_login.login_required"
from flask_login import login_user, current_user, login_required, logout_user
from is_safe_url import is_safe_url

#--------------------------------OUR DEPENDENCIES--------------------------------#
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utils
from userManager import User, UserManager
from registrationForm import RegistrationForm
from loginForm import LoginForm
import webAppConsts

class WebApp(UserManager):
    def __init__(self, isDebug:bool=False, port:str=None):
        """
            \n@Brief: Creates a web application that provides a GUI for running the email app
            \n@Note: Automatically finds and uses your publically exposed ip address (not localhost)
            \n@Note: Calling this class will spin up the web app and block your programs executation
            \n@Param: isDebug - Should the flask app run with debug mode on
            \n@Param: post - The port to connect the flask app on
        """
        self.hostIP = utils.getIP()
        self.hostPost = port if port != None and len(port) > 0 else '5000'
        self.hostAddr = 'http://' + self.hostIP + ':' + self.hostPost
        self.app = Flask(__name__)

        # Inheret all functions and 'self' variables (UserManager)
        super().__init__(self.app)

        # change location of where the html, css, and js code lives
        self.__pathToThisDir = webAppConsts.pathToThisDir
        self.__backendDir = webAppConsts. backendDir
        self.__rootDir = webAppConsts.rootDir
        self.__frontendDir = webAppConsts.frontendDir
        self.app.static_folder = webAppConsts.staticDir
        self.app.template_folder = webAppConsts.htmlDir
        # needs to be kept within the static folder so it can be loaded
        self.sites = webAppConsts.sites
        self.formSites = webAppConsts.formSites
        self.infoSites = webAppConsts.infoSites
        self.settingsSites = webAppConsts.settingsSites
        # TODO: find less kludgy way to combine 3 dicts into one
        # (missing settingsSites, but that is just for posting and getting, not redirect)
        self._urls = utils.mergeDicts(utils.mergeDicts(self.sites, self.formSites), self.infoSites)

        # create all sites to begin with
        self.initializingStatus = True
        self.generateSites()
        self.createInfoSites()
        self.createSettingsSites()
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
        self.app.config["SECRET_KEY"] = secrets.token_urlsafe(64) # needed to keep data secure
        self.flaskSocket = SocketIO(self.app, async_mode="threading")
        # webbrowser.open(self._getSiteUrl(self.sites["landingpage"])) # wont work in deploy setting
        self.app.run(host=self.hostIP, port=self.hostPost, debug=self.__isDebug)
        # werkzeug.serving.run_simple(hostname=self.hostIP, port=int(self.hostPost), application=self.app, use_debugger=self.__isDebug)

    def createSettingsSites(self):
        """Helper function for creating "settingsSites' that provides closure for 'self' variables"""
        @self.app.route(self.settingsSites["numFetch"], methods=["GET", "POST"])
        @login_required
        def createNumFetchSetting():
            if flask.request.method == "GET":
                currNumFetch = current_user.getNumFetch()
                return self.returnSuccessResp({"numFetch": currNumFetch})
            elif flask.request.method == "POST":
                newNumFetch = int(flask.request.get_json()["numFetch"])
                current_user.setNumFetch(newNumFetch)
                return self.returnSuccessResp({"numFetch": newNumFetch})

    def generateSites(self):
        '''
            This function is a wrapper around all the other functions which actually create pages.
            Hence, by calling this function all sites will be initialized.
        '''
        # wrap pages in generateSites function so that 'self' can be used
        # for each function render the sidebar so that there is a single source of truth for its design
        @self.app.route(self.sites['landingpage'], methods=["GET", "POST"])
        def createMainPage():
            return render_template("mainPage.html", title="Texting App Main Page",
                links=self.sites, formLinks=self.formSites)

        @self.app.route(self.sites['textpage'], methods=["GET", "POST"])
        @login_required
        def createTextPage():
            # proxy for current User object that triggered this
            contactList = current_user.getContactList()
            return render_template("textPage.html", title="Texting App Texting Page", 
                links=self.sites, formLinks=self.formSites, contacts=contactList)

        @self.app.route(self.sites['emailpage'], methods=["GET", "POST"])
        @login_required
        def createEmailPage():
            # proxy for current User object that triggered this
            contactList =  current_user.getContactList()
            return render_template("emailPage.html", title="Texting App Email Page", 
                links=self.sites, formLinks=self.formSites, contacts=contactList)

        @self.app.route(self.sites['aboutpage'], methods=["GET", "POST"])
        def createAboutPage():
            return render_template("aboutPage.html", title="Texting App About Page",
                links=self.sites, formLinks=self.formSites)

        @self.app.route(self.formSites["webAppLogin"], methods=["GET", "POST"])
        def login():
            """
                https://flask-login.readthedocs.io/en/latest/
                https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins
                Here we use a class of some kind to represent and validate our
                client-side form data. For example, WTForms is a library that will
                handle this for us, and we use a custom LoginForm to validate.
            """
            # do not attempt to login if already logged in
            if current_user.is_authenticated:
                return redirect(self.sites["landingpage"])

            # https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader
            # -- "flask_login.login_user"
            form = LoginForm(self.app)

            if form.validate_on_submit():
                # username & password fields of form have been validated at this point
                # They will be 'None' if validation failed
                username = form.username.data
                password = form.password.data
                validUsername = username != None
                validPassword = password != None

                # check results
                isSuccess = validUsername and validPassword # only both true == success
                if isSuccess:
                    user = self.getUserByUsername(username)
                    login_user(user, remember=form.rememberMe.data)

                    # route to original destination
                    # is_safe_url should check if the url is safe for redirects.
                    # See http://flask.pocoo.org/snippets/62/ for an example.
                    next = flask.request.args.get('next')
                    isNextBad = next == None or not is_safe_url(next, self._urls)
                    if isNextBad:
                        return redirect(next or self.sites["landingpage"])
                    else:
                        return redirect(next)

                    # on error, keep trying to login until correct
                    return redirect(self.formSites["webAppLogin"])

            return render_template('login.html', title='Sign In', form=form, 
                links=self.sites, formLinks=self.formSites)

        @self.app.route(self.formSites["webAppRegister"], methods=["GET", "POST"])
        def register():
            """
                Creates registration page
            """
            if current_user.is_authenticated:
                return redirect(self.sites["landingpage"])
            form = RegistrationForm(self.app)
            if form.validate_on_submit():
                self.addUser(form.username.data, form.password.data)
                flash('Congratulations, you are now a registered user!')
                return redirect(self.formSites["webAppLogin"])
            return render_template('register.html', title='Register', form=form,
                links=self.sites, formLinks=self.formSites)

        @self.app.route('/crash')
        def test():
            raise Exception()

    def createInfoSites(self):
        @self.app.route(self.infoSites["emailData"], methods=["POST"])
        @login_required
        def getEmailData()->dict():
            emailData = flask.request.get_json()
            toRtn = {}
            emailContents = current_user.selectEmailById(emailData["idDict"], emailData["emailList"], emailData["emailId"])
            toRtn["emailContent"] = emailContents.strip()
            return self.returnSuccessResp(additionalDict=toRtn)
        
        @self.app.route(self.formSites["webAppLogout"], methods=["GET", "POST"])
        @login_required
        def logoutEmailAccount()->dict():
            """
                \n@Brief:   Logouts of email
                \n@Returns: {rtnCode: bool} rtnCode - 0 == success, -1 == fail
            """
            self.updateUserObjById(current_user.get_id(), current_user._get_current_object())
            logout_user()
            flash("Successfully logged out!")
            return redirect(self.formSites["webAppLogin"])

    # form submissions get posted here (only accessible)
    def generateFormResultsSites(self):
        formData = {}
        @self.app.route(self.formSites['textForm'], methods=['POST'])
        @login_required
        def createTextForm():
            optDataDict = {} # add keys to be returned at end of post request
            if (not self.initializingStatus):
                url = self.hostAddr + self.formSites['textForm']
                formData = flask.request.get_json()
                proccessData = self.manageFormData(formData)
                current_user.updateEmailLogin(
                    proccessData["firstName"],
                    proccessData["lastName"],
                    emailAddress=proccessData["emailAddress"],
                    password=proccessData["password"]
                )

                # check if receive if sending/receiving message form
                if (proccessData['task'] == "sending"):
                    sendErr = current_user.send("text", proccessData["message"])
                    if (sendErr != None):
                        print(sendErr)
                        # TODO: somehow inform user on webpage of send error (return should have error message)
                
                elif (proccessData['task'] == "receiving"):
                    # responsible for login to get preliminary email data
                    # use ui dropdown to select which email to fully fetch
                    print("receiving")
                    numToFetch = current_user.getNumFetch()
                    preliminaryEmailData = current_user.userReceiveEmailUser(numToFetch)
                    optDataDict = utils.mergeDicts(optDataDict, preliminaryEmailData)
                    # TODO: somehow inform user on webpage of send error (return should have error message)
                    if (optDataDict["error"] == True):
                        print("Failed to receive emails: \n{0}".format(optDataDict["text"]))
                
                elif (proccessData['task'] == "adding-contact"):
                    current_user.addContact(
                        proccessData["firstName"],
                        proccessData["lastName"],
                        proccessData["emailAddress"],
                        proccessData["carrier"],
                        proccessData["phoneNumber"]
                    )
                else:
                    raise Exception("UNKNOWN TASK")

            # return to original site
            return self.returnSuccessResp(optDataDict)

    def manageFormData(self, formData:dict):
        """
            \n@Brief: Helper function that parses ui form for relevant data
            \n@Param: formData - data from the ui's form: {
                firstName: str,
                lastName: str,
                emailAddress: str,
                password: str,
                carrier: str,
                phoneNumber: str,
                message: str,
                task: str
            }
            \n@Note: Not all expected data in `formData` will actually exist
            \n@Returns: Processed version of `formData` (has same keys)
            With values being empty strings ("") if does not exist
        """
        # collect all form information
        expectedDict = {
            "firstName":        "",
            "lastName":         "",
            "emailAddress":     "",
            "password":         "",
            "carrier":          "",
            "phoneNumber":         "",
            "message":          "",
            "task":             ""
        }
        for key in expectedDict.keys():
            expectedDict[key] = formData[key] if utils.keyExists(formData, key) else ""
        return expectedDict

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
        for site in self._urls.keys():
            print(self._getSiteUrl(self._urls[site]))
        print() # newline
    
    def _getSiteUrl(self, site):
        """
            \n@Brief: Helper function that gets full url to a page
            \n@Param: site - the part that comes after the ip/host (localhost/index.html)
        """
        return "{0}{1}".format(self.hostAddr, site)
    
    def returnSuccessResp(self, additionalDict={}):
        """
            Helper function for flask app route request to tell frontend success and additional data
        """
        flaskResponseDict = {'success':True}
        dataDict = utils.mergeDicts(flaskResponseDict, additionalDict)
        return json.dumps(dataDict), 200, {'ContentType':'application/json'}



if __name__ == "__main__":
    # Create all CLI Flags
    # https://docs.python.org/3/library/argparse.html
    parser = argparse.ArgumentParser(description="Start up a web app GUI for the emailing agent")
    parser.add_argument(
        "-p", "--port",
        type=str,
        required=False,
        help="The port to run the emailing web app from",
    )

    # defaults debugMode to false (only true if flag exists)
    parser.add_argument(
        "--debugMode", 
        action="store_true",
        required=False,
        help="Use debug mode for development environments",
    )

    # Actually Parse Flags (turn into dictionary)
    args = vars(parser.parse_args())
    port = args["port"] if utils.keyExists(args, "port") else None
    debugMode = args["debugMode"] if utils.keyExists(args, "debugMode") else False

    ui = WebApp(port=port, isDebug=debugMode)
