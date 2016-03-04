$(document).ready(function () {
    mixpanel.track("viewed homepage");
        
    $('#label-custom-itinerary').addClass('active');
    $('#custom-itinerary').fadeIn();
    $('#toggle-main').change(function() {
      $('.toggle-label').each(function() {
        var $this = $(this);
        $this.hasClass('active') ? $this.removeClass('active') : $this.addClass('active')
      });
      $('.homepage-option').each(function() {
        var $this = $(this);
        $this.is(':visible') ? $this.hide() : $this.fadeIn()
      })
    });
    $('.toggle-label').click(function() {
      if ($(this).hasClass('active')) {
        return false;
      } else {
        $('#toggle-main').click();
      }
    })

    function getParameterByName(name) {
        name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
        var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
            results = regex.exec(location.search);
        return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
    }

    $("#id_city").attr("class", "btn btn-default dropdown-toggle homepage-city");

    //hide loginpartial on homepage
    $(".navBox").attr("style", "display:none");


    $("#language_switch_topbar").click(function () {
        if ($(this).val() == "cn") {
            mixpanel.track("switched language from top bar_cn");
        } else {
            mixpanel.track("switched language from top bar");
        }
    });

    var utmId = getParameterByName('utm');
    if (utmId) {
        initial_referrer = "utm" + utmId;
    } else {
        initial_referrer = document.referrer;
    }

    var des_url = window.location.pathname;
    var language = "en-au";
    if (des_url.indexOf("/cn") > -1 || window.location.href.indexOf(".cn") > -1) {
        language = "zh-CN";
    }

    mixpanel.people.set({"Language": language});
    mixpanel.people.set({"$initial_referrer": initial_referrer});

    if (language == "zh-CN") {
        $(function () {
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
        });
    }
    else {
        $(function () {
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

        });
    }

    var video = $("video").get(0);
    $("#enter_fullscreen").click(function () {
        $("#video-fullscreen").fadeIn();
        mixpanel.track("viewed video");
        video.play();
    });

    $("#exit_video").click(function () {
        $("#video-fullscreen").fadeOut();
        video.pause();
    });

});
