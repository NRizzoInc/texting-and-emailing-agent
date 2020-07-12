'use strict';
// This file contains all the button commands

import { parseForm/*, loadEmailDropdown*/ } from "./formProcessor.js"
import { loadResource, writeResizeTextarea, isVisible, postData, getData } from "./utils.js"
import { Dropdown } from "./dropdown.js"

const emailSelDropdown = new Dropdown("email-id-selector", true)
const numFetchSelDropdown = new Dropdown("num-email-fetch-selector", false)
const urlsPath = "/static/urls.json"
// true means show (default everything to that except terminal data & selector)
const defaultDisplayDict = {
    "fname":        true,
    "lname":        true,
    "email":        true,
    "password":     true,
    "message":      true,
    "phone":        true,
    "carrier":      true,
    "textarea":     false,
    "selector":     false,
    "numFetch":     false, // only show this in receiving
    "task":         null
}

$(document).ready( () => {
    // add event listener for each form button element
    const formBtnList = document.getElementsByClassName("myBtn")
    for (const btn of formBtnList) {
        btn.addEventListener("click", () => {
            onFormBtnClick(btn.id)
        })
    }

    // return button
    const returnBtn = document.getElementById("Go-Back-Btn")
    returnBtn.addEventListener("click", () => {
        exitForm()
    })

    const submitBtn = document.getElementById("Submit-Button")
    submitBtn.addEventListener("click", () => {
        // get the selected email id if receiving email
        const isReceiving = document.getElementById('Texting-Form').getAttribute("task") == "receiving"
        // only visible if currently selecting email from dropdown
        const isSelectingEmail = isVisible("email-id-selector")
        submitFormBtn(submitBtn, isReceiving, isSelectingEmail)
    })

    // prevent page from automatically returning to main page from form
    // goes back after form processing complete
    const formEl = document.getElementById("Texting-Form")
    formEl.addEventListener("submit", (event) => {
        event.preventDefault()
    }, true)

    // fill in the dropdown (5-100 incrementing by 5)
    numFetchSelDropdown.fillDropdown(5, 5, 100)
})

/**
 * @brief onClick callback for main page buttons that pulls up the new form page and hide buttons
 * @Note triggered by "Send", "Receive", and "Add Contact" buttons
 */
async function onFormBtnClick(id) {
    // manipulate form page based on which form is desired 
    document.getElementsByClassName('button-wrapper')[0].style.display = "none"
    document.getElementById('Texting-Form-Wrapper').style.display = "block"

    const displayDict = Object.assign({}, defaultDisplayDict) // deep copy
    // set name attributes to match task of button
    // make non-necessary form lines disappear
    if (id == 'text-receive-button') {
        displayDict.fname = false
        displayDict.lname = false
        displayDict.message = false
        displayDict.phone = false
        displayDict.carrier = false
        displayDict.numFetch = true // need to select num emails to fetch
        displayDict.task = "receiving"
        emailSelDropdown.clearDropdown()
    } 
    else if (id == 'text-send-button') {
        displayDict.phone = false
        displayDict.carrier = false
        displayDict.task = "sending"
    }
    else if (id == 'add-contact-button') {
        displayDict.message = false
        displayDict.password = false
        displayDict.task = "adding-contact"
    }
    else {
        console.error("ID Does Not Mean Anything");
    }
    setDisplays(displayDict)
}

/**
 * Helper function to set fields' visibility
 * @param {{
        "fname":        true,
        "lname":        true,
        "email":        true,
        "password":     true,
        "message":      true,
        "phone":        true,
        "carrier":      true,
        "textarea":     false,
        "selector":     false,
        "numFetch":     false,
        "task":         null
    }} displayDict If a field is true, show it
 */
function setDisplays(displayDict) {
    const display = "flex"
    const hide    = "none"
    document.getElementById('firstname-container').style.display =          displayDict.fname     ? display : hide
    document.getElementById('lastname-container').style.display =           displayDict.lname     ? display : hide
    document.getElementById('email-container').style.display =              displayDict.email     ? display : hide
    document.getElementById('password-container').style.display =           displayDict.password  ? display : hide
    document.getElementById('message-container').style.display =            displayDict.message   ? display : hide
    document.getElementById('phone-number-container').style.display =       displayDict.phone     ? display : hide
    document.getElementById('carrier-container').style.display =            displayDict.carrier   ? display : hide
    document.getElementById('terminal-text-container').style.display =      displayDict.textarea  ? display : hide
    document.getElementById('email-id-selector').style.display =            displayDict.selector  ? display : hide
    document.getElementById('num-email-fetch-container').style.display =     displayDict.numFetch  ? display : hide

    // use name attribute in formProcessor to determine some actions
    document.getElementById('Texting-Form').setAttribute("task", displayDict.task)

    // remove any content stored within output textarea
    writeResizeTextarea("terminal-text", "")
}

/**
 * @brief onClick function for the form 'submit' button
 * @param {HTMLButtonElement} submitBtn The button element that was clicked (vanilla form)
 * @param {Boolean} isReceiving True if trying to receive emails
 * @param {Boolean} isSelectingEmail True if email dropdown is showing to allow user to pick email to fetch
 */
