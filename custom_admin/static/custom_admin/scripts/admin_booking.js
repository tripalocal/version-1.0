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
},

globalVariables = {
    chosenFields: {},
    cleanChosenFields: function() {
        this.chosenFields = {};
    }
},

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
        domPresentationEvents.selectBookingsEvent();

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

    selectBookingsEvent: function() {
        $("[name='admin-panel-booking-id-checkbox']").on("click", {}, domPresentationEventsProcessor.selectBookings);
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
    // decorator
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
    selectBookings: function(event) {
        var currentBooking = event.currentTarget;
        if(currentBooking.checked) {
            globalVariables.chosenFields[currentBooking.value] = true;
        } else {
            globalVariables.chosenFields[currentBooking.value] = false;
        }
    }
}

var domCommEvents = {
    setListener: function() {
        this.uploadReviewEvent();
        this.changeTimeEvent();
        this.markNoShowEvent();
        this.reopenBookingEvent();
        this.cancelBookingEvent();
        this.deleteBookingsEvent();
        this.archiveBookingEvent();
        this.sendEmailToHostEvent();
        this.sendEmailToGuestEvent();
    },

    uploadReviewEvent: function() {
        $("#upload-review-button").on("click", {}, dommCommEventsProcessor.processUploadReviewEvent);
    },

    changeTimeEvent: function() {
        $("#change-time-button").on("click", {}, dommCommEventsProcessor.processChangeTimeEvent);
    },

    markNoShowEvent: function() {
        $("a[id^='booking-mark-as-no-show-link-']").on("click", {"status": "no_show"}, dommCommEventsProcessor.processChangeStatusEvent);
    },

    reopenBookingEvent: function() {
        $("a[id^='booking-reopen-booking-link-']").on("click", {"status": "paid"}, dommCommEventsProcessor.processChangeStatusEvent);
    },

    cancelBookingEvent: function() {
        $("a[id^='booking-cancel-booking-link-']").on("click", {"status": "rejected"}, dommCommEventsProcessor.processChangeStatusEvent);
    },

    deleteBookingsEvent: function() {
        $("#bookings-delete-link").on("click", {"status": "deleted"}, dommCommEventsProcessor.processMultiChangeStatusEvent);
    },

    archiveBookingEvent: function() {
        $("#bookings-archive-link").on("click", {"status": "archived"}, dommCommEventsProcessor.processMultiChangeStatusEvent);
    },

    sendEmailToHostEvent: function() {
        $("#bookings-email-to-host-link").on("click", {"recipient": "host"}, dommCommEventsProcessor.processSendEmailEvent);
    },

    sendEmailToGuestEvent: function() {
        $("#bookings-email-to-guest-link").on("click", {"recipient": "guest"}, dommCommEventsProcessor.processSendEmailEvent);
    },
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
        commModule.postData(href, datum, dommCommEventsCallBack.changeTimeEventSuccessCallBack, helper.genaralFailNotification);
        $("#change-time-popup").hide();
        eventQueue.addEvent(event);
    },

    processChangeStatusEvent: function(event) {
        var status = event.data.status;
        var statusShow = helper.changeBookingStatusDisplay(status);
        if(!confirm("Are you sure to change the booking status as " + statusShow + "?")) {
            return null;
        }
        var triggerId = event.currentTarget.id;
        var objectId = helper.getLineIdByElementId(triggerId);
        var href = location.href;
        var datum = {
            "operation": "change_status",
            "status": status,
            "object_id": objectId,
        };
        commModule.postData(href, datum, dommCommEventsCallBack.changeStatusSuccessCallBack, helper.genaralFailNotification);
        eventQueue.addEvent(event);
    },

    processMultiChangeStatusEvent: function(event) {
        var status = event.data.status;
        var statusShow = helper.changeBookingStatusDisplay(status);
        if(!confirm("Are you sure to change the booking status as " + statusShow + "?")) {
            return null;
        }
        var href = location.href;
        var datum = {
            "operation": "multi_change_statuses",
            "status": status,
            "object_id": helper.collectChosenFields(),
        };
        commModule.postData(href, datum, dommCommEventsCallBack.deleteBookingSunccessCallBack, helper.genaralFailNotification);
        globalVariables.cleanChosenFields();
        eventQueue.addEvent(event);
    },

    processSendEmailEvent: function(event) {
        var recipient = event.data.recipient
        if(!confirm("Are you sure to send the email to " + recipient + "?")) {
            return null;
        }
        var href = location.href;
        var datum = {
            "operation": "send_mail",
            "recipient": recipient,
            "object_id": helper.collectChosenFields(),
        };
        commModule.postData(href, datum, dommCommEventsCallBack.deleteBookingSunccessCallBack, helper.genaralFailNotification);
        globalVariables.cleanChosenFields();
        eventQueue.addEvent(event);
    }
}

