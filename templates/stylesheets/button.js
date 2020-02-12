// This file contains all the button commands
function buttonPostRequest(pageToRequest, id) {
    // trigger new page and hide buttons
    $.post(pageToRequest, function onSuccess () {
        document.getElementsByClassName('button-wrapper')[0].style.display = "none"
        document.getElementById('Texting-Form-Wrapper').style.display = "block"
        
        if (id == 'text-receive-button') {
            document.getElementById('message-container').style.display = 'none'
            // TODO: show text results (terminal on page)
        } 
        else if (id == 'text-send-button') {
            
        }
    })
}