async function submitFormBtn(submitBtn, isReceiving, isSelectingEmail) {
    // has id of submit button (need to extrapolate form id parent)
    const triggerID = submitBtn.closest("form").id

    // get url to post to
    const urls = await loadResource(urlsPath)

    // skip form parsing if currently selecting email to fully fetch
    // this is true for sending & receiving (step #1 of "receiving")
    if (!isSelectingEmail) {
        let formAddr;
        if (triggerID.toLowerCase().includes("text")) {
            formAddr = urls.formSites.textForm
        } else if (triggerID.toLowerCase().includes("email")) {
            formAddr = urls.formSites.emailForm
        } else {
            console.error("Error: unknown triggerer case")
        }

        // receiving, but still need to select email id & show corresponding data in box (step #1)
        // hide everything besides dropdown menu & buttons
        // hide immediately or else there is a large delay in hidding it bc parse takes awhile
        if (isReceiving) {
            const displayDict = {}
            const currTask = document.getElementById('Texting-Form').getAttribute("task") // maintain state
            for (const key of Object.keys(defaultDisplayDict)) {
                displayDict[key] = key == "selector"
            }
            displayDict.task = currTask
            setDisplays(displayDict)
        }

        const resData = await parseForm(triggerID, formAddr)
        
        // fill dropdown so user can select which email to show
        if (isReceiving) parseEmailData(resData)
        // wait for another submit (after dropdown option is selected)
        // do not continue if default option is chosen (i.e. have not selected one)
        // this function will be called again and routed to case that does POST request
    } else if (isSelectingEmail && isReceiving) {
        // step #2 of receiving
        // case when need to do POST request to get backend to fully fetch selected email
        const dropdownData = emailSelDropdown.getData()
        const selEmailData = {
            emailId     : emailSelDropdown.getSelected().value,
            idDict      : dropdownData.idDict,
            emailList   : dropdownData.emailList,
            authKey     : dropdownData.authKey
        }

        // post collated data about selected email to allow backend to fully fetch
        const emailDataPage = urls.infoSites.emailData
        const resDict = await postData(selEmailData, emailDataPage)

        // hide everything besides textarea (for emails) & email selector dropdown
        const displayDict = {}
        const currTask = document.getElementById('Texting-Form').getAttribute("task") // maintain state
        for (const key of Object.keys(defaultDisplayDict)) {
            displayDict[key] = key == "selector" || key == "textarea"
        }
        displayDict.task = currTask
        setDisplays(displayDict)

        // write email in textarea
        writeResizeTextarea("terminal-text", resDict.emailContent)
    }
    
    if (!isReceiving) {
        // immediately go back if not receiving
        exitForm()
    }
}

/**
 * @brief Parse email data and add them to dropdown to allow ability to determine which email id to fully fetch
 * @param {{
 *   error: Boolean,
 *   text: String,
 *   authKey: String
 *   idDict: {'<email id>': {idx: '<list index>', desc: ''}, ...},
 *   emailList: [{To, From, DateTime, Subject, Body, idNum, unread}, ...]
 * }} emailData
 * If error, 'error' key will be true & message will be in 'text' key
 * "emailList": list of dicts with email message data
 * "idDict": dict of email ids mapped to indexes of emailMsgLlist
 */ 
async function parseEmailData(emailData) {
    const emailDicts = Object.entries(emailData.idDict)
    const sortedDictList = emailDicts.sort(sortEmailDesc)
    for (const [idNum, infoDict] of sortedDictList) {
        const realVal = idNum // values that map to actual indexes within the 'emailData.emailList' list
        const text = infoDict.desc
        emailSelDropdown.addOption(realVal, text)
    }

    // need to store authKey, emailList, and other important info related to email dropdown
    emailSelDropdown.appendData(emailData)
}

/**
 * @brief Helper function to sort list such that most recent email goes on top of dropdown
 * @param {['<email id>', {idx: '<list index>', desc: ''}]} emailEntryPrev Dictionary containing info about this email
 * @param {['<email id>', {idx: '<list index>', desc: ''}]} emailEntryCurr Dictionary containing info about this email
 * @returns {-1 | 1 | 0}
 * -1 = prev < curr.
 *  1 = prev > curr.
 *  0 = prev == curr.
 */
function sortEmailDesc(emailEntryPrev, emailEntryCurr) {
    // each only has 1 key which is the idNum that can be used to sort
    // the higher the idNUm, the more recent the email was received
    const idNumPrev = Number(emailEntryPrev[0])
    const idNumCurr = Number(emailEntryCurr[0])
    const comparison = idNumPrev - idNumCurr

    // return based on result (reverse to get most recent on top/first)
    if      (comparison < 0)   return  1
    else if (comparison > 0)   return -1
    else if (comparison == 0)  return  0
}

/**
 * @brief Helper function that hides form and brings up the main page
 * @note Usually used by "Go Back" button
 */
function exitForm() {
    document.getElementsByClassName('button-wrapper')[0].style.display = "block"
    document.getElementById('Texting-Form-Wrapper').style.display = "none"
}
