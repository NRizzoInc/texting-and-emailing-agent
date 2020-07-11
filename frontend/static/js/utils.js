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