$(document).ready(function() {
    initDOMPresentation();
    domCommEvents.setListener();
    domPresentationEvents.setListner();
});

function initDOMPresentation() {
    // Hide the status select box.
    $("select[id^='select-status-']").hide();
    // Hide the commission input.
    $("input[id^='input-commission-']").hide();
    // Change the hover of active td.
    $("td[id^='td-status-']").hover(function() {
        $(this).css("cursor", "pointer");
    });
    $("td[id^='td-commission-']").hover(function() {
        $(this).css("cursor", "pointer");
    });
    $("td[id^='td-status-']").each(function() {
       var currentP = $(this).children("p");
       currentP.css("color", helper.mapStatusToColor(currentP.text()));
    });
}

var domPresentationEvents = {
    setListner: function() {
        var allStatusTdTags = $("td[id^='td-status-']");
        var allCommissionTdTags = $("td[id^='td-commission-']");
        allStatusTdTags.on("dblclick", {toElementName: "#select-status-"}, presentationUtil.swapInterfaceInTable);
        allCommissionTdTags.on("dblclick", {toElementName: "#input-commission-"}, presentationUtil.swapInterfaceInTable);
    }
}

var domCommEvents = {
    setListener: function() {
        this._statusTdEvent();
    },

    _statusTdEvent: function() {
        var allStatusSelectTag = $("select[id^='select-status-']");
        allStatusSelectTag.each(function() {
            var currentSelect = $(this);
            var object_id = helper.getLineIdByElementId(currentSelect.attr("id"));
            currentSelect.change(function() {
            href = location.href,
            datum = {
                "operation": "post_status",
                "status": currentSelect.val(),
                "object_id": object_id,
            };
            successCallback = helper.genaralSuccessNotification;
            failCallback = helper.genaralFailNotification;
            commModule.postData(href, datum, successCallback, failCallback);
            $("#td-status-" + object_id + " p").css("color", helper.mapStatusToColor(currentSelect.val()));
            });
        });
    }
}

var presentationUtil = {
    swapInterfaceInTable: function(event) {
        // Get the current elements.
        var currentTd = $(event.target);
        var toElementName = event.data.toElementName;
        var currentId = helper.getLineIdByElementId(currentTd.attr("id"));
        var currentUI = $(toElementName + currentId);
        var currentValue = currentTd.children("p");
        // Hide current UI.
        if(currentUI.css("display") == "none") {
            currentUI.css("display", "block");
            currentUI.val(currentValue.text());
            currentValue.text("");
        } else {
            currentUI.css("display", "none");
            currentValue.text(currentUI.val());
        }
    }
}

var commModule = {
    postData: function(href, datum, successCallback, failCallback) {
        $.post(href, $.extend({
            'csrfmiddlewaretoken': $("[name='csrfmiddlewaretoken']")[0].value
        }, datum))
            .done(successCallback)
            .fail(failCallback);
    }
}

var helper = {
    getLineIdByElementId: function(name) {
        // Id is the part following the last '-' in a DOM name.
        return name.split("-").pop();
    },
    genaralSuccessNotification: function(result) {
        alert(result.success);
    },
    genaralFailNotification: function() {
        alert(result.success);
    },
    mapStatusToColor: function(status) {
        switch (status) {
            case "Listed":
                return "green";
            case "Unlisted":
                return "red";
            case "Draft":
                return "black";
            case "Submitted":
                return "yellow";
        }
    }
}

