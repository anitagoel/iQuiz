
var current_section_start_time = null;   //used by sending time spent on a question to server

function initialize_quiz() { 
	jumpToQuestion(question_ids[current_question_index]); //Jump to the first question
	answered_question_ids.forEach(function(qid, index) {
	    changeButtonState(qid, "answered");
	    }
	);
	updateAnswerNumberButtons ();
	
	$("#questions-slider-nav").on('input', function () {
		jumpToQuestion(question_ids[this.value-1]);
	});
}

function len(obj) { return Object.keys(obj).length; }

var setTimeForQuestion = (qid) => {
	var question_timer = document.querySelector(`.question-timer[target="${qid}"]`);
	var question_rem_time = question_time_limits[qid];
	if (question_rem_time == -1)
		question_timer.innerHTML = 'No time limit';
	else {
		question_timer.innerHTML = question_rem_time
		var question_time_interval = setInterval(() => {
			question_rem_time = question_rem_time - 1;
			if(question_rem_time<0){
				clearInterval(question_time_interval);
				save_and_next(qid);
				if(question_ids.indexOf(qid) == (question_ids.length-1)){
					console.log("Force Submit")
					force_submit();
				}
				return;
			}
			question_timer.innerHTML = question_rem_time;
		}, 1000)
	}
}


function submit() {
	var ok = confirm("Are you sure you want to submit?");
	if (ok){
		force_submit();
	}
}
function force_submit(){
	setTimeout(function() {
		redirectHandler('/student', 'You are being redirected to homepage...', 1000);
	}, 30000); //definitely redirect to homepage after 30 seconds.
	send_time_spent_details(1);
	
	message = 'The quiz is being submitted... <br/>Please wait!'
	redirectHandler('#', message, null);
	sendPostponedRequests(); //send postponed requests.
	setTimeout(check_submit, 3000); //Call check_submit after 3 seconds.
}

function check_submit(){
	if (len(postponedRequest) == 0)  {
		href = '/student';
		message = 'The quiz has been submitted!'
		redirectHandler(href, message, 1000);
		saveResponseAjax(["submit-request",{submit:"1"}]);
	}

	else {
		setTimeout(check_submit, 2000); //Call check_submit every 2s if not submitted
	}
}

function changeButtonState(qid, state){
	switch (state){
		case exclusiveQuestionButtonState[0]:
			$('#id-question-button-'+ qid).addClass('btn-blue-grey').addClass('unvisited');
			break;
		case exclusiveQuestionButtonState[1]: //Transition from 
			$('#id-question-button-'+ qid).removeClass('btn-blue-grey').removeClass('unvisited').addClass('btn-danger').addClass('not-answered');
			break;
		case exclusiveQuestionButtonState[2]:
			$('#id-question-button-'+ qid).removeClass('btn-info').removeClass('marked').removeClass('btn-danger').removeClass('not-answered'); //Remove marked and not-answered classes
			$('#id-question-button-'+ qid).addClass('btn-success').addClass('answered');
			break; //Add answered classes
		case exclusiveQuestionButtonState[3]:
			$('#id-question-button-'+ qid).removeClass('btn-success').removeClass('answered').removeClass('btn-danger').removeClass('not-answered'); //Remove marked and not-answered classes
			$('#id-question-button-'+ qid).addClass('btn-info').addClass('marked');
			break;
	}
}

function updateAnswerNumberButtons () {
	//Function to update the number of unvisited, answered, not-answered and marked questions.
	//This number is equal to one less the number of buttons with class answered, not-answered...etc respectively. (Subtracting one due to presence of one extra buttons with same class in example grid)
		$('#button-number-answered').text($('#div-question-palette').find('.answered').length);
		$('#button-number-not-answered').text($('#div-question-palette').find('.not-answered').length);
		$('#button-number-unvisited').text($('#div-question-palette').find('.unvisited').length);
		$('#button-number-marked').text($('#div-question-palette').find('.marked').length);
}

function getButtonState(qid){
	if ($('#id-question-button-'+ qid).hasClass('visited')) return "visited";
	else if ($('#id-question-button-'+ qid).hasClass('answered')) return "answered";
	else if ($('#id-question-button-'+ qid).hasClass('marked')) return "marked";
	else if ($('#id-question-button-'+ qid).hasClass('not-answered')) return "not-answered";
	else return "None";

}
/**
 * The function validate_data searches if any validate_data function for given qid is defined.
 * The expected name of the function is validate_data_
**/
function validate_data(data, qid){
    validator = response_validators[question_types[qid]];
    if (validator)
        return validator(data);
    return data
}


