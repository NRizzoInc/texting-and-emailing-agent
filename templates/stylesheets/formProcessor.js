function parseForm(formId, formLink) {
    // loop through form to get form key:value pairs 
    let form = document.getElementById(formId);
    console.log(form)
    console.log(JSON.stringify(form['1']))
    let formData = JSON.stringify(form);
    console.log(formData)
    $.ajax({
        url: formLink,
        type: 'POST',
        data: formData,
        dataType: "json",   
        contentType: "application/json",
        success: function (msg) {
            console.log(msg);
        },
        error: function (msg) {
            // console.log(msg);
        }
    });
} // end of parse form function