function title(title) {
    $('#title').text(title);
}

function tip(message, type, allowOff) {
    if( allowOff === undefined ) {
        allowOff = true;
    }
    if( type === undefined ) {
        type = 'info';
    }

    $('#tip').removeClass('alert-info');
    $('#tip').removeClass('alert-warning');
    $('#tip').removeClass('alert-success');
    $('#tip').removeClass('alert-error');
    $('#tip').removeClass('hide');

    $('#tip').addClass('alert-' + type);

    $('#tip-message').html(message);

    if( allowOff === true ) {
        $('#tip-close').css('display', '');
    } else {
        $('#tip-close').css('display', 'none');
    }
}
function tipClose() {
    $('#tip').addClass('hide');
}
function tipHasClose() {
    return $('#tip').hasClass('hide');
}

$(document).ready(function() {
    $('#tip-close').click(function() {
        tipClose();
    });
});