function save_and_next(qid){
	//Mark as visited
	current_question_index = question_ids.indexOf(qid);
	//Perform following only if the form is actually filled/question is answered
	var form = $('#form-question-' + qid);
	//validate that required fields are there before sending the response
	//Serialize the form associated with given question_id
	data = $('#form-question-' + qid).serialize();
	if (data && validate_data(data, qid)){
        changeButtonState(qid, "answered");
        request = [qid, data];
        success = saveResponseAjax(request);
    }

    if (current_question_index < question_ids.length - 1) {
        jumpToQuestion(question_ids[current_question_index+1]);
    }
    else{
    	// jumpToQuestion(question_ids[0]);
    }

    updateAnswerNumberButtons ();
}

function mark_for_review_and_next(qid){
	// save_and_next(qid);
	changeButtonState(qid, "marked");
	updateAnswerNumberButtons ();
}

function clear_response(qid){
	//Cleares the response of the student for the given qid
	current_question_state = getButtonState(qid);
	var form = $('#form-question-' + qid);
	form[0].reset(); //reset the form and return
	//Call the response_clearer_function if exists for the given question type
	clearer_function = response_clearer[question_types[qid]];
	if (clearer_function) clearer_function(qid); //call the clearer_function if exists

	form.find("input").prop("checked", false);
	if (current_question_state == "not-answered" || current_question_state == "unvisited") {
		return;
	}
	
	data = {"clear_response": qid};
	request = [qid, data];
	saveResponseAjax(request);
	//Reset the form for the given qid
	$('#form-question-' + qid).trigger("reset");
	changeButtonState(qid, "not-answered");
	console.log("Response cleared for Question Id: " + qid);
}

function saveResponseAjax(request){
	question_id = request[0];
	data = request[1];
	success = false;

	$.ajax({
    type: "POST",
    url: "quiz/save_response",
    data: data,
    success: function(response) {
     	if ('error' in response){
     		redirectHandler('/student', 'Some error has occurred! Please report this to admin.', 5000);
     	}

     	if ('redirect' in response) {
    		//Redirect request is received, handle it
    		href = response['redirect'];
    		message = '';
    		time = 1000;
    		if ('message' in response) message = response['message'];
    		if ('time' in response) time = response['time'];
    		redirectHandler(href, message, time);
    	}
     	success = true;
    },
    error: function(){
    	postponedRequest[question_id] = data;
    	pollServerConnection(); //Keep polling the server until successful
    }
    });
	return success;
}

var sendingPostponedRequests = false; //Used to see if sendPostponedRequests function is already called or not.

// TODO: Combine all the postponed requests into ONE single request for better response time
function sendPostponedRequests(){
	if (!sendingPostponedRequests){
		sendingPostponedRequests = true;
		//The function tries to send all the failed ajax requests.
		for (question_id in postponedRequest){
			data = postponedRequest[question_id];
			delete postponedRequest[question_id];
			saveResponseAjax([question_id, data]);
		}
	}
	sendingPostponedRequests = false;
}

function pollServerConnection() {
	$.ajax({
    type: "POST",
    url: "quiz/save_response",
    data: 'checking-connection=True',
    success: function(response) {
		$('#offline').hide();
		sendPostponedRequests();
		return;
    },
    error: function(){
		$('#offline').show();
		console.log('Offline');
		setTimeout(pollServerConnection, 5000);
    }
    });
}


function switchQuestionView(qid){

	index = question_ids.indexOf(qid);
	if (index == -1) return;
	//Update the slider for navigation
	$("#questions-slider-nav").val(index+1);

	$('#div-question-' + question_ids[current_question_index]).addClass('hidden-question').removeClass('animated fadeIn');;
	$('#id-question-button-'+ question_ids[current_question_index] ).removeClass('active-button');
	current_question_index = index; //update the current question to the given question
	$('#div-question-' + qid).removeClass('hidden-question').addClass('animated fadeIn');
	$('#id-question-button-'+ qid ).addClass('active-button');

	if (!(getButtonState(qid) == "answered" || getButtonState(qid) == "marked")) changeButtonState(qid, "not-answered");
	updateAnswerNumberButtons ();
}


