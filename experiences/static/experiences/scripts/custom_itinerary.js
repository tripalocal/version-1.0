
// Enable columns to snap in draggable components
function init_drag() {
  $(".column").sortable({
    connectWith: ".column",
    placeholder: "drop-placeholder",
    start: function(event, ui) {
      ui.item.addClass('tilt');
      tilt_direction(ui.item);
    },
    stop: function(event, ui) {
      ui.item.removeClass("tilt");
      $("html").unbind('mousemove', ui.item.data("move_handler"));
      ui.item.removeData("move_handler");
      update_price_title(event, ui);
    }
  });
}

// Tilting of draggable components
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

$(document).ready(function() {
  // Initialize popovers
  $('[data-toggle="popover"]').popover();

  // Filter buttons
  $(document).on("click", "#cancel-add-adults", function() {
    $("#add-adults").popover("hide");
  });
  $(document).on("click", "#submit-add-adults", function() {
    update_guests();
  });

  // Add item buttons (left panel)
  $("#add-flight-btn").click(function() {
    $("#flight_column").hide();
    $("#add-flight").fadeIn();
    set_new_item_location('flight');
  });
  $("#add-flight-cancel").click(function() {
    $("#flight_column").fadeIn();
    $("#add-flight").hide();
  });

  $("#add-transfer-btn").click(function() {
    $("#transfer_column").hide();
    $("#add-transfer").fadeIn();
    set_new_item_location('transfer');
  });
  $("#add-transfer-cancel").click(function() {
    $("#transfer_column").fadeIn();
    $("#add-transfer").hide();
  });

  $("#add-accommodation-btn").click(function() {
    $("#accommodation_column").hide();
    $("#add-accommodation").fadeIn();
    set_new_item_location('accommodation');
  });
  $("#add-accommodation-cancel").click(function() {
    $("#accommodation_column").fadeIn();
    $("#add-accommodation").hide();
  });

  $("#add-restaurant-btn").click(function() {
    $("#restaurant_column").hide();
    $("#add-restaurant").fadeIn();
    set_new_item_location('restaurant');
  });
  $("#add-restaurant-cancel").click(function() {
    $("#restaurant_column").fadeIn();
    $("#add-restaurant").hide();
  });

  $("#add-suggestion-btn").click(function() {
    $("#suggestion_column").hide();
    $("#add-suggestion").fadeIn();
    set_new_item_location('suggestion');
  });
  $("#add-suggestion-cancel").click(function() {
    $("#suggestion_column").fadeIn();
    $("#add-suggestion").hide();
  });

  $("#add-pricing-btn").click(function() {
    $("#pricing_column").hide();
    $("#add-pricing").fadeIn();
  });
  $("#add-pricing-cancel").click(function() {
    $("#pricing_column").fadeIn();
    $("#add-pricing").hide();
  });
});
