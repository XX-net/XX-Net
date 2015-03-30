

$("#wide_screen").click(function() {
    if($("#nav_container").hasClass("container")){
        $("#nav_container").addClass("container-fluid")
        $("#nav_container").removeClass("container")

        $("#content_container").addClass("container-fluid")
        $("#content_container").removeClass("container")

        $("#wide_screen").attr('src',"/img/narrow-screen.png")
    }else{
        $("#nav_container").addClass("container")
        $("#nav_container").removeClass("container-fluid")

        $("#content_container").addClass("container")
        $("#content_container").removeClass("container-fluid")
        $("#wide_screen").attr('src',"/img/wide-screen2.png")
    }
});