function send_time_spent_details(qid){
	current_question_id = question_ids[current_question_index];

	//TODO: Check this part.

	if (current_section_start_time == null){
		current_section_start_time = Date.now();
		return;
	}
	else{

		//Send the difference between current time and current_section_start_time to serve for the given question_id
		diff = (Date.now() - current_section_start_time)/1000;  	// in seconds
		question_id_with_tag = current_question_id + "_time_spent" ;  // We add the _time_spent so there is no overriding of the postponed requests by these requests.
		earlier_request = postponedRequest[question_id_with_tag];
		if (earlier_request){
			earlier_request[viewing-time-duration] += diff;   //add the duration of time if the request is postponed.
			return;
		}

		if (diff<1){
			return; // Ignore if less than 1 second TODO: Was it right thing to do? Should we create a dictionary to store the time locally and send when its beyond a fixed time?
		}
		request = [question_id_with_tag, {"viewing-time-qid": current_question_id, "viewing-time-duration": diff}]; 
		saveResponseAjax(request);
		//Now change the current_section_start_time to now!
		current_section_start_time = Date.now();
	}
}


function send_time_spent_details_ajax(request) {
	question_id = request[0];
	data = request[1];
	success = false;
	$.ajax({
    type: "POST",
    url: "quiz/save_time_spent",
    data: data,
    success: function(response) {
     	if ('error' in response){
     		redirectHandler('/student', 'Some error has occurred! Please report this to admin.', 5000);
     	}
    },
    error: function(){
    	setTimeout(function() { send_time_spent_details(request); }, 5000); // retry after 5 seconds
    	pollServerConnection(); //Keep polling the server until successful
    }
    });
	return success;

}


// the array contains the function which are called when jumpToQuestion is called. Note that switchQuestionView modifies
// the current_question_id, hence it is called at last (might be used by previous functions)

jumpToQuestionFunctions = [send_time_spent_details, switchQuestionView, setTimeForQuestion];  

function jumpToQuestion(qid){
	//Call each function from jumpToQuestionFunctions array with qid.
	for (index in jumpToQuestionFunctions){
		jumpToQuestionFunctions[index](qid);
	}
}


function show_all_questions_in_palette(){
	//Function shows all the question palette buttons back, and hides the button.
	$('#div-question-palette').find('.question-button').prop('disabled', false).removeClass('disabled-palette-button').removeClass('active-button');
	$('#palette-back-button').css('visibility', 'hidden').css('opacity', '0');
	qid = question_ids[current_question_index];
	$('#id-question-button-'+ qid ).addClass('active-button');

}

function show_questions_in_palette(type){
	//Shows the given type of questions in the palette
	console.log(type);
	valid_types = ['answered','not-answered', 'unvisited', 'marked'];
	if (valid_types.indexOf(type) == -1) return;
	$('#palette-back-button').css('visibility', 'visible').css('opacity', '1');;
	$('#div-question-palette').find('.question-button').prop('disabled', true).addClass('disabled-palette-button').removeClass('active-button');
	$('#div-question-palette').find('.question-button.' + type).prop('disabled', false).removeClass('disabled-palette-button').addClass('active-button');
}


/**
 *Function for countdown timer.
**/
function timer_update() {
  var now = Date.now();
  var distance = countDownTime - now;

  // Time calculations for days, hours, minutes and seconds
  var days = Math.floor(distance / (1000 * 60 * 60 * 24)); //Will not days, hopefully there will be none!!
  var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  //Ignore days as it must be zero (hopefully!)
  var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
  var seconds = Math.floor((distance % (1000 * 60)) / 1000);
  hours_str = ("0" + hours).slice(-2);
  minutes_str = ("0" + minutes).slice(-2);
  seconds_str = ("0" + seconds).slice(-2);
  if (hours>0) {
  document.getElementById("timer-time").innerHTML = hours_str + ':' + minutes_str + ":" + seconds_str;
	}
	else {
		document.getElementById("timer-time").innerHTML =  minutes_str + ":" + seconds_str;
	}
  if (hours == 0 && minutes<5) {
  	if (!($('#timer').hasClass('btn-warning'))) $('#timer').addClass('btn-warning').addClass('animated jello');
  }
  if (hours == 0 && minutes<1) {
  	if (!($('#timer').hasClass('btn-danger'))) $('#timer').removeClass('btn-warning').removeClass('jello').addClass('btn-danger').addClass('jello');
  }
  if (distance <= 0) {
  	//Submit the quiz and exit
    clearInterval(timerStartedInterval);
    document.getElementById("timer-time").innerHTML = "00:00:00";
    force_submit();
  }
}