var dommCommEventsCallBack = {
    uploadReviewEventSuccessCallBack: function(result) {
        if (!result.success) {
            alert("Failed Updated! Reason: " + result.server_info + ".");
            return null;
        }
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
        helper.resetListener();
    },
    changeTimeEventSuccessCallBack: function(result) {
        if (!result.success) {
            alert("Failed Updated! Reason: " + result.server_info + ".");
            return null;
        }
        var newDatetime = result.new_datetime;
        var id = result.id;
        var tdStatusDatetime = $("#td-booking-datetime-" + id);
        tdStatusDatetime.text(newDatetime);
        helper.resetListener();
    },
    changeStatusSuccessCallBack: function(result) {
        if (!result.success) {
            alert("Failed Updated! Reason: " + result.server_info + ".");
            return null;
        }
        var statusDescription = result.status_description;
        var id = result.id;
        var tdStatusDescription = $("#td-status-description-" + id);
        var tdActions = $("#td-action-" + id);
        tdStatusDescription.text(statusDescription);
        presentationUtil.changeActionPanel(tdActions, id,
            result.actions[0],
            result.actions[1],
            "",
            "");
        helper.resetListener();
    },
    deleteBookingSunccessCallBack: function(result) {
        if (!result.success) {
            alert("Failed Updated! Reason: " + result.server_info + ".");
            return null;
        }
        globalVariables.cleanChosenFields();
        var ids = result.id;
        for(var index in ids) {
            $("#booking-table-row-" + ids[index]).css("display", "none");
        }
        helper.resetListener();
    },
    archiveBookingSuccessCallBack: function(result) {
        return this.deleteBookingSunccessCallBack(result);
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
        console.log(result);
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
    changeBookingStatusDisplay: function(status) {
        switch (status) {
            case "no_show":
                return "not show status";
            case "paid":
                return "previous status";
            case "rejected":
                return "cancelled status";
            case "accepted":
                return "accepted status";
            case "requested":
                return "requested status";
            case "deleted":
                return "deleted status";
            case "archived":
                return "archived status";
        }

    },
    collectChosenFields: function() {
        var result = [];
        for(var key in globalVariables.chosenFields) {
            if(globalVariables.chosenFields[key]) {
                result.push(key);
            }
        }
        return result;
    },
    mapTitleToId: function(title) {
        list = title.split(" ");
        result = '';
        for(var index in list) {
            result = result + list[index].toLowerCase() + '-';
        }
        result = 'booking-' + result + 'link-';
        return result;
    },
    resetListener: function() {
        domPresentationEvents.setListner();
        domCommEvents.setListener();
    }
}

var presentationUtil = {
    changeActionPanel: function(td, id, newFirstTitle, newSecondTitle, newFirstId, newSecondId) {
        var children = td.find("a");
        var firstLink = children[0];
        var secondLink = children[1];
        children.unbind();
        if(newFirstTitle) {
            firstLink.innerHTML = newFirstTitle;
            firstLink.id = helper.mapTitleToId(newFirstTitle) + id;
        } else {
            firstLink.innerHTML = '';
            firstLink.id = '';
        }
        if(newSecondTitle) {
            secondLink.innerHTML = newSecondTitle;
            secondLink.id = helper.mapTitleToId(newSecondTitle) + id;
        } else {
            secondLink.innerHTML = '';
            secondLink.id = '';
        }
    },
}

var constant = {
    CANCEL_BOOKING_DESCRIPTION: "Cancel Booking",
    CHANGE_TIME_DESCRIPTION: "Change Time",

    CANCEL_BOOKING_ID_PREFIX: "booking-cancel-booking-link-",
    CHANGE_TIME_ID_PREFIX: "booking-change-time-link-",

    TD_DATETIME_PREFIX: "td-booking-datetime-",
}

