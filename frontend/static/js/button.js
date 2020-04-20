'use strict';
// This file contains all the button commands

import { parseForm } from "./formProcessor.js"

$(document).ready( () => {
    // add event listener for each form button element
    const formBtnList = document.getElementsByClassName("myBtn")
    for (const btn of formBtnList) {
        btn.addEventListener("click", () => {
            buttonPostRequest(btn.id)
        })
    }

    const submitBtn = document.getElementById("Submit-Button")
    submitBtn.addEventListener("click", () => {
        submitFormBtn(submitBtn)
    })
})

// get id new page and hide buttons
async function buttonPostRequest(id) {
    // manipulate form page based on which form is desired 
    document.getElementsByClassName('button-wrapper')[0].style.display = "none"
    document.getElementById('Texting-Form-Wrapper').style.display = "block"

    // set name attributes to match task of button
    // make non-necessary form lines disappear
    if (id == 'text-receive-button') {
        document.getElementById('firstname-container').style.display = 'none'
        document.getElementById('lastname-container').style.display = 'none'
        document.getElementById('message-container').style.display = 'none'
        document.getElementById('phone-number-container').style.display = 'none'
        document.getElementById('carrier-container').style.display = 'none'
        // use name attribute in formProcessor to determine some actions
        document.getElementById('Texting-Form').setAttribute("task", "receiving")
    } 
    else if (id == 'text-send-button') {
        document.getElementById('phone-number-container').style.display = 'none'
        document.getElementById('carrier-container').style.display = 'none'
        // use name attribute in formProcessor to determine some actions
        document.getElementById('Texting-Form').setAttribute("task", "sending")   
    }
    else if (id == 'add-contact-button') {
        // hide non-neccessary stuff for adding a new contact
        document.getElementById('message-container').style.display = "none"
        document.getElementById('password-container').style.display = "none"
        // use name attribute in formProcessor to determine some actions
        document.getElementById('Texting-Form').setAttribute("task", "adding-contact")   
    }
    else {
        console.error("ID Does Not Mean Anything");
    }
}

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

async function loadResource (toLoad) {
    return new Promise((resolve, reject) => {
        $.getJSON(toLoad, (loadedObj) => {
            // console.log("Loaded: " + JSON.stringify(loadedObj))
            resolve(loadedObj)
        })
    }).catch((err) => "Failed to load resource: " + toLoad + ": " + err)
} 