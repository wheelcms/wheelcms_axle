$(document).ready(function() {
    // make rows clickable if they have a data-url
    $(".clickrow").on('click', function() {
        document.location = $(this).data('url');
    });

    // Check if any accordions need to be opened if it contains a form
    // with errors
    $(".accordion-inner:has('.has-error')").each(function(i, v) {
        $(v).parent().addClass("in");
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

/*
 * AngularJS browser modal rewrite
 */

app = angular.module('wheelcms-admin', function ($interpolateProvider) {
    $interpolateProvider.startSymbol('<[');
    $interpolateProvider.endSymbol(']>');
});

app.controller('AdminCtrl', function($scope) {
});

function props_or_browser(path, type, options, callback) {
    if(path) {
        var scope = angular.element($("#detailsModal").get()).scope();
        scope.$apply(function() { scope.show(); });

    }
    else {
        var scope = angular.element($("#browseModal").get()).scope();
        scope.$apply(function() { scope.show(); });
    }
}

app.factory("PropsModal", function() {
});

app.factory("BrowseModal", function() {
});

app.controller('PropsCtrl', ["$scope", "PropsModal",
                             function($scope, PropsModal) {
    $scope.show = function() {
        console.log("Props Show");
    };
}]);

app.controller('BrowseCtrl', ["$scope", "BrowseModal", "$element",
                              function($scope, BrowseModal, $element) {
    $scope.show = function(path, mode, options, callback) {
        console.log("Browse Show");
        $($element).modal();

        /* depending on model show/hide tabs */


    };
}]);
