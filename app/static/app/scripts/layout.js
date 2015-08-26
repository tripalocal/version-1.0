function create_post(email, message) {
    $.ajax({
        url: "email_custom_trip",
        type: "POST",
        dataType: "json",
        data: {
            csrfmiddlewaretoken: $("[name='csrfmiddlewaretoken']")[0].value,
            message: message,
            email: email
        },

        success: function (json) {
            $('#popup-form-details').val('');
            $('#popup-form-email').val('');
            $('#results').html("<p class=''>Thank you for you suggestion.</p>");
            $.cookie("closePopup", 3, {path: '/'});
        },

        error: function (xhr, errmsg, err) {
            $('#results').html("<p class=''>Oops! We have encountered an error.</p>");
        }
    });
}


$(document).ready(function () {
    var popupTimmer;

    if ($(window).width() > 520) {
        var nClose = parseInt($.cookie("closePopup"), 10);

        if (!nClose || nClose < 3) {
            popupTimmer = setTimeout(function () {
                $('#help-popup').modal('show');
                mixpanel.track("saw popup01");
            }, 60000); // milliseconds
        }

        $('#help-popup').on('hidden.bs.modal', function () {
            mixpanel.track("closed popup01");
        });

        $('.close-popup').click(function () {
            clearTimeout(popupTimmer);
            if (nClose) {
                $.cookie("closePopup", nClose + 1, {path: '/'});
            } else {
                $.cookie("closePopup", 1, {path: '/'});
            }

            $('#help-popup').modal('hide');
            mixpanel.track("closed popup01");
        });

        $('#help-no').click(function () {
            clearTimeout(popupTimmer);
            if (nClose) {
                $.cookie("closePopup", nClose + 1, {path: '/'});
            } else {
                $.cookie("closePopup", 1, {path: '/'});
            }

            $('#help-popup').modal('hide');
            mixpanel.track("selected No from popup01");
        });

        $('#help-yes').click(function () {
            $('#popup-page-1').hide();
            $('#popup-page-2').show();
            mixpanel.track("selected Yes from popup01");
        });

        $('#custom-trip-form').on('submit', function (event) {
            event.preventDefault();

            $('#results').empty();
            email = $('#popup-form-email').val();
            message = $('#popup-form-details').val();

            if (!message || !email) {
                $('#results').html("<p class=''>Please fill all fields.</p>");
            } else {
                var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
                if (regex.test(email)) {
                    alert('Thanks.');
                    create_post(email, message);
                } else {
                    $('#results').html("<p class=''>Email Invalid.</p>");
                }
            }
        });
    }

    var des_url = window.location.pathname;
    if (des_url.indexOf("/cn") > -1) {
        $('#id_language_select').val('cn');
        $('#id_language_top').attr("href", "https://www.tripalocal.com" + des_url.substring(3));
    }
    else if (window.location.href.indexOf(".cn") > -1) {
        $('#id_language_select').val('cn');
        $('#id_language_top').attr("href", "https://www.tripalocal.com" + des_url);
    }
    else {
        $('#id_language_select').val('en');
        $('#id_language_top').attr("href", "https://www.tripalocal.com/cn" + des_url);
    }

    $('#id_language_select').change(function () {
        if ($("#user_email").val()) {
            mixpanel.identify($("#user_email").val());
        }

        var des_url = window.location.pathname;

        if ($(this).val() == "cn") {
            mixpanel.track("switched language from footer");
            window.location.href = "https://www.tripalocal.com/cn" + des_url;
        } else {
            mixpanel.track("switched language from footer_cn");
            window.location.href = "https://www.tripalocal.com" + des_url.substring(3);
        }
    });

    $('#id_profile_div').click(function () {
        hide = $('#id_menu').attr('hide');
        if (hide == 'true') {
            $('#id_menu').attr('style', '');
            $('#id_menu').attr('hide', 'false');
        }
        else {
            $('#id_menu').attr('style', 'display:none;');
            $('#id_menu').attr('hide', 'true');
        }
    });
});
