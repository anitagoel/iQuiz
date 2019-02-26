//Handles the redirection by showing a modal like div with given message
var redirectHandler = function (href, message, time){
    //check if already redirect div is there
    message = message || 'Redirecting...';
    time = time || 1000;
    div = $('#redirect-div');
    if (div[0] != null){
        clearTimeout(div[0].timeout);
        div[0].parentElement.removeChild(div[0]); //Remove the element
    }
        //Blur the whole content-body div.
        $('#content-body').css('filter','blur(5px)');
        //Add a div on the body
        new_div = document.createElement('div');
        new_div.id = 'redirect-div';
        new_div.classList.add('center-body');
        new_div.innerHTML = '<span>' + message + '</span>';
        document.body.appendChild(new_div);
        if (!(time == null)) {
            new_div.timeout = setTimeout(function() {
                window.location.href = href;
            }, time);
        }
}