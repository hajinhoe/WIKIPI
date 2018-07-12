$(document).ready(function () {
    $("#side_search button").on("click", function () {
        window.location.replace("/search/" + $("#side_search input").val());
    });

    $("#side_search input").on("keypress", function (e) {
        if(e.keyCode == 13) {
            window.location.replace("/search/" + $("#side_search input").val());
        }
    });

    $("#navbar_search button").on("click", function () {
        window.location.replace("/search/" + $("#navbar_search input").val());
    });

    $("#navbar_search input").on("keypress", function (e) {
        if(e.keyCode == 13) {
            window.location.replace("/search/" + $("#navbar_search input").val());
        }
    });
});