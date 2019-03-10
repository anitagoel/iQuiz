//Script for form submission using AJAX
$("#form_id").submit(function(e) {
    e.preventDefault(); // avoid to execute the actual submit of the form.
    var form = $(this);
    var url = form.attr('action');
    var data = form.serialize();
    replace_content(url, {'form-save-request' : true},  data);
});

//The script containing the function to help with loading the Pagedown editor


var createEditor = function(el) {
        var selectors = {
            input : el.id,
            button : el.id + "_wmd_button_bar",
            preview : el.id + "_wmd_preview",
        };
        var editor = new Markdown.Editor(converter, "", selectors);
        editor.run();
};

var options_table = document.getElementById("form-table");
//get the html for the options
var option_html = `
				  	<th><input type="radio" name="correct_option" value="{option_id}"> <label for="id_draft_options_{option_number}">Option {option_number}</label></th>
				  	<td>
					  	<div class="wmd-wrapper" id="id_draft_options_{option_number}-wmd-wrapper">
					    	<div class="wmd-panel">
						        <div id="id_draft_options_{option_number}_wmd_button_bar"></div>
						      	 <textarea  class="wmd-input" cols="40" id="id_draft_options_{option_number}" name="draft_options" rows="3" required></textarea>
					    	</div>
					    	<p class="wmd-preview-title">
					        	<small>HTML Preview</small>
					    	</p>
					    	<div id="id_draft_options_{option_number}_wmd_preview" class="wmd-panel wmd-preview"></div>
						</div>
					</td>
`

function addNewOption() {
	current_option_number += 1;
	newOptionHTML = option_html;
	newOptionHTML = newOptionHTML.replace(/{option_id}/g, "option_" + current_option_number);
	newOptionHTML = newOptionHTML.replace(/{option_number}/g, '' + current_option_number);
	newOptionHTMLElement = document.createElement("tr");
	newOptionHTMLElement.id = "table_row_option_{option_number}".replace("{option_number}", current_option_number);
	newOptionHTMLElement.innerHTML = newOptionHTML;
	console.log(newOptionHTMLElement.html);
	options_table.insertBefore(newOptionHTMLElement, null);
	newTextArea = document.getElementById("id_draft_options_{option_number}".replace("{option_number}", current_option_number));

	DjangoPagedown.createEditor(newTextArea);
	update_textarea_handlers();
}

//Handles focussing textarea and shows the preview.
function update_textarea_handlers(){

	$('.wmd-wrapper').click(function () {
		if (!$(this).find('textarea').hasClass('expand')){
			$('.wmd-input').removeClass('expand');
			$('.wmd-preview').hide();
			$(this).find('textarea').addClass('expand');
			$(this).find('.wmd-preview').show();
		}
	});
}

DjangoPagedown.init();
update_textarea_handlers();