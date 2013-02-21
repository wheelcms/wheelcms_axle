$(document).ready(function() {
    // make rows clickable if they have a data-url
    $("tr.clickrow").live('click', function() {
        document.location = $(this).data('url');
    });
    // enable sorting
    $(".sortable").sortable({
        items: "tr.sortablerow"
    });

    // Check if any accordions need to be opened if it contains a form
    // with errors
    $(".control-group.error").each(function(i, v) {
        $(v).parents(".accordion-body").removeClass("collapsed").addClass("collapse").addClass("in");
    });
});
