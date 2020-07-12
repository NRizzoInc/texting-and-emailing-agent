"use strict"

export class Dropdown {
    /**
     * @brief Class that helps manage dropdown menus
     * @param {String} dropdownId The id of the '<select>' tag element
     */
    constructor(dropdownId) {
        this._dropdownId = dropdownId
        this._dropdownEl = document.getElementById(this._dropdownId)
        const placeholderExt = "-placeholder"
        this._placeholderId = `${dropdownId}${placeholderExt}`
        const placeholderCandidate = document.getElementById(this._placeholderId)
        this._placeholderExists = placeholderCandidate != null
        console.assert(this._placeholderExists, `Invalid placeholder id. Should be '${this._placeholderId}'`)
        // deep copy if exists
        this._placeholder = placeholderCandidate != null ? placeholderCandidate.cloneNode(true) : ""
        this._data = {} // can be used to hold misc data (like emailList)
    }

    /**
     * @return {String} The id of the <select> element that this class deals with 
     */
    getId() {
        return this._dropdownId
    }

    /**
     * @returns {HTMLSelectElement} The html <select> element retrieved based on id
     */
    getDropdownEl() {
        return this._dropdownEl
    }

    /**
     * @brief Changes all necessary variables to match the new id
     * @param {String} newId The new dropdown id to use
     * @returns {HTMLSelectElement} The newly selected dropdown
     */
    setId(newId) {
        this._dropdownId = newId
        this._dropdownEl = document.getElementById(newId)
        return this.getDropdownEl()
    }

    /**
     * @brief Helper function which adds data to local storage for misc purposes
     * @param {JSON} newData The data to add
     */
    appendData(newData) {
        Object.assign(this._data, this._data, newData)
    }

    /**
     * @returns Data kept within local storage
     */
    getData() {
        return this._data
    }

    /**
     * @brief Helper function that gets 'value' property of selected <option>
     * @returns {{
     *   value: String,
     *   text: String
     * }} Selected option's value & text (what is visible on the page)
     */
    getSelected() {
        const selectedOptIdx = this._dropdownEl.selectedIndex
        const selectedOpt = this._dropdownEl.options[selectedOptIdx]
        return {value: selectedOpt.value, text: selectedOpt.text}
    }

    /**
     * @param text The text contained within the desired <option>
     * @return {HTMLOptionElement} The html <optional> element that contains the desired text 
     */
    getOptionByText(text) {
        for (const opt in this._dropdownEl.options) {
            if (opt.text === text) {
                return opt
            }
        }
    }

    /**
     * @brief Helper function that sets which <option> is selected based on the passed text
     * @param {String} text The selected option's text, which differs from its actual value
     * @returns {String} Selected option's value (different from input text)
     */
    setSelectBoxByText(text) {
        const selectedOpt = this.getOptionByText(text)
        selectedOpt.selected = true
        return selectedOpt.value
    }

    /**
     * @brief Helper function that sets which <option> is selected based on the passed value
     * @note Probably not used as much as setSelectBoxByText
     * @param {String} value The selected option's value (different than what is actually visible on ui)
     * @returns {String} Selected option's text (different from value)
     */
    setSelectBoxByValue(value) {
        this._dropdownEl.value = value
        return this._dropdownEl.text
    }

    /**
     * @brief Helper function that sets which <option> is selected based on the passed index
     * @note Probably not used as much as setSelectBoxByText
     * @param {Number} idx The selected option's index
     * @returns {String} Selected option's value
     */
    setSelectBoxByIndex(idx) {
        this._dropdownEl.options[idx].selected = true
        return this._dropdownEl.options[idx].value
    }

    /**
     * @brief Adds a new <option> to the dropdown menu
     * @note value & text can be the same
     * @param {String} value The desired value & id (not visible)
     * @param {String} text The desired text (visible on ui)
     */
    addOption(value, text) {
        const newOpt = document.createElement("option")
        newOpt.id = value
        newOpt.value = value
        newOpt.text = text
        this._dropdownEl.appendChild(newOpt)
    }

    /**
     * @brief Removes an <option> item from the dropdown based on the passed value (not visible on ui)
     * @param {String} value The value of the <option> to remove
     */
    removeOptionByValue(value) {
        // when added, options' id & value are the same
        const toRemove = document.getElementById(value)
        toRemove.parentNode.removeChild(toRemove)
    }

    /**
     * @brief Removes an <option> item from the dropdown based on the passed text (what is visible on ui)
     * @param {String} text The text of the <option> to remove
     */
    removeOptionByText(text) {
        const toRemove = getOptionByText(text)
        toRemove.parentNode.removeChild(toRemove)
    }

    /**
     * @brief Helper function that removes all options besides placeholder
     */
    clearDropdown() {
        // zero out children & re-add placeholder
        this._dropdownEl.innerHTML = ""
        this._dropdownEl.appendChild(this._placeholder)
        this._data = {}
    }
}