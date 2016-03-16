/**
 * @fileoverview Supporting Javascript for the search viewer.
 * @author sammc@google.com (Sam McNally)
 */
function checkAllEntities() {
  var check = $('#alldocs').prop('checked');
  $('input[name="doc_id"]').attr('checked', check);
  updateDeleteButtonAndCheckbox();
}

function updateDeleteButtonAndCheckbox() {
  var checkboxes = $('input[name="doc_id"]');
  var checked_checkboxes = checkboxes.filter(':checked');

  if (checked_checkboxes.length) {
    $('#delete_button').removeAttr('disabled');
    $('#delete_button').removeClass('disabled');
  } else {
    $('#delete_button').attr('disabled', 'disabled');
    $('#delete_button').addClass('disabled');
  }

  $('#alldocs').attr('checked',
                     checkboxes.length == checked_checkboxes.length);
}

$(document).ready(function() {
  $('#alldocs').click(checkAllEntities);

  $('#delete_button').click(function() {
    return confirm('Are you sure you wish to delete these documents?');
  });

  $('input[name="doc_id"]').change(function() {
    updateDeleteButtonAndCheckbox();
  });

  if ($('#delete_button').length) {
    updateDeleteButtonAndCheckbox();
  }
});
