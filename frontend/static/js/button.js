'use strict';
// This file contains all the button commands

import { parseForm } from "./formProcessor.js"
import { loadResource, writeResizeTextarea, exitForm } from "./utils.js"

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
        submitFormBtn(submitBtn)
    })

    // prevent page from automatically returning to main page from form
    // goes back after form processing complete
    const formEl = document.getElementById("Texting-Form")
    formEl.addEventListener("submit", (event) => {
        event.preventDefault()
    }, true)
})

/**
 * @brief onClick callback for main page buttons that pulls up the new form page and hide buttons
 * @Note triggered by "Send", "Receive", and "Add Contact" buttons
 */
async function onFormBtnClick(id) {
    // manipulate form page based on which form is desired 
    document.getElementsByClassName('button-wrapper')[0].style.display = "none"
    document.getElementById('Texting-Form-Wrapper').style.display = "block"

    // true means show (default everything to that except terminal data)
    const displayDict = {
        "fname":        true,
        "lname":        true,
        "email":        true,
        "password":     true,
        "message":      true,
        "phone":        true,
        "carrier":      true,
        "terminal":     false,
        "task":         null
    }

    // set name attributes to match task of button
    // make non-necessary form lines disappear
    if (id == 'text-receive-button') {
        displayDict.fname = false
        displayDict.lname = false
        displayDict.message = false
        displayDict.phone = false
        displayDict.carrier = false
        displayDict.terminal = true
        displayDict.task = "receiving"
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
        "terminal":     false,
        "task":         null
    }} displayDict If a field is true, show it
 */
function setDisplays(displayDict) {
    const display = "block"
    const hide    = "none"
    document.getElementById('firstname-container').style.display =          displayDict.fname     ? display : hide
    document.getElementById('lastname-container').style.display =           displayDict.lname     ? display : hide
    document.getElementById('email-container').style.display =              displayDict.email     ? display : hide
    document.getElementById('password-container').style.display =           displayDict.password  ? display : hide
    document.getElementById('message-container').style.display =            displayDict.message   ? display : hide
    document.getElementById('phone-number-container').style.display =       displayDict.phone     ? display : hide
    document.getElementById('carrier-container').style.display =            displayDict.carrier   ? display : hide
    document.getElementById('terminal-text-container').style.display =      displayDict.terminal  ? display : hide

    // use name attribute in formProcessor to determine some actions
    document.getElementById('Texting-Form').setAttribute("task", displayDict.task)

    // remove any content stored within output textarea
    writeResizeTextarea("terminal-text", "")
}

/**
 * @brief onClick function for the form 'submit' button
 * @param {HTMLButtonElement} submitBtn The button element that was clicked (vanilla form)
 */
async function submitFormBtn(submitBtn) {
    // has id of submit button (need to extrapolate form id parent)
    const triggerID = submitBtn.closest("form").id

    // get url to post to
    const urls = await loadResource("/static/urls.json")
    
    let formAddr;
    if (triggerID.toLowerCase().includes("text")) {
        formAddr = urls.formSites.textForm
    } else if (triggerID.toLowerCase().includes("email")) {
        formAddr = urls.formSites.emailForm
    } else {
        console.error("Error: unknown triggerer case")
    }
    parseForm(triggerID, formAddr)
}
