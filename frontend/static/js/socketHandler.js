"use strict"

const connectingUrl = "http://" + document.domain + ":" + location.port
const socket = io.connect(connectingUrl);
/**
 * @brief Creates a socket event listener that calls the desired callback when flask sends a desired message
 * @param {String} event The flask message to wait for
 * @param {Function} callback A callback function that takes one argument -- response (JSON)
 * @param {Boolean} onlyOnce (optional - default = true) Only triggers the event listener once
 */
export function createSocketListener(event, callback, onlyOnce=true) {
    if (onlyOnce) {
        socket.once(event, callback)
    } else {
        socket.on(event, callback)
    }
}
