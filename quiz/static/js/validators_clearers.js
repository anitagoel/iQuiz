// all the validators for the question should be added in response_validators . e.g., if there is a validator
// for question of type MCQ, then it should be added as response_validators['MCQ'] = function() { return true;};
var response_validators = {};

//Response clearer is a dictionary which contains the response clearer for the questions.
//Every question type being implemented can define its response_clearer if there is anything
//special required to clear the response in the form. 
//Note: This JS function will be triggered when the student presses the 'Clear Response' button
//on a particular question. The response clearer should be added as response_clearer['MCQ'] = function (qid) { //Somehow clear the form for the question with given qid //};
var gform;
var response_clearer = {};

/**
 * Add the response_clearer for the MCQ type question.
**/
response_clearer['MCQ'] = 
function (qid) {
	var form =  $("#form-question-" + qid);
	form.find("input").attr({'checked': false});
	gform =form;
};


/**
 * Add the response_clearer for the TFQ type question.
**/
response_clearer['TFQ'] = 
function (qid) {
	var form =  $('#form-question-' + qid);
	form.find('input').attr({'checked': false});
};


/** Currently there are no special validator and clearer**/