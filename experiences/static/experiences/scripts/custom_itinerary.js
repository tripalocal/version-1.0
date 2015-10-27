$(function() {
  // Initialize popovers
  $('[data-toggle="popover"]').popover();

  // Draggable logic
  $(".column").sortable({
    connectWith: ".column",
    handle: ".portlet-header",
    cancel: ".portlet-toggle",
    start: function(event, ui) {
      ui.item.addClass('tilt');
      tilt_direction(ui.item);
    },
    stop: function(event, ui) {
      ui.item.removeClass("tilt");
      $("html").unbind('mousemove', ui.item.data("move_handler"));
      ui.item.removeData("move_handler");
    }
  });

  function tilt_direction(item) {
    var left_pos = item.position().left,
      move_handler = function(e) {
        if (e.pageX >= left_pos) {
          item.addClass("right");
          item.removeClass("left");
        } else {
          item.addClass("left");
          item.removeClass("right");
        }
        left_pos = e.pageX;
      };
    $("html").bind("mousemove", move_handler);
    item.data("move_handler", move_handler);
  }

  $(".portlet")
    .addClass("ui-widget ui-widget-content ui-helper-clearfix ui-corner-all")
    .find(".portlet-header")
    .addClass("ui-widget-header ui-corner-all")
    .prepend("<span class='ui-icon ui-icon-minusthick portlet-toggle'></span>");

  $(".portlet-toggle").click(function() {
    var icon = $(this);
    icon.toggleClass("ui-icon-minusthick ui-icon-plusthick");
    icon.closest(".portlet").find(".portlet-content").toggle();
  });

  //Add item buttons (left panel)
  $("#add-flight-btn").click(function() {
    $("#flight_column").hide();
    $("#add-flight").show();
  });
  $("#add-flight-cancel").click(function() {
    $("#flight_column").show();
    $("#add-flight").hide();
  });

  $("#add-transfer-btn").click(function() {
    $("#transfer_column").hide();
    $("#add-transfer").show();
  });
  $("#add-transfer-cancel").click(function() {
    $("#transfer_column").show();
    $("#add-transfer").hide();
  });

  $("#add-accommodation-btn").click(function() {
    $("#accommodation_column").hide();
    $("#add-accommodation").show();
  });
  $("#add-accommodation-cancel").click(function() {
    $("#accommodation_column").show();
    $("#add-accommodation").hide();
  });

  $("#add-restaurant-btn").click(function() {
    $("#restaurant_column").hide();
    $("#add-restaurant").show();
  });
  $("#add-restaurant-cancel").click(function() {
    $("#restaurant_column").show();
    $("#add-restaurant").hide();
  });

  $("#add-suggestion-btn").click(function() {
    $("#suggestion_column").hide();
    $("#add-suggestion").show();
  });
  $("#add-suggestion-cancel").click(function() {
    $("#suggestion_column").show();
    $("#add-suggestion").hide();
  });

  $("#add-pricing-btn").click(function() {
    $("#pricing_column").hide();
    $("#add-pricing").show();
  });
  $("#add-pricing-cancel").click(function() {
    $("#pricing_column").show();
    $("#add-pricing").hide();
  });
});
