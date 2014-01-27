/*
 * AngularJS browser modal rewrite
 */

app = angular.module('wheelcms-admin', ['ui.bootstrap'],
 function ($interpolateProvider) {
    $interpolateProvider.startSymbol('<[');
    $interpolateProvider.endSymbol(']>');
});

app.controller('AdminCtrl', function($scope) {
});

function props_or_browser(path, type, options, callback) {
    if(path) {
        var scope = angular.element($("#detailsModal").get()).scope();
        scope.$apply(function() { scope.show(type, options, callback); });

    }
    else {
        var scope = angular.element($("#browseModal").get()).scope();
        scope.$apply(function() { scope.show(path, type, options, callback); });
    }
}

app.factory("PropsModal", function() {
});

app.factory("BrowseModal", function() {
});

app.controller('PropsCtrl', ["$scope", "PropsModal", "$element",
                             function($scope, PropsModal, $element) {
    $scope.show = function(type, options, callback) {
        console.log("Props Show");
        $($element).modal();
    };
}]);

app.controller('BrowseCtrl', ["$scope", "BrowseModal", "$element",
                              function($scope, BrowseModal, $element) {
    $scope.tabs = [ {active: true, disabled: false },
                    {active: false, disabled: false },
                    {active: false, disabled: false }];

    $scope.show = function(path, mode, options, callback) {
        console.log("Browse Show");
        $($element).modal();

        $scope.tabs = [ {active: true, disabled: false },
                        {active: false, disabled: false },
                        {active: false, disabled: false }];

        if(mode == "link") {
            console.log("Link");
            $scope.tabs[1].disabled = false;
            $scope.tabs[2].disabled = true;
        }
        else {
            $scope.tabs[1].disabled = true;
            $scope.tabs[2].disabled = false;
        }

        $scope.link_type = (mode=="link");
        $scope.external_url = "";


        $scope.browse = (path.indexOf('http') !== 0);

        if($scope.browse) {
            $scope.tabs[0].active = true;
        }
        else if($scope.link_type) {
            $scope.tabs[1].active = true;
        }
        else {
            $scope.tabs[2].active = true;
        }
        console.log($scope.tabs);

        
        /* depending on internal/external path, open local/browse or 
         * external tab
         */

    };

}]);
