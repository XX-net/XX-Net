$(function() {
  var $window = $(window);
  var sectionTop = $('.top').outerHeight() + 20;
  var $createDestroy = $('#switch-create-destroy');

  // initialize highlight.js
  hljs.initHighlightingOnLoad();

  // navigation
  $('a[href*="#"]').on('click', function(event) {
    event.preventDefault();
    var $target = $($(this).attr('href').slice('#'));

    if ($target.length) {
      $window.scrollTop($target.offset().top - sectionTop);
    }
  });

  // initialize all the inputs
  $('input[type="checkbox"], input[type="radio"]')
  .not("[data-switch-no-init]")
  .bootstrapSwitch();

  $('[data-switch-get]').on("click", function() {
    var type = $(this).data('switch-get');

    alert($('#switch-' + type).bootstrapSwitch(type));
  });

  $('[data-switch-set]').on('click', function() {
    var type = $(this).data('switch-set');

    $('#switch-' + type).bootstrapSwitch(type, $(this).data('switch-value'));
  });

  $('[data-switch-toggle]').on('click', function() {
    var type = $(this).data('switch-toggle');

    $('#switch-' + type).bootstrapSwitch('toggle' + type.charAt(0).toUpperCase() + type.slice(1));
  });

  $('[data-switch-set-value]').on('input', function(event) {
    event.preventDefault();
    var type = $(this).data('switch-set-value');
    var value = $.trim($(this).val());

    if ($(this).data('value') == value) {
      return;
    }

    $('#switch-' + type).bootstrapSwitch(type, value);
  });

  $('[data-switch-create-destroy]').on('click', function() {
    var isSwitch = $createDestroy.data('bootstrap-switch');

    $createDestroy.bootstrapSwitch(isSwitch ? 'destroy' : null);
    $(this).button(isSwitch ? 'reset' : 'destroy');
  });
});
