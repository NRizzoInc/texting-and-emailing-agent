'use strict';

import { loadResource } from "./utils.js"

export async function parseForm(formId, formLink) {
    // loop through form to get form key:value pairs 
    const form = document.getElementById(formId);
    const inputs = [] 
    inputs.push(Array.from(form.getElementsByTagName("input")))
    inputs.push(Array.from(form.getElementsByTagName("textarea")).filter(el => !el.readOnly))
    const formData = {};
    
    // get all inputs to form
    for (const tags of inputs) {
        for (const div of tags) {
            if (div.id != "Submit-Button") {
                // dont include the submit button
                formData[div.id] = div.value
            }
        }
    }

    // determine if adding contact, sending, or receiving message
    formData.task = form.getAttribute("task")
    if (!formData.task) {
        console.error("No such valid task attribute")
    }
    
    // POST data to website (waits for backend to finish processing form data)
    await postFormData(formLink, formData)

    // return to main text/email site
    if (formData.task == "receiving") {
        // if receive, show data in box
        const terminalTextId = "terminal-text"
        const terminalText = await getTerminalPage()
        // autosize height/width to fit text
        const textDiv = $(`#${terminalTextId}`)
        textDiv.html(terminalText).each((idx, el) => {
            const maxHeight = textDiv.parent().width()
            const desiredHeight = el.scrollHeight
            const heightToSet = Math.min(maxHeight, desiredHeight)
            textDiv.outerHeight(heightToSet)
        })

    } else {
        // immediately if not receive
        window.history.back()
    }

} // end of parse form function

async function getTerminalPage() {
    const urls = await loadResource("/static/urls.json")
    const terminalPage = urls.infoSites.terminalText
    let terminalData = {}
    try {
        terminalData = await $.ajax({
            url: terminalPage,
            type: 'GET',
            // need both for flask to understand MIME Type
            dataType: "json",
            contentType: "application/json",
        })
        terminalData = terminalData.terminalData
    } catch (err) {
        console.log(`Error getting terminal page: ${JSON.stringify(err)}`)
    }

    return terminalData
}

async function postFormData(formLink, formData) {
    let postRtnCode = ""
    try {
        postRtnCode = await $.ajax({
            url: formLink,
            type: 'POST',
            // need both for flask to understand MIME Type
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify(formData),
        })
    } catch (err) {
        console.log(`Failed to post to '${formLink}': ${JSON.stringify(err)}`);
    }

    return postRtnCode
}
