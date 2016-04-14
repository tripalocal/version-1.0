# Po files cannot have computed values, so remember to change the text in po file correspondingly
REQUEST_SENT_NOTIFY_HOST = "Tripalocal: {} has requested your {} on {}. Please respond within 48 hours or {} will be refunded"
REQUEST_SENT_NOTIFY_CUSTOMER = "Tripalocal: You have requested {}'s {} at {}, further information will be provided shortly."

BOOKING_CONFIRMED_NOTIFY_CUSTOMER = "Tripalocal: Your booking for {exp_title} with {host_name} at {exp_datetime} has been confirmed."
BOOKING_CONFIRMED_NOTIFY_HOST = "Tripalocal: You have a confirmed booking request for {exp_title} sent by {customer_name} at {exp_datetime}."

BOOKING_CANCELLED_NOTIFY_CUSTOMER = "Tripalocal: Your booking request for {exp_title} at {exp_datetime} with " \
                                    "{host_name} has been cancelled. Refund is on the way."
BOOKING_CANCELLED_NOTIFY_HOST = "Tripalocal: {customer_name}'s booking request for {exp_title} at {exp_datetime} has been cancelled."

REVIEW_NOTIFY_CUSTOMER = "Tripalocal: How was your experience with {host_name}? Please leave a review for your host to help out another traveller planning their perfect trip."

REMINDER_NOTIFY_HOST = "Tripalocal: You've got one booking for {exp_title} with {customer_name} at {exp_datetime} coming soon."
REMINDER_NOTIFY_CUSTOMER = "Tripalocal: Your booking for {exp_title} with {host_name} at {exp_datetime} is coming soon."

MESSAGE_NOTIFY = "Tripalocal: {sender_name}"

REQUEST_REMIND_HOST = "Tripalocal: It's been 24 hours since {guest_name} reached out. Please confirm or decline the request as soon as possible."

skyscanner_flight = "http://flight.tripalocal.com/{language}/flights#/result?originplace={origin}&destinationplace={destination}&outbounddate={outbound}&inbounddate={inbound}&cabinclass={cabinclass}&adults={adults}&children={children}&infants={infants}&currency={currency}&newWindow={new}"

class ItineraryStatus():
    Deleted = "deleted"
    Draft = "draft"
    Ready = "ready"
    Paid = "paid"
    Allowed_Status = [Deleted, Draft, Ready, Paid]

class ProductType():
    Private = "PrivateProduct"
    Public = "PublicProduct"
    Flight = "Flight"
    Transfer = "Transfer"
    Accommodation = "Accommodation"
    Restaurant = "Restaurant"
    Suggestion = "Suggestion"
    Price = "Price"

class CityCode():
    Melbourne = "MEL"
    Sydney = "SYD"
    Brisbane = "BNE"
    Goldcoast = "OOL"
    Cairns = "CNS"
    Adelaide = "ADL"
    Canberra = "CBR"
    Perth = "PER"
    Darwin = "DRW"
    Hobart = "HBA"
    Alicesprings = "ASP"
    Queenstown = "ZQN"
    Auckland = "AKL"
    Christchurch= "CHC"
    Wellington = "WLG"