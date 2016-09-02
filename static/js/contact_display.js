"use strict";

function displayPreference(result) {
    // Assign a var to the class name of the <ul> getting updated.
    var prefName = '.' + result.typeButton + 'List';

    // Create an <li> for the new entry that will display.s
    var newDiv = '<li>' + result.value + '</li>';
    console.log(newDiv);

    $(prefName).append(newDiv);

    console.log('\n\nPref updated\n\n');
}

// Grab the id of the button associated with updating the email.
function getPreference(evt) {
    // evt.preventDefault();
    debugger;
    // Grab the name of the button that was clicked.
    // The name of the button corresponds with the column name.
    var typeButton = $(this).attr("id");

    // Grab the id of the contact.
    var relatp_id = this.dataset.relid;

    // Organize the gathered info as an object.
    var formInputs = {
        "value": $("#" + typeButton + "input").val(),
        "id": relatp_id,
        "typeButton": typeButton
    };
        // Send the object to the route /contact-display-handler as a POST request.
        $.post("/contact-display-handler",
           formInputs,
           displayPreference
           );
}

$('button').click(getPreference);