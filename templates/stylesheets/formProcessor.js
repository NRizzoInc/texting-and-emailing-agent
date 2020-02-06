function parseForm(formId, formLink) {
    let formData = JSON.stringify($("#myForm").serializeArray());
    console.log("posting!")
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
            console.log(msg);
        }
    });
} // end of parse form function