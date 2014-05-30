mod = angular.module('toolbar_savebutton', []);

mod.controller('SaveCancelController', function($scope) {
    $scope.save = function() {
        $scope.$emit("toolbar.savebutton.click", {'a':1});
    };
});
