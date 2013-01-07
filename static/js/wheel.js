$(document).ready(function() {
    // make rows clickable if they have a data-url
    $("tr.clickrow").live('click', function() {
        document.location = $(this).data('url');
    });
    // enable sorting
    $(".sortable").sortable();

});
