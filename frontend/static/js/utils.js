"use strict"

/**
 * @brief Helper function to load .json static files client side
 * @param {String} toLoad url to json file to load (i.e.: /test.json)
 * @returns {JSON} The loaded data
 */
export async function loadResource (toLoad) {
    // have to load data in a string and parse it to make into json
    let loadedJson = {}
    try {
        loadedJson = await $.ajax({
            url: toLoad,
            type: 'GET',
            dataType: "text",
            dataType:'json',
            contentType: 'application/json',
            cache: false, // dont load from cache or get issue if resource is updated
        })
    } catch (err) {
        console.log(`Error loading resource ${toLoad}:`)
        console.log(err)
    }
    return loadedJson
}

/**
 * @brief Helper function that resizes the textarea's height to fit within its parent
 * @param {String} textareaID The html textarea element's id
 * @param {String} text The text to write within the textarea box (that causes size adjustment)
 * Use empty quotes to reset textarea
 */
let originalScrollHeight = null
export function writeResizeTextarea (textareaID, text) {
    const textDiv = $(`#${textareaID}`)
    const tableContainer = $("#Texting-Form-Wrapper")
    textDiv.html(text).each((idx, el) => {
        const maxHeight = tableContainer.height()
        const desiredHeight = el.scrollHeight
        originalScrollHeight = originalScrollHeight == null ? desiredHeight : originalScrollHeight // keep track of original height
        // if setting to empty text, scroll height should be set to original
        const heightToSet = text == "" ? originalScrollHeight : Math.min(maxHeight, desiredHeight)
        textDiv.outerHeight(heightToSet)
    })
}

export function isHidden(elId) {
    return $(`#${elId}`).is(":hidden")
}

export function isVisible(elId) {
    return $(`#${elId}`).is(":visible")
}

export function makeCursorSpin(){
    $("body").css("cursor", "progress")
}

export function makeCursorNormal(){
    $("body").css("cursor", "default")
}


/********************************************** GET & POST FUNCTIONS **********************************************/

/**
 * @brief Helper function that sends POST request containing information about the selected email
 * @param {{
    *   emailId: String,
    *   authKey: String,
    *   idDict: {'<email id>': {idx: '<list index>', desc: ''}, ...},
    *   emailList: [{To, From, DateTime, Subject, Body, idNum, unread}, ...],
    * } | {}} data The data to post for backend to parse
    * @param {String} url The site to post the data to
    * @returns The POST request's response.
    * What you really want is the "emailContent" field as it contains the full email
*/
export async function postData(data, url) {
    const reqResponse = {}
    try {
        const resData = await $.ajax({
            url: url,
            type: 'POST',
            // need both for flask to understand MIME Type
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify(data),
        })
        Object.assign(reqResponse, reqResponse, resData) // merge dicts
    } catch (err) {
        console.log(`Failed to POST to '${url}': ${JSON.stringify(err)}`);
    }
    return reqResponse
}

/**
* @brief Generic GET request wrapper that returns result
* @param {String} url The url to get
* @param {JSON} data (optional) Additional data to pass along in request
* @returns The GET request's response
*/
export async function getData(url, data={}) {
    const reqResponse = {}
    try {
        const resData = await $.ajax({
            url: url,
            type: 'GET',
            // need both for flask to understand MIME Type
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify(data),
        })
        Object.assign(reqResponse, reqResponse, resData) // merge dicts
    } catch (err) {
        console.log(`Failed to GET to '${url}': ${JSON.stringify(err)}`);
    }
    return reqResponse
}
