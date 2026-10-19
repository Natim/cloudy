/*JSHINT */
/*global $: true, cloudy: true */

function update_count_chars_message() {
	var left = 140 - $("#share-message").val().length;
	if (left < 0) {
		$("#char-count").addClass("error-message");
	} else {
		$("#char-count").removeClass("error-message");
	}
	$("#char-count span").html(left);
}

$('a.fbShare').live('click', function() {
	cloudy.share('facebook', {
		url: $(this).attr('href'),
		title: $(this).attr('title')
	});
	return false;
});

$('a.twShare').live('click', function() {
	cloudy.share('twitter', {
		tweet: $("#share-message").val()
	});
	return false;
});

$(document).ready(function() {
	/* Count char for text area */
	update_count_chars_message();
	$("#share-message").keyup(function() {
		update_count_chars_message();
	});
});
