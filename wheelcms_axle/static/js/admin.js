app = angular.module('wheelcms-admin', ['ui.bootstrap'],
 function ($interpolateProvider) {
    $interpolateProvider.startSymbol('<[');
    $interpolateProvider.endSymbol(']>');
});

app.controller('AdminCtrl', function($scope) {
});

