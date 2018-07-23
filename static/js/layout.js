$(document).ready(function () {
    $("#header_search button").on("click", function () {
        window.location.replace("/search/" + $("#header_search input").val());
    });

    $("#header_search input").on("keypress", function (e) {
        if(e.keyCode == 13) {
            window.location.replace("/search/" + $("#header_search input").val());
        }
    });
    $("#side_search button").on("click", function () {
        window.location.replace("/search/" + $("#side_search input").val());
    });

    $("#side_search input").on("keypress", function (e) {
        if(e.keyCode == 13) {
            window.location.replace("/search/" + $("#side_search input").val());
        }
    });
});