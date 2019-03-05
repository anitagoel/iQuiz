//Hide the screen while the quiz is being loaded, for maximum of 10 seconds.
var loadingLock = function (href, message, time){
    if (!time) {
      //We won't lock the screen if time is not provided.
      return;
    }
    message = message || 'Loading...';
    time = time || 1000;
    div = document.getElementById('lock');
    //Blur the whole content-body div.
    document.getElementById('content-body').style.filter = 'blur(5px)';
    //Add a div on the body
    div.classList.add('center-body');
    div.innerHTML = '<span>' + message + '</span>';
    if (!(time == null)) {
        div.timeout = setTimeout(function() {
            loadingLockRelease();
        }, time);
    }
}

function loadingLockRelease(){
  //Function removes the lock div, cancels the div timeout if exists, and removes the blur from the content body.
  //Start the timer.
  loading = false;
  div = document.getElementById('lock');
  div.remove();
  document.getElementById('content-body').style.filter = 'blur(0px)';
  if (time_left){
    //If there is time_left variable, then proceed with starting the countdown
    var countDownTime = Date.now() + time_left; //In milliseconds
    // Update the count down every 1 second
    timerStartedInterval = setInterval(timer_update, 1000);
  }
}
