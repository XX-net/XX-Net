/**
 * @fileoverview Supporting Javascript for the datastore editor.
 * @author bquinlan@google.com (Brian Quinlan)
 */
$(document).ready(function() {
  $('#delete_button').click(function() {
    return confirm(
        'Are you sure you wish to delete this entity? If your app uses ' +
        'memcache to cache entities (e.g. uses ndb) then you may see stale ' +
        'results unless you flush memcache.');
  });
});
