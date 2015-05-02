/* String format */
String.prototype.format = function() {
    var newStr = this, i = 0;
    while (/%s/.test(newStr)) {
        newStr = newStr.replace("%s", arguments[i++])
    }
    return newStr;
}

function title(title) {
    $('#title').text(title);
}

function tip(message, type) {
    $('.message', '.alert').html(message);
    $('.alert').removeClass('alert-error');
    $('.alert').removeClass('alert-success');
    $('.alert').removeClass('hide');
    $('.alert').addClass('alert-' + type);
}
