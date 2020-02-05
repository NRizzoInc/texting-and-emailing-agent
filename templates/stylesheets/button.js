// This file contains all the button commands
function buttonPostRequest(pageToRequest) {
    // trigger new page and hide buttons
    $.post(pageToRequest, function onSuccess () {
        // document.getElementsByClassName('.button-wrapper').style.visibility = 'hidden'
        console.log(document.getElementsByClassName('button-wrapper'))
        document.getElementsByClassName('button-wrapper')[0].style.visibility = "hidden"
    })
}