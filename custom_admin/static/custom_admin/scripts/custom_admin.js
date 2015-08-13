function changeTime(bookingId) {
    var changeTimePopup = document.getElementById('change_time_popup');
    var form = document.getElementById('change_time_form');
    var bookingTime = document.getElementById('booking_date_time_booking_id_' + bookingId).innerHTML;
    var date_info = bookingTime.split(" ");
    var day = date_info[0];
    var month = _convertMonthNameToNumber(date_info[1]);
    var year = date_info[2];
    var time = date_info[3];
    var yearSelect = document.getElementById('id_new_date_year');
    var monthSelect = document.getElementById('id_new_date_month');
    var daySelect = document.getElementById('id_new_date_day');

    for (var i = 0; i < yearSelect.length; i++)
        if (yearSelect.options[i].text == year)
            yearSelect.options[i].selected = true;
    monthSelect.options[month - 1].selected = true;
    daySelect.options[day - 1].selected = true;
    document.getElementById('id_new_time').value = time;
    document.getElementById('booking_id_in_change_time_popup').innerHTML = bookingId;
    // Show the popup.
    changeTimePopup.style.display = "block";




    // Change the form action.
    form.action = "/custom_admin/change_time/" + bookingId;
}

function cancelBooking(bookingId) {
    var r = confirm("Are you sure to cancel the booking?");
    if (r == true) {
        document.location.href = '/custom_admin/cancel_booking/' + bookingId;
    }
}

function reopenBooking(bookingId) {
    var r = confirm("Are you sure to reopen the booking?");
    if (r == true) {
        document.location.href = '/custom_admin/reopen_booking/' + bookingId;
    }
}

function markAsNoShow(bookingId) {
    var r = confirm("Are you sure to mark the booking as not showing?");
    if (r == true) {
        document.location.href = '/custom_admin/mark_as_no_show/' + bookingId;
    }
}

function _convertMonthNameToNumber(month_name) {
    switch (month_name) {
        case "Jan":
            return 1;
        case "Feb":
            return 2;
        case "Mar":
            return 3;
        case "Apr":
            return 4;
        case "May":
            return 5;
        case "Jun":
            return 6;
        case "Jul":
            return 7;
        case "Aug":
            return 8;
        case "Sep":
            return 9;
        case "Oct":
            return 10;
        case "Nov":
            return 11;
        case "Dec":
            return 12;
    }
}




function closeChangeTimePopup() {
    document.getElementById('change_time_popup').style.display = "none";
}

function closeUploadReviewPopup() {
    document.getElementById('upload_review_popup').style.display = "none";
}

$(document).ready(function () {
    $("#change_time_success_notification").fadeOut(6000);
    $("#change_time_failed_notification").fadeOut(6000);
});


function uploadReview(bookingId) {
    var uploadReviewPopup = document.getElementById('upload_review_popup');
    var form = document.getElementById('upload_review_form');

    uploadReviewPopup.style.display = "block";
    form.action = "/custom_admin/upload_review/" + bookingId;
}

function sendConfirmationEmailHost() {
    var r = confirm("Are you sure to send the email to hosts?");
    if (r == true) {
        var form = document.getElementById('custom_admin_panel_table_form');
        form.action = "/custom_admin/send_confirmation_email_host/";
        form.submit();
    }
}

function sendConfirmationEmailGuest() {
    var r = confirm("Are you sure to send the email to guests?");
    if (r == true) {
        var form = document.getElementById('custom_admin_panel_table_form');
        form.action = "/custom_admin/send_confirmation_email_guest/";
        form.submit();
    }
}

function deleteBookings() {
    var r = confirm("Are you sure to delete the bookings?");
    if (r == true) {
        var form = document.getElementById('custom_admin_panel_table_form');
        form.action = "/custom_admin/delete_bookings/";
        form.submit();
    }
}

function archiveBookings() {
    var r = confirm("Are you sure to archive the bookings?");
    if (r == true) {
        var form = document.getElementById('custom_admin_panel_table_form');
        form.action = "/custom_admin/archive_bookings/";
        form.submit();
    }
}

function unarchiveBookings() {
    var r = confirm("Are you sure to unarchive the bookings?");
    if (r == true) {
        var form = document.getElementById('custom_admin_panel_table_form');
        form.action = "/custom_admin/unarchive_bookings/";
        form.submit();
    }
}