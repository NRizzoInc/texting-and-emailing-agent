# Description

* This repo contains a command line email client utility that can also send text messages
  * Advantages: 
    * No need to use a web browser to access your mail
    * Can access/send mail on a GUI-less or server environment
    * Can text someone from your laptop without needing to pull out your phone
  * Disadvantages:
    * Requires python on local machine to run it
* Non-developer (laypeople) who do not have python, but stil want to text people can use the web app version of this code
  * Currently running at [`http://72.68.204.143:65501/`](http://72.68.204.143:65501/) (contact me at `rizzo.n@northeastern.edu` if site is down)
  * Advantages:
    * Can text people from anywhere
    * Do not need to have any special software on your computer to use it
  * Disadvantages:
    * Requires you to register & login to an account before sending a text (need to keep data private)
* see the [`running code section`](#running-code) for how to actually use the code in this repo

## Setup

On Linux: `sudo ./install/setup.sh a`
On Windows (with Git Bash): `./install/setup.sh a`

Create dummy login to perform email operations:

1. You will need to either get access to the dummy email account I set up or make your own
    *  (only contributors will get access to mine)
2. To make your own: 
    1. Create a low security gmail account (or else email app cannot get past default security)
        1. Create the account -> click on your name icon on the top right of gmail's screen -> `Manage your Google Account`
        2. On left side click `security` -> scroll down to find `Less secure app access` -> `Turn on access`
        3. Note: do NOT do this with your actual gmail account as it will leave you vulnerable
    1. Create a file called `defaultLogin.json` at `backend/emailData/defaultLogin.json`
    2. Insert the following json and modify the email address & password to match your gmail account made with low security

``` json
{
  "dummy-email": {
      "email-address": "<insert your email>",
      "password": "<insert your password>"
  }
}
```

That's it! Done!!
(I tried to make it as straightforward as possible)

## Running Code

[**Do the setup before moving on**](#setup)

If you do not want to deal with starting and stopping the python virtual environment, look no further!

The `start.sh` bash script within this directory is meant to help you run the python code while automatically

using the virtual environment so your global python system is not messed up

### Starting Code with Start Script (`start.sh`)

* To run the email agent (the command line version of the web app): `<path to this dir>/start.sh --mode cli`
* To run the web app: `<path to this dir>/start.sh --mode web`
* Additional help can be found at `<path to this dir>/start.sh --help`
* All command line flags used from the bash scripts will transfer over to the python scripts
* Send text without requiring further input after executing: `./start.sh --mode cli --send -f <receiver firstname> -l <receiver lastname> --no-wait -x 'text' -m "<the message you want to text>"`

### Starting Code Directly (with Python)

**(Not recommended as you will have to deal with virtual environment shenanigans yourself)**

1. Activate the virtual environment (located in `emailEnv` directory after install)
2. Run either the GUI (`webApp`) or command line version (`emailCLIManager`)

  > GUI: `python <path to repo root>/backend/src/webApp/webApp.py`

  > Command Line: `python <path to repo root>/backend/src/emailing/emailCLIManager.py`

## How to Use (Flags)

1. To send messages (either text or emails) you need to [add a contact to your personalized contact list](#to-add-a-contact-3-ways)

2. To run the code:
  1. Easiest Way: [`start.sh`](#starting-code-with-start-script-startsh)
  2. Manual Way: [`python`](#starting-code-directly-with-python)

3. Use `--help` flag with either start option to understand your options

4. Once inside the program it will guide you step by step **FYI (y = yes, n = no)**

## To Add a Contact (3 ways)

1. Try to send a message to a user who does not exist. The program will ask you if you want to add the contact to the list and go through it with you step by step.

2. To skip directly to the add contact step, simply use the `emailCLIManager` flag `--add-contact`

3. Via the web app -- click "Add Contact"

## To Update the Contact List (2 ways)

1. Try to send a message to a user who already exist. The program will ask you if you want to update the contacts info and go through it with you step by step.

2. To skip directly to the add contact step, simply the `emailCLIManager` flag `--update-contact`

## To Make Code Executable on a Computer Without Python

**TODO:** This needs to be updated when better scripted up

1. In your terminal type: `pip install pyinstaller`

2. Wait for it to finish installing and then type: `pyinstaller emailAgent.py`

3. This will create a bunch of files and folders (primarily the 'dist' folder), including a .exe, which you can run on a computer that operates on a similar platform

4. To run the executable, change directories to `email_messages/dist/emailAgent/`. Then simply type `emailAgent.exe` and everything will run as if it was python!!
