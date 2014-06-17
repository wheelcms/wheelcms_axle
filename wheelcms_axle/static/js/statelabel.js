mod = angular.module("state_label", []);

/*
 * Display a label with specific style/text depending on the supplied state
 */
mod.directive("state", function() {
    return {
        restrict: 'E',
        template: '<span ng-if="show" class="label {{label}}">{{labeltext}}</span>',
        replace: true,

        scope: {
            'state':'=state'
        },
        controller: function($scope, $element, $attrs) {
            $scope.$watch('state', function(value) {
                $scope.show = true;

                if(value == "modified") {
                    $scope.label = "label-primary";
                    $scope.labeltext = "modified";
                }
                else if(value == "deleted") {
                    $scope.label = "label-danger";
                    $scope.labeltext = "deleted";
                }
                else if(value == "added") {
                    $scope.label = "label-success";
                    $scope.labeltext = "added";
                }
                else {
                    $scope.show = false;
                }
            });
        }
    };
});
