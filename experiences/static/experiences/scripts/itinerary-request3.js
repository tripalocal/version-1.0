$(document).ready(function() {
	// Initialise fullpage 
	$('#fullpage').fullpage({
		paddingTop: '50px',
		paddingBottom: '50px', 
		navigation: true,
		navigationPosition: 'left',
		showActiveTooltip: true,
		anchors: ['section1', 'section2', 'section3', 'section4', 'section5', 'section6', 'section7', 'section8', 'section9'],
		navigationTooltips: ['Start', 'Destinations', 'Dates', 'Guests', 'Interests', 'What\'s Included', 'Extras', 'Contact', 'Done!'],
		sectionsColor: ['#f7f7f7', '#f3f3f3', '#7BAABE', 'whitesmoke', '#f7f7f7'],
		onLeave: function(index, nextIndex, direction) {
			if (nextIndex == 2 && direction == 'up') {
				$('#nav-up').attr('disabled', 'disabled');
			} else {
				$('#nav-up').removeAttr('disabled');
			} 
			if (nextIndex == 9 && direction == 'down') {
				$('#nav-down').attr('disabled', 'disabled');
			} else {
				$('#nav-down').removeAttr('disabled');
			}
			if (index == 1 && direction == 'down') {
				$('#status-bar').slideDown();
				$('#nav-up').attr('disabled', 'disabled');
			}
			if (nextIndex == 1 && direction == 'up') {
				$('#status-bar').slideUp();
			}
		}
	});
	// Initialise calendar
	$('#calendar').fullCalendar({
		aspectRatio: 1.5,
		selectable: true,
		unselectAuto: false,
		header: {
			left:   'title',
			center: '',
			right:  'today prev,next'
		},
		select: function(start, end, jsEvent, view) {
			$('#id_start_date').val(moment(start).format("YYYY-MM-DD"));
			$('#id_end_date').val(moment(end).format("YYYY-MM-DD"));
		}
	});
	$('.loading').fadeOut('slow');
	// Bind click events
	$('#start-btn').on('click', function() {
		$.fn.fullpage.moveSectionDown();
	})
	$('.overlay').on('click', function() {
		$this = $(this);
		$this.hasClass('selected') ? $this.removeClass('selected') : $this.addClass('selected');
	});
	$('.circle').on('click', function() {
	    $this = $(this);
	    $this.hasClass('unselected') ? $this.removeClass('unselected') : $this.addClass('unselected');
	});
	$('#nav-up').on('click', function() {
		$.fn.fullpage.moveSectionUp();
	});
	$('#nav-down').on('click', function() {
		$.fn.fullpage.moveSectionDown();
	});
})