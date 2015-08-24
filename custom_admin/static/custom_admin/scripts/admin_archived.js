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
        domPresentationEvents.selectBookingsEvent();
    },
    selectBookingsEvent: function() {
        $("[name='admin-panel-booking-id-checkbox']").on("click", {}, domPresentationEventsProcessor.selectBookings);
    }
}

var domPresentationEventsProcessor = {
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
        this.deleteBookingsEvent();
        this.unarchiveBookingEvent();
    },
    deleteBookingsEvent: function() {
        $("#bookings-delete-link").on("click", {"status": "deleted"}, dommCommEventsProcessor.processMultiChangeStatusEvent);
    },
    unarchiveBookingEvent: function() {
        $("#bookings-unarchive-link").on("click", {"status": "unarchived"}, dommCommEventsProcessor.processMultiChangeStatusEvent);
    }

}

var dommCommEventsProcessor = {
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
        commModule.postData(href, datum, dommCommEventsCallBack.processMultiChangeStatusSunccessCallBack, helper.genaralFailNotification);
        globalVariables.cleanChosenFields();
        eventQueue.addEvent(event);
    }
}

var dommCommEventsCallBack = {
    processMultiChangeStatusSunccessCallBack: function(result) {
        if (!result.success) {
            alert("Failed Updated! Reason: " + result.server_info + ".");
            return null;
        }
        globalVariables.cleanChosenFields();
        var ids = result.id;
        for(var index in ids) {
            $("#booking-table-row-" + ids[index]).css("display", "none");
        }
    },
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
    collectChosenFields: function() {
        var result = [];
        for(var key in globalVariables.chosenFields) {
            if(globalVariables.chosenFields[key]) {
                result.push(key);
            }
        }
        return result;
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
            case "unarchived":
                return "unarchived status";
        }

    },
}

var presentationUtil = {

}

var constant = {
    CANCEL_BOOKING_DESCRIPTION: "Cancel Booking",
    CHANGE_TIME_DESCRIPTION: "Change Time",

    CANCEL_BOOKING_ID_PREFIX: "booking-cancel-booking-link-",
    CHANGE_TIME_ID_PREFIX: "booking-change-time-link-",

    TD_DATETIME_PREFIX: "td-booking-datetime-",
}

