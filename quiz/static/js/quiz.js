var current_question_index = 0;
var postponedRequest = {};
var response_timing = {};
//The css classes available for styling the question buttons
var exclusiveQuestionButtonState = ['unvisited', 'not-answered', 'answered', 'marked'];
jumpToQuestion(question_ids[current_question_index]); //Jump to the first question

function len(obj) { return Object.keys(obj).length; }

answered_question_ids.forEach(function(qid, index) {
    changeButtonState(qid, "answered");
    }
);

updateAnswerNumberButtons ();
var submitted = false;

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
			$('#id-question-button-'+ qid).addClass('btn-dark').addClass('unvisited');
			break;
		case exclusiveQuestionButtonState[1]: //Transition from 
			$('#id-question-button-'+ qid).removeClass('btn-dark').removeClass('unvisited').addClass('btn-danger').addClass('not-answered');
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
	console.log("index is changed to :" + current_question_index );
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
        console.log("This is the last question!");
    }
    updateAnswerNumberButtons ();
}

function mark_for_review_and_next(qid){
	save_and_next(qid);
	changeButtonState(qid, "marked");
	updateAnswerNumberButtons ();
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

function jumpToQuestion(qid){
	if (question_ids.indexOf(qid) == -1) return;
	$('#div-question-' + question_ids[current_question_index]).addClass('hidden-question');
	$('#id-question-button-'+ question_ids[current_question_index] ).removeClass('active-button');
	current_question_index = question_ids.indexOf(qid); //update the current question to the given question
	$('#div-question-' + qid).removeClass('hidden-question');
	$('#id-question-button-'+ qid ).addClass('active-button');

	if (!(getButtonState(qid) == "answered" || getButtonState(qid) == "marked")) changeButtonState(qid, "not-answered");
	updateAnswerNumberButtons ();
/** //TODO: Add this part for collecting data for analytics
	if (current_section_start_time == null){
		current_section_start_time = Date.now();
	}
	else{
		//Send the difference between current time and current_section_start_time to serve for the given question_id
		diff = Date.now() - current_section_start_time;
		question_id = question_ids[last_question_id_index];
		request = [question_id, {viewing_time: diff}]; 
		saveResponseAjax(request);
		//Now change the current_section_start_time to now!
		current_section_start_time = Date.now();
	}
**/
}


function show_all_questions_in_palette(){
	//Function shows all the question palette buttons back, and hides the button.
	$('#div-question-palette').find('.question-button').prop('disabled', false).removeClass('disabled-palette-button');
	$('#palette-back-button').css('visibility', 'hidden').css('opacity', '0');

}

function show_questions_in_palette(type){
	//Shows the given type of questions in the palette
	console.log(type);
	valid_types = ['answered','not-answered', 'unvisited', 'marked'];
	if (valid_types.indexOf(type) == -1) return;

	$('#palette-back-button').css('visibility', 'visible').css('opacity', '1');;
	console.log($('#div-question-palette').find('.question-buttons'));
	$('#div-question-palette').find('.question-button').prop('disabled', true).addClass('disabled-palette-button');
	$('#div-question-palette').find('.question-button.' + type).prop('disabled', false).removeClass('disabled-palette-button');
}