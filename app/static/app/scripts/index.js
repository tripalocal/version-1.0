$(document).ready(function () {
    mixpanel.track("viewed homepage");
    $(".request-btn").click(function () {
        window.location.href = "https://www.tripalocal.com/multidaytrip/";
        mixpanel.track("checked out designed multi-day from homepage");
    });

    $("#video-fullscreen").hide();
    function getParameterByName(name) {
        name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
        var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
            results = regex.exec(location.search);
        return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
    }

    $("#id_city").attr("class", "btn btn-default dropdown-toggle homepage-city");
    $("#id_start_date").attr("class", "input-sm");
    $("#id_end_date").attr("class", "input-sm");
    $("#id_start_date").attr("style", "height:40px;");
    $("#id_end_date").attr("style", "height:40px;");


    //hide loginpartial on homepage
    $(".navBox").attr("style", "display:none");


    $("#language_switch_topbar").click(function () {
        if ($(this).val() == "cn") {
            mixpanel.track("switched language from top bar_cn");
        } else {
            mixpanel.track("switched language from top bar");
        }
    });

    $(function () {
        $("#id_start_date").datetimepicker();
    });

    $(function () {
        $("#id_end_date").datetimepicker();
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
