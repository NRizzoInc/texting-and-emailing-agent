'use strict';

export function parseForm(formId, formLink) {
    // loop through form to get form key:value pairs 
    const form = document.getElementById(formId);
    const inputs = [] 
    inputs.push(form.getElementsByTagName("input"))
    inputs.push(form.getElementsByTagName("textarea"))
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
    
    // POST data to website
    $.ajax({
        url: formLink,
        type: 'POST',
        // need both for flask to understand MIME Type
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify(formData),
        success: (msg) => {
            console.log("Successfully posted: " + JSON.stringify(msg));
        },
        error: (err) => {
            console.log("Failed to post: " + err);
        }
    })
} // end of parse form function
