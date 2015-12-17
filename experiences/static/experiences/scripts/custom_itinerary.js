
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
  $("#sortable").sortable({
    connectwith: "#sortable",
    placeholder: "drop-placeholder-sm",
    start: function(event, ui) {
      ui.item.addClass('tilt');
      tilt_direction(ui.item);
    },
    stop: function(event, ui) {
      ui.item.removeClass("tilt");
      $("html").unbind('mousemove', ui.item.data("move_handler"));
      ui.item.removeData("move_handler");
      update_dates();
    }
  });
}

// Tilting of draggable components
function tilt_direction(item) {
  var left_pos = item.position().left,
    move_handler = function(e) {
      if (e.pageX >= (left_pos + 3)) {
        item.addClass("right");
        item.removeClass("left");
      } else if (e.pageX < (left_pos - 3)) {
        item.addClass("left");
        item.removeClass("right");
      }
      left_pos = e.pageX;
    };
  $("html").bind("mousemove", move_handler);
  item.data("move_handler", move_handler);
}

function init_slider(item) {
  var fixedPriceMin = parseFloat(item.find(".fixed-price-min").text());
  var fixedPriceMax = parseFloat(item.find(".fixed-price-max").text());
  var priceMin = parseFloat(item.find(".price-min").text());
  var priceMax = parseFloat(item.find(".price-max").text());

  var $fixedPrice = item.find(".fixed-price");
  var $price = item.find(".price");
  var $sliderPriceBase = item.find(".slider-price-base");
  var $sliderPricePP = item.find(".slider-price-pp");

  $sliderPriceBase.slider({
    min: fixedPriceMin,
    max: fixedPriceMax,
    value: (fixedPriceMin + fixedPriceMax)/2,
    slide: function( event, ui ) {
        $fixedPrice.val( ui.value );
        update_price_title();
      }
  });
  $sliderPricePP.slider({
    min: priceMin,
    max: priceMax,
    value: (priceMin + priceMax)/2,
    slide: function( event, ui ) {
        $price.val( ui.value );
        update_price_title();
      }
  });
  $fixedPrice.val( $sliderPriceBase.slider( "value" ) );
  $price.val( $sliderPricePP.slider( "value" ) );
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
    $(this).hide();
    $("#flight_column").hide();
    $("#add-flight").fadeIn();
    set_new_item_location('flight');
  });
  $("#add-flight-cancel").click(function() {
    $("#add-flight-btn").fadeIn();
    $("#flight_column").fadeIn();
    $("#add-flight").hide();
  });

  $("#add-transfer-btn").click(function() {
    $(this).hide();
    $("#transfer_column").hide();
    $("#add-transfer").fadeIn();
    set_new_item_location('transfer');
  });
  $("#add-transfer-cancel").click(function() {
    $("#add-transfer-btn").fadeIn();
    $("#transfer_column").fadeIn();
    $("#add-transfer").hide();
  });

  $("#add-accommodation-btn").click(function() {
    $(this).hide();
    $("#accommodation_column").hide();
    $("#add-accommodation").fadeIn();
    set_new_item_location('accommodation');
  });
  $("#add-accommodation-cancel").click(function() {
    $("#add-accommodation-btn").fadeIn();
    $("#accommodation_column").fadeIn();
    $("#add-accommodation").hide();
  });

  $("#add-restaurant-btn").click(function() {
    $(this).hide();
    $("#restaurant_column").hide();
    $("#add-restaurant").fadeIn();
    set_new_item_location('restaurant');
  });
  $("#add-restaurant-cancel").click(function() {
    $("#add-restaurant-btn").fadeIn();
    $("#restaurant_column").fadeIn();
    $("#add-restaurant").hide();
  });

  $("#add-suggestion-btn").click(function() {
    $(this).hide();
    $("#suggestion_column").hide();
    $("#add-suggestion").fadeIn();
    set_new_item_location('suggestion');
  });
  $("#add-suggestion-cancel").click(function() {
    $("#add-suggestion-btn").fadeIn();
    $("#suggestion_column").fadeIn();
    $("#add-suggestion").hide();
  });

  $("#add-pricing-btn").click(function() {
    $(this).hide();
    $("#pricing_column").hide();
    $("#add-pricing").fadeIn();
  });
  $("#add-pricing-cancel").click(function() {
    $("#add-pricing-btn").fadeIn();
    $("#pricing_column").fadeIn();
    $("#add-pricing").hide();
  });
});
