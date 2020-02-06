// This file contains all the button commands
function buttonPostRequest(pageToRequest) {
    // trigger new page and hide buttons
    $.post(pageToRequest, function onSuccess () {
        document.getElementsByClassName('button-wrapper')[0].style.display = "none"
        document.getElementById('Texting-Form').style.display = "block"
    })
}