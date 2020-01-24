#!/usr/bin/python3

# This file is responsible for creating a flask Web App UI 
#-----------------------------DEPENDENCIES-----------------------------#
import flask
from flask import Flask, templating, render_template
import socket # used to get local network exposible IP

class WebApp():
    def __init__(self):
        self.host_ip = self.getIP()
        self.host_port = '9999'
        self.host_address = 'https://' + self.host_ip + ':' + self.host_port +'/'
        self.app = Flask(__name__)
        self.app.static_folder = "templates/stylesheets" # change location of where the css stylesheets are

        # create all sites to begin with
        self.generateSites()

        # start up the web app
        self.app.run(host=self.host_ip, port=self.host_port, debug=True)
    
    def getIP(self):
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        return IPAddr

    def generateSites(self):
        '''
            This function is a wrapper around all the other functions which actually create pages.
            Hence, by calling this function all sites will be initialized.
        '''

        @self.app.route('/')
        def createMainPage():
            return render_template("mainPage.html", title="Texting Application Main Page")

if __name__ == "__main__":
    ui = WebApp()