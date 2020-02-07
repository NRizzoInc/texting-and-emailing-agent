function parseForm(formId, formLink) {
    // loop through form to get form key:value pairs 
    let form = document.getElementById(formId);
    let inputTags = form.getElementsByTagName('input');
    let textTags = form.getElementsByTagName('textarea');
    let inputs = [];
    inputs.push(inputTags);
    inputs.push(textTags);
    console.log(inputs)
    
    let formData = {}; // declare json
    for (let tag of inputs) { // iterate through all possible tags
        for (let key of tag) { // iterate through all matches of that tag
            if (key.id != "Submit-Button") {
                console.log("Id: " + key.id + "\nValue: " + key.value)
                let value = document.getElementById(key.id).value
                formData[key.id] = value
            }
        }
    }
    formData = JSON.stringify(formData)
    console.log(formData)

    // POST data to website
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