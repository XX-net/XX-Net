/**
 * @fileoverview Supporting Javascript for the blobstore viewer.
 */

function checkAllEntities() {
  var check = $('#allkeys').prop('checked');
  $('input[name="blob_key"]').attr('checked', check);
  updateDeleteButtonAndCheckbox();
}

function updateDeleteButtonAndCheckbox() {
  var checkboxes = $('input[name="blob_key"]');
  var checked_checkboxes = checkboxes.filter(':checked');

  if (checked_checkboxes.length) {
    $('#delete_button').removeAttr('disabled');
    $('#delete_button').removeClass('disabled');
  } else {
    $('#delete_button').attr('disabled', 'disabled');
    $('#delete_button').addClass('disabled');
  }

  $('#allkeys').attr('checked', checkboxes.length == checked_checkboxes.length);
}

function displayInline(contentUrl) {
  var iframe =
      '<iframe src="' + contentUrl + '" class="inlined-content"></iframe>';
  $('#inlined_content').html(iframe);
}

$(document).ready(function() {
  $('#allkeys').click(checkAllEntities);

  $('input[name="blob_key"]').change(function() {
    updateDeleteButtonAndCheckbox();
  });

  $('[data-action=delete]').click(function() {
    return confirm('Are you sure?');
  });

  $('#display_inline').click(function() {
    var url = $(this).data('content-uri');
    displayInline(url);
  });

  if ($('#delete_button').length) {
    updateDeleteButtonAndCheckbox();
  }
});
