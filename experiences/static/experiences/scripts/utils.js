
function isValidEmailAddress(emailAddress) {
    var pattern = new RegExp( /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/i);
    return pattern.test(emailAddress);
};

function isValidName(name) {
    var pattern = new RegExp(/^['a-z\ ._\u4e00-\u9eff]{1,20}$/i);
    return pattern.test(name);
};

function isValidPhoneNumber(number) {
    var pattern = new RegExp(/^[\+0-9\ ]{10,14}$/);
    return pattern.test(number);
}