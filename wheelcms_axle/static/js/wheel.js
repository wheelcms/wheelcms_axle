$(document).ready(function() {
    // make rows clickable if they have a data-url
    $(".clickrow").live('click', function() {
        document.location = $(this).data('url');
    });

    // Check if any accordions need to be opened if it contains a form
    // with errors
    $(".control-group.error").each(function(i, v) {
        $(v).parents(".accordion-body").removeClass("collapsed").addClass("collapse").addClass("in");
    });
});

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
        }
    }
});
