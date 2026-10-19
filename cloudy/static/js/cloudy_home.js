$(document).ready(function() {
		/* Slide features */
		simpleSlide({'swipe':'true'});

		/* Cycle quotes */
		$('.cycle-quotes').cycle({
			fx: 'fade',
			speed:  500,
			timeout: 6000,
			cleartypeNoBg: true
		});

		/* Cycle partners */
		$('.cycle-partners').cycle({
			fx: 'fade',
			speed:  500,
			timeout: 6000,
			cleartypeNoBg: true
		});

});
