/**
 * @fileoverview Supporting Javascript for the datastore viewer.
 * @author bquinlan@google.com (Brian Quinlan)
 */
function checkAllEntities() {
  var check = $('#allkeys').prop('checked');
  $('input[name="entity_key"]').attr('checked', check);
  updateDeleteButtonAndCheckbox();
}

function updateDeleteButtonAndCheckbox() {
  var checkboxes = $('input[name="entity_key"]');
  var checked_checkboxes = checkboxes.filter(':checked');

  if (checked_checkboxes.length) {
    $('#delete_button').removeAttr('disabled');
    $('#delete_button').removeClass('disabled');
  } else {
    $('#delete_button').attr('disabled', 'disabled');
    $('#delete_button').addClass('disabled');
  }

  $('#allkeys').attr('checked',
                     checkboxes.length == checked_checkboxes.length);
}

$(document).ready(function() {
  $('#allkeys').click(checkAllEntities);

  $('#create_button').click(function() {
    params = {'kind' : $('#kind_input').attr('value'),
              'next': '{{ request.uri }}'};

    if ($('#namespace_input').length) {
      params['namespace'] = $('#namespace_input').attr('value');
    }

    window.location = '/datastore/edit?' + $.param(params);
    return false;
  });

  $('#delete_button').click(function() {
    return confirm(
        'Are you sure you wish to delete these entities? If your app uses ' +
        'memcache to cache entities (e.g. uses ndb) then you may see stale ' +
        'results unless you flush memcache.');
  });

  $('#memcache_flush_button').click(function() {
    return confirm('Are you sure you want to flush all keys from the cache?');
  });

  $('input[name="entity_key"]').change(function() {
    updateDeleteButtonAndCheckbox();
  });

  if ($('#delete_button').length) {
    updateDeleteButtonAndCheckbox();
  }

  $('kind_input').focus();
});
