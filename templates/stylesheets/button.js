// This file contains all the button commands
function buttonPostRequest(pageToRequest, id) {
    // trigger new page and hide buttons
    $.post(pageToRequest)

    // manipulate form page based on which form is desired 
    document.getElementsByClassName('button-wrapper')[0].style.display = "none"
    document.getElementById('Texting-Form-Wrapper').style.display = "block"
    
    if (id == 'text-receive-button') {
        document.getElementById('message-container').style.display = 'none'
        document.getElementById('phone-number-container').style.display = 'none'
        document.getElementById('carrier-container').style.display = 'none'
        // use name attribute in formProcessor to determine some actions
        document.getElementById('Texting-Form').setAttribute("name", "receiving")
    } 
    else if (id == 'text-send-button') {
        document.getElementById('phone-number-container').style.display = 'none'
        document.getElementById('carrier-container').style.display = 'none'
        // use name attribute in formProcessor to determine some actions
        document.getElementById('Texting-Form').setAttribute("name", "sending")   
    }
    else if (id == 'add-contact') {
        // hide non-neccessary stuff for adding a new contact
        document.getElementById('message-container').style.display = "none"
        document.getElementById('password-container').style.display = "none"
        // use name attribute in formProcessor to determine some actions
        document.getElementById('Texting-Form').setAttribute("name", "adding-contact")   
    }
    else {
        console.error("ID Does Not Mean Anything");
    }
}