$(document).ready(function() {
	// Initialise fullpage 
	var desktop = true;
	if ($(window).width < 480) {
		var desktop = false;
	}
	$('#fullpage').fullpage({
		autoScrolling: desktop,
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

  if (window.location.pathname.indexOf("/cn") > -1 || window.location.href.indexOf(".cn") > -1) {
  $("#id_start_date").datetimepicker({
      format: 'YYYY-MM-DD', locale: 'zh-CN'
    });
    $("#id_end_date").datetimepicker({
        format: 'YYYY-MM-DD', locale: 'zh-CN',
        useCurrent: false
    });

    $("#id_start_date").on("dp.change", function (e) {
        $('#id_end_date').data("DateTimePicker").minDate(e.date);
    });
    $("#id_end_date").on("dp.change", function (e) {
        $('#id_start_date').data("DateTimePicker").maxDate(e.date);
    });
  }
  else {
    $("#id_start_date").datetimepicker({
        format: 'YYYY-MM-DD'
    });
    $("#id_end_date").datetimepicker({
        format: 'YYYY-MM-DD',
        useCurrent: false
    });

    $("#id_start_date").on("dp.change", function (e) {
        $('#id_end_date').data("DateTimePicker").minDate(e.date);
    });
    $("#id_end_date").on("dp.change", function (e) {
        $('#id_start_date').data("DateTimePicker").maxDate(e.date);
    });
  }
  
  // Clear the date fields
  $('#id_start_date').val('');
  $('#id_end_date').val('');

	// Show page when init is done
	$('.loading').fadeOut('slow');

	// Bind click events
	$('#start-btn').on('click', function() {
		$.fn.fullpage.moveSectionDown();
	});
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
					$('#success-page').html(
						'<h1>Your request has been submitted!</h1><h2>Please keep an eye on our phone call within 4 hours. We will call you between 9am - 9pm Beijing time.</h2>'
					).css({
						'position': 'fixed',
						'width': '100%',
						'height': '100%',
					});
					$('#fp-nav').fadeOut();
					$('#status-bar').slideDown();
				})
				.fail(function() {
					
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
  
  // Check if date fields entered:
  if (isNaN(days)) {
    return;
  }

	// car+driver
	switch ($('#car-driver option:selected').text()) {
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
	switch ($('#accommodation option:selected').text()) {
		case 'please select':
			break;
		case 'none':
			break;
		case '3 star':
			min += (Math.round(guests / 2) * 150);
			max += (Math.round(guests / 2) * 300);
			break;
		case '4 star':
			min += (Math.round(guests / 2) * 200);
			max += (Math.round(guests / 2) * 400);
			break;
		case '5 star':
			min += (Math.round(guests / 2) * 300);
			max += (Math.round(guests / 2) * 600);
			break;
	}

	// service language
	switch ($('#service-language option:selected').text()) {
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
	switch ($('#national-flight option:selected').text()) {
		case 'please select':
			break;
		case 'none':
			break;
		case 'economy':
			min += ((cities - 1) * guests * 200);
			max += ((cities - 1) * guests * 400);
	}

	// airport transfer
	switch ($('#airport-transfer option:selected').text()) {
		case 'please select':
			break;
		case 'none':
			break;
		case 'yes':
			min += (cities * 200);
			max += (cities * 200);
	}

  if (min < 1000) {
    $('#budget').text('Our custom itinerary service starts from $1000');
  }
	else {
		$('#budget').text('Estimated cost: $' + Math.round(min/guests) + '+ per person ($' + min + '+ in total)').addClass('animated fadeInUp');
		var wait = window.setTimeout(function(){
      $('#budget').removeClass('animated fadeInUp')}, 1000
    );
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
		$('.asterisk').addClass('animated shake').css({'color': 'red'});
		var wait = window.setTimeout( function(){
            $('.asterisk').removeClass('animated shake')}, 1000
        );
		return false;
	}
}