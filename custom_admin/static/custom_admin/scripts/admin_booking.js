eventQueue = {
    events: [],
    addEvent: function(event) {
        this.events.push(event);
    },
    removeEvent: function() {
        this.events.pop();
    },
    getPreviousEvent: function() {
        return this.events[this.events.length-1];
    }
}

$(document).ready(function() {
    initDOMPresentation();
    domCommEvents.setListener();
    domPresentationEvents.setListner();
});

function initDOMPresentation() {
    eventQueue.events = [];

}

var domPresentationEvents = {
    setListner: function() {
        domPresentationEvents.changeTimeEvent();
        domPresentationEvents.uploadReviewEvent();

    },

    changeTimeEvent: function() {
        // Click the change time link, popup for changing time showed.
        $("a[id^='booking-change-time-link-']").on("click",{"popupDivId": "change-time-popup"},domPresentationEventsProcessor.setPopupDateTime);
        // Close the change time popup.
        $("#close-change-time-button").on("click", {"popupDivId": "change-time-popup"}, domPresentationEventsProcessor.hidePopup);
    },

    uploadReviewEvent: function() {
        // Click the upload review link, popup for uploading review.
        $("a[id^='booking-upload-review-link-']").on("click",{"popupDivId": "upload-review-popup"},domPresentationEventsProcessor.showPopup);
        // Close the upload review popup.
        $("#close-upload-review-button").on("click", {"popupDivId": "upload-review-popup"}, domPresentationEventsProcessor.hidePopup);
    },
}

var domPresentationEventsProcessor = {
    showPopup: function(event) {
        var popupDivId = event.data.popupDivId;
        $("#" + popupDivId).show();
        eventQueue.addEvent(event);
    },
    hidePopup: function(event) {
        var popupDivId = event.data.popupDivId;
        $("#" + popupDivId).hide();
        eventQueue.addEvent(event);
    },
    setPopupDateTime: function(event) {
        domPresentationEventsProcessor.showPopup(event);
        var triggerId = event.currentTarget.id;
        var bookingId = helper.getLineIdByElementId(triggerId);
        var datetime = helper.getDateTimeFromString($("#" + constant.TD_DATETIME_PREFIX + bookingId).text());
        $("#id_new_date_year").val(datetime.year);
        $("#id_new_date_month").val(datetime.month);
        $("#id_new_date_day").val(datetime.day);
        $("#id_new_time").val(datetime.time);
        $("#booking_id_in_change_time_popup").text(bookingId);
    },
}

var domCommEvents = {
    setListener: function() {
        this.uploadReviewEvent();
        this.changeTimeEvent();
    },

    uploadReviewEvent: function() {
        $("#upload-review-button").on("click", {}, dommCommEventsProcessor.processUploadReviewEvent);
    },

    changeTimeEvent: function() {
        $("#change-time-button").on("click", {}, dommCommEventsProcessor.processChangeTimeEvent);
    }

}

var dommCommEventsProcessor = {
    processUploadReviewEvent: function(event) {
        // Get the button id from the previous event.
        var previousTriggerId = eventQueue.getPreviousEvent().currentTarget.id;
        var objectId = helper.getLineIdByElementId(previousTriggerId);
        var review = $("#id_review").val();
        var rate = $("#id_rate").val();
        var href = location.href;
        var datum = {
            "operation": "upload_review",
            "review": review,
            "rate": rate,
            "object_id": objectId,
        };
        commModule.postData(href, datum, dommCommEventsCallBack.uploadReviewEventSuccessCallBack, helper.genaralFailNotification);
        $("#upload-review-popup").hide();
        eventQueue.addEvent(event);
    },

    processChangeTimeEvent: function(event) {
        var previousTriggerId = eventQueue.getPreviousEvent().currentTarget.id;
        var objectId = helper.getLineIdByElementId(previousTriggerId);
        var newDate = $("#id_new_date_year").val() + "-" + $("#id_new_date_month").val() + "-" + $("#id_new_date_day").val();
        var newTime = $("#id_new_time").val();
        var href = location.href;
        var datum = {
            "operation": "change_time",
            "new_date": newDate,
            "new_time": newTime,
            "object_id": objectId,
        };
        console.log(datum);
        commModule.postData(href, datum, helper.genaralSuccessNotification, helper.genaralFailNotification);
        $("#upload-review-popup").hide();
        eventQueue.addEvent(event);
    }
}

var dommCommEventsCallBack = {
    uploadReviewEventSuccessCallBack: function(result) {
        var statusDescription = result.status_description;
        var id = result.id;
        var colour = result.colour;
        var tdStatusDescription = $("#td-status-description-" + id);
        var tdActions = $("#td-action-" + id);
        tdStatusDescription.text(statusDescription);
        tdStatusDescription.css("color", colour);
        presentationUtil.changeActionPanel(tdActions, id,
            constant.CANCEL_BOOKING_DESCRIPTION,
            constant.CHANGE_TIME_DESCRIPTION,
            constant.CANCEL_BOOKING_ID_PREFIX,
            constant.CANCEL_BOOKING_ID_PREFIX);
    }
}

var commModule = {
    postData: function(href, datum, successCallback, failCallback) {
        $.post(href, $.extend({
            'csrfmiddlewaretoken': $("[name='csrfmiddlewaretoken']")[0].value
        }, datum))
            .done(successCallback)
            .fail(failCallback);
    },
}

var helper = {
    getLineIdByElementId: function (name) {
        // Id is the part following the last '-' in a DOM name.
        return name.split("-").pop();
    },
    genaralSuccessNotification: function (result) {
        if (result.success) {
            alert("Success Updated!");
        } else {
            alert("Failed Updated! Because: " + result.server_info);
        }
        ;
    },
    genaralFailNotification: function () {
        alert("Failed Updated!");
    },
    convertMonthNameToNumber: function(month_name) {
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
    },
    getDateTimeFromString: function (bookingTime) {
        var date_info = bookingTime.split(" ");
        return {
            day: date_info[0],
            month: this.convertMonthNameToNumber(date_info[1]),
            year: date_info[2],
            time: date_info[3]
        };
    },
}



var presentationUtil = {
    changeActionPanel: function(td, id, newFirstTitle, newSecondTitle, newFirstId, newSecondId) {
        var children = td.find("a");
        var firstLink = children[0];
        var secondLink = children[1];
        firstLink.innerHTML = newFirstTitle;
        firstLink.id = newFirstId + id;
        secondLink.innerHTML = newSecondTitle;
        secondLink = newSecondId + id;
    },
}

var constant = {
    CANCEL_BOOKING_DESCRIPTION: "Cancel Booking",
    CHANGE_TIME_DESCRIPTION: "Change Time",

    CANCEL_BOOKING_ID_PREFIX: "booking-cancel-booking-link-",
    CHANGE_TIME_ID_PREFIX: "booking-change-time-link-",

    TD_DATETIME_PREFIX: "td-booking-datetime-",
}

