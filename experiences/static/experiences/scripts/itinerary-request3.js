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
			left: 'title',
			center: '',
			right: 'today prev,next'
		},
		select: function(start, end, jsEvent, view) {
			$('#id_start_date').val(moment(start).format("YYYY-MM-DD"));
			$('#id_end_date').val(moment(end).format("YYYY-MM-DD"));
		}
	});

	// Show page when init is done
	$('.loading').fadeOut('slow');

	// Bind click events
	$('#start-btn').on('click', function() {
		$.fn.fullpage.moveSectionDown();
	})
	$('.overlay').on('click', function() {
		$this = $(this);
		$this.hasClass('selected') ? $this.removeClass('selected') : $this.addClass('selected');
		updateCities();
	});
	$('.circle').on('click', function() {
		$this = $(this);
		$this.hasClass('unselected') ? $this.removeClass('unselected') : $this.addClass('unselected');
		updateInterests();
	});
	$('#nav-up').on('click', function() {
		$.fn.fullpage.moveSectionUp();
	});
	$('#nav-down').on('click', function() {
		$.fn.fullpage.moveSectionDown();
	});
	
	$('select').on('change',function() {
		updateBudget();
	});

	$('#submit-btn').on('click', function() {
		$(this).html('Submitting<i class="ellipsis"><i>.</i><i>.</i><i>.</i></i>').attr('disabled', 'disabled');
		if (validateForm()) {
			$.ajax({
					url: '/itinerary/request/',
					type: 'POST',
					data: {
						csrfmiddlewaretoken: $("[name='csrfmiddlewaretoken']")[0].value,
						destinations: $("#id_destinations").val(),
						start_date: $("#id_start_date").val(),
						end_date: $("#id_end_date").val(),
						guests_adults: $("#id_guests_adults").val(),
						guests_children: $("#id_guests_children").val(),
						guests_infants: $("#id_guests_infants").val(),
						interests: $("#id_interests").val(),
						accommodation: $("#accommodation").val(),
						car_driver: $("#car-driver").val(),
						national_flight: $("#national-flight").val(),
						service_language: $("#service-language").val(),
						requirements: $("#id_requirements").val(),
						name: $("#id_name").val(),
						wechat: $("#id_wechat").val(),
						email: $("#id_email").val(),
						mobile: $("#id_mobile").val(),
						budget : $('#budget').text()
					}
				})
				.done(function() {

				})
				.fail(function() {
					$('.alert-danger').fadeIn();
				});
		}
		$(this).removeAttr('disabled').html('Submit');
	})
})

function updateBudget() {
	var guests = parseInt($('#id_guests_adults').val()) + parseInt($("#id_guests_children").val()) + parseInt($("#id_guests_infants").val());
	var days = moment($('#id_end_date').val()).diff(moment($('#id_start_date').val()), 'days');
	var cities = $('#id_destinations').val().split(',').length;
	var min = 0;
	var max = 0;

	// car+driver
	switch ($('#car-driver').val()) {
		case 'please select':
			break;
		case 'infrequent':
			if (guests < 5) {
				min += 167;
				max += 400;
			} else if (guests < 8) {
				min += 267;
				max += 500;
			} else {
				min += 333;
				max += 667;
			}
			break;
		case 'frequent':
			if (guests < 5) {
				min += 250;
				max += 600;
			} else if (guests < 8) {
				min += 400;
				max += 750;
			} else {
				min += 500;
				max += 1000;
			}
			break;
		case 'entire trip':
			if (guests < 5) {
				min += 500;
				max += 1200;
			} else if (guests < 8) {
				min += 800;
				max += 1500;
			} else {
				min += 1000;
				max += 2000;
			}
			break;
	}

	// accommodation
	switch ($('#accommodation').val()) {
		case 'please select':
			break;
		case 'none':
			break;
		case '3 star':
			min += ((guests / 2) * 150);
			max += ((guests / 2) * 300);
			break;
		case '4 star':
			min += ((guests / 2) * 200);
			max += ((guests / 2) * 400);
			break;
		case '5 star':
			min += ((guests / 2) * 300);
			max += ((guests / 2) * 600);
			break;
	}

	// service language
	switch ($('#service-language').val()) {
		case 'please select':
			break;
		case 'english':
			break;
		case 'chinese':
			min += 50;
			max += 50;
	}

	//// PER DAY ABOVE
	min *= days;
	max *= days;
	//// FOR WHOLE TRIP BELOW

	// national flights
	switch ($('#national-flight').val()) {
		case 'please select':
			break;
		case 'none':
			break;
		case 'economy':
			min += ((cities - 1) * guests * 200);
			max += ((cities - 1) * guests * 400);
	}

	// airport transfer
	switch ($('#airport-transfer').val()) {
		case 'please select':
			break;
		case 'none':
			break;
		case 'yes':
			min += (cities * 200);
			max += (cities * 200);
	}

	if (min != 0 && max != 0) {
		$('#budget').text('Estimated cost: $' + min + ' to $' + max + ' total for this itinerary.');
	}
}

function updateCities() {
	var selectedCities = $('.overlay.selected').map(function() {
		return $(this).parent().attr('data-city');
	}).get();
	$('#id_destinations').val(selectedCities.join());
}

function updateInterests() {
	var selectedInterests = $('.circle').filter(':not(.unselected)').map(function() {
		return $(this).text();
	}).get();
	$('#id_interests').val(selectedInterests.join());
}

function validateForm() {
	if ($('#id_destinations').val() && $('#id_start_date').val() && $('#id_guests_adults').val() && $('#id_name').val() && $('#id_mobile').val() && $('#id_email').val()) {
		return true;
	} else {
		$('.asterisk').css({'font-size':'48px', 'color': 'red'});
		return false;
	}
}
