import { writeResizeTextarea } from "./utils.js"


export function resizeContactList() {
    const contactListId = "contact-list-textarea"
    const contactListArea = $(`#${contactListId}`)
    const contactListEl = contactListArea[0]
    const textToWrite = contactListArea.innerHTML
    console.log(`textToWrite: ${textToWrite}`)
    writeResizeTextarea(contactListId, textToWrite)
}