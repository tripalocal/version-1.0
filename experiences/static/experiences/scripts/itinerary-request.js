$(document).ready(function() {
  // Initialise skrollr
  var s = skrollr.init();

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

  // Bind click events
  $('.scroll-down').on('click', function() {
    $('html,body').animate({
      scrollTop: $('#slide1').offset().top
    }, 'slow');
  });
  $('.overlay').on('click', function() {
    $this = $(this);
    $this.hasClass('selected') ? $this.removeClass('selected') : $this.addClass('selected');
  });
  $('.circle').on('click', function() {
    $this = $(this);
    $this.hasClass('unselected') ? $this.removeClass('unselected') : $this.addClass('unselected');
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
          budget: $("#id_budget").val(),
          interests: $("#id_interests").val(),
          whats_included: $("#id_whats_included").val(),
          accommodation: $("#accommodation").val(),
          car_driver: $("#car-driver").val(),
          national_flight: $("#national-flight").val(),
          requirements: $("#id_requirements").val(),
          name: $("#id_name").val(),
          wechat: $("#id_wechat").val(),
          email: $("#id_email").val(),
          mobile: $("#id_mobile").val()
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
});

function validateForm() {
  var selectedCities = $('.overlay.selected').map(function() {
    return $(this).parent().attr('data-city');
  }).get();
  if (selectedCities.length === 0) {
    return raiseError('destinations');
  } else {
    $('#id_destinations').val(selectedCities.join());
  }

  if (!$('#id_start_date').val() || !$('#id_end_date').val()) {
    return raiseError('dates');
  }

  if (!$('#id_name').val() || !$('#id_email').val() || !$('#id_wechat').val() || !$('#id_mobile').val()) {
    return raiseError('contact');
  }

  var selectedInterests = $('.circle').filter(':not(.unselected)').map(function() {
    return $(this).text();
  }).get();
  $('#id_interests').val(selectedInterests.join());

  return true;
}

function raiseError(section) {
  console.log(section);
  $('html,body').animate({
      scrollTop: $('#' + section).offset().top
  }, 'slow');
  return false;
}

function budgetCalculator() {
  
}