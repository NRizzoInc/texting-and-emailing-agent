'use strict';

/**
 * @brief Helper function that reads through the form data and collates it to be sent to backend
 * @param {String} formId The form's html element's name
 * @param {String} formLink The URL to the form being used (i.e. /textForm or /emailForm)
 * @returns {JSON} Response data from backend POST request
 */
export async function parseForm(formId, formLink) {
    // loop through form to get form key:value pairs 
    const form = document.getElementById(formId);
    const inputs = [] 
    inputs.push(Array.from(form.getElementsByTagName("input")))
    inputs.push(Array.from(form.getElementsByTagName("textarea")).filter(el => !el.readOnly))
    const formData = {
        "carrier": document.getElementById("carrier-selector").getAttribute("value") // value is updated onChange
    }

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
    const resData = await postFormData(formLink, formData)
    return resData
} // end of parse form function

/**
 * @brief Helper function that posts the collated form data and gives back an "authKey" for later retrieval
 * @param {String} formLink The url to post the data to
 * @param {JSON} formData The data to post
 * @returns {reqResponse} Contains the backend's json response to post request
 * Contains some stuff like authKey UUID for retrieving backend's processed data or the data itself
 */
async function postFormData(formLink, formData) {
    const reqResponse = {terminalData: null, authKey: null}
    try {
        const resData = await $.ajax({
            url: formLink,
            type: 'POST',
            // need both for flask to understand MIME Type
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify(formData),
        })
        Object.assign(reqResponse, reqResponse, resData) // merge dicts
    } catch (err) {
        console.log(`Failed to post to '${formLink}': ${JSON.stringify(err)}`);
    }
    return reqResponse
}
