"use strict"

export async function loadResource (toLoad) {
    return new Promise((resolve, reject) => {
        $.getJSON(toLoad, (loadedObj) => {
            // console.log("Loaded: " + JSON.stringify(loadedObj))
            resolve(loadedObj)
        })
    }).catch((err) => "Failed to load resource: " + toLoad + ": " + err)
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
    textDiv.html(text).each((idx, el) => {
        const maxHeight = textDiv.parent().width() // trust me, use width not height
        const desiredHeight = el.scrollHeight
        originalScrollHeight = originalScrollHeight == null ? desiredHeight : originalScrollHeight // keep track of original height
        // if setting to empty text, scroll height should be set to original
        const heightToSet = text == "" ? originalScrollHeight : Math.min(maxHeight, desiredHeight)
        textDiv.outerHeight(heightToSet)
    })
}

/**
 * @brief Helper function that hides form and brings up the main page
 * @note Usually used by "Go Back" button
 */
export function exitForm() {
    document.getElementsByClassName('button-wrapper')[0].style.display = "block"
    document.getElementById('Texting-Form-Wrapper').style.display = "none"
}
