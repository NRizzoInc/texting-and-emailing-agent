function loadContactList(data) {
    let contactList = JSON.parse(data)
    document.getElementById('Contact-List').innerHTML = JSON.stringify(contactList, undefined, 4)
}