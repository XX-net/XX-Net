/**
 * Created by debian on 12/26/14.
 */

function clean_menu_active(){
    $("#li_goagent_status").removeClass("active")
    $("#li_goagent_config").removeClass("active")
    $("#li_goagent_deploy").removeClass("active")
    $("#li_goagent_log").removeClass("active")
    $("#li_config").removeClass("active")
    $("#li_about").removeClass("active")
}

$( "#goagent_status" ).click(function() {
    $( "#right_content" ).load( "block/goagent/status.html" );
    clean_menu_active()
    $("#li_goagent_status").addClass("active")
});
$( "#goagent_config" ).click(function() {
    $( "#right_content" ).load( "block/goagent/config.html" );
    clean_menu_active()
    $("#li_goagent_config").addClass("active")
});
$( "#goagent_deploy" ).click(function() {
    $( "#right_content" ).load( "block/goagent/deploy.html" );
    clean_menu_active()
    $("#li_goagent_deploy").addClass("active")
});
$( "#goagent_log" ).click(function() {
    $( "#right_content" ).load( "block/goagent/logging.html" );
    clean_menu_active()
    $("#li_goagent_log").addClass("active")
});
$( "#config" ).click(function() {
    $( "#right_content" ).load( "block/config.html" );
    clean_menu_active()
    $("#li_config").addClass("active")
});
$( "#about" ).click(function() {
    $( "#right_content" ).load( "block/about.html" );
    clean_menu_active()
    $("#li_about").addClass("active")
});

$( "#right_content" ).load( "block/goagent/status.html" );