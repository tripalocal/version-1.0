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
        domPresentationEvents.selectItinerariesEvent();
    },
    selectItinerariesEvent: function () {
        $("[name='admin-panel-itinerary-id-checkbox']").on("click", {}, domPresentationEventsProcessor.selectItineraries);
    }
}

var domPresentationEventsProcessor = {
    selectItineraries: function(event) {
        var currentItinerary = event.currentTarget;
        if (currentItinerary.checked) {
            globalVariables.chosenFields[currentItinerary.value] = true;
        } else {
            globalVariables.chosenFields[currentItinerary.value] = false;
        }
    }
}

var domCommEvents = {
    setListener: function() {
        this.deleteItineraryEvent();
        this.duplicateItineraryEvent();
    },
    deleteItineraryEvent: function () {
        $("#delete-itinerary").on("click", { "status": "deleted" }, dommCommEventsProcessor.processMultiChangeStatusEvent);
    },
    duplicateItineraryEvent: function () {
        $("#dulicate-itinerary").on("click", {}, dommCommEventsProcessor.processMultiDuplicationEvent);
    }

}

var dommCommEventsProcessor = {
    processMultiChangeStatusEvent: function(event) {
        var status = event.data.status;
        var statusShow = helper.changeItineraryStatusDisplay(status);
        if(!confirm("Are you sure to change the itinerary status as " + statusShow + "?")) {
            return null;
        }
        var href = location.href;
        var datum = {
            "operation": "multi_change_statuses",
            "status": status,
            "object_id": helper.collectChosenFields(),
        };
        //commModule.postData(href, datum, dommCommEventsCallBack.processMultiChangeStatusSuccessCallBack, helper.genaralFailNotification);
        //globalVariables.cleanChosenFields();
        //eventQueue.addEvent(event);
    },

    processMultiDuplicationEvent: function(event) {
        var href = location.href;
        var datum = {
            "operation": "duplicate_itineraries",
            "object_id": helper.collectChosenFields(),
        };
        commModule.postData(href, datum, helper.genaralSuccessNotification, helper.genaralFailNotification);
        globalVariables.cleanChosenFields();
        eventQueue.addEvent(event);
    }
}

var dommCommEventsCallBack = {
    processMultiChangeStatusSuccessCallBack: function(result) {
        if (!result.success) {
            alert("Status NOT updated! Reason: " + result.server_info + ".");
            return null;
        }
        globalVariables.cleanChosenFields();
        var ids = result.id;
        for(var index in ids) {
            $("#itinerary-id-" + ids[index]).css("display", "none");
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
    genaralFailNotification: function (result) {
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
    changeItineraryStatusDisplay: function(status) {
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
    CHANGE_TIME_DESCRIPTION: "Change Time",
}

