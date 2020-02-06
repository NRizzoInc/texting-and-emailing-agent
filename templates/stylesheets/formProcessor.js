function parseForm(formId, formLink) {
    let form = document.getElementById(formId);
    $.ajax({
        url: formLink,
        type: 'POST',
        data: {
            email: 'email@example.com',
            message: 'hello world!'
        },
        success: function (msg) {
            alert(msg);
        }         
    });
} // end of parse form function