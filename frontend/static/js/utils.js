"use strict"

export async function loadResource (toLoad) {
    return new Promise((resolve, reject) => {
        $.getJSON(toLoad, (loadedObj) => {
            // console.log("Loaded: " + JSON.stringify(loadedObj))
            resolve(loadedObj)
        })
    }).catch((err) => "Failed to load resource: " + toLoad + ": " + err)
}
