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
        $("a[id^='booking-change-time-link-']").on("click",{"popupDivId": "change-time-popup"},domPresentationEventsProcessor.showPopup);
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
    }
}

var domCommEvents = {
    setListener: function() {
        this.uploadReviewEvent();
    },

    uploadReviewEvent: function() {
        $("#upload-review-button").on("click", {}, dommCommEventsProcessor.processUploadReviewEvent);
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
    getLineIdByElementId: function(name) {
        // Id is the part following the last '-' in a DOM name.
        return name.split("-").pop();
    },
    genaralSuccessNotification: function(result) {
        if(result.success) {
            alert("Success Updated!");
        } else {
            alert("Failed Updated! Because: " + result.serverInfo);
        };
    },
    genaralFailNotification: function() {
        alert("Failed Updated!");
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
    }
}

var constant = {
    CANCEL_BOOKING_DESCRIPTION: "Cancel Booking",
    CHANGE_TIME_DESCRIPTION: "Change Time",

    CANCEL_BOOKING_ID_PREFIX: "booking-cancel-booking-link-",
    CHANGE_TIME_ID_PREFIX: "booking-change-time-link-",
}

