mod = angular.module('tagInputWrapper', ['ngTagsInput']);

/*
 * Wrap the <tags-input> tag and link it to a hidden field, so the
 * tags can be initialized and send back as an ordinary form field
 */
mod.directive('inputwrap', function($rootScope, $http) {
    return {
        restrict: 'E',
        transclude: true,
        scope: {
            flat_tags: '@value'
        },
        controller: function($scope, $element, $attrs) {
            $scope.tags = $scope.flat_tags.split(",");

            $scope.loadTags = function(query) {
                return $http.get($rootScope.urlbase + '+tags/?query=' + query);
            };

            $scope.$watch(function() { return $scope.tags; },
                function(newVal, oldVal) {
                    var res = [];
                    var i = 0;
                    for(i = 0; i < newVal.length; i++) {
                        res.push(newVal[i].text);
                    }
                    $scope.flat_tags = res.join();
            }, true);
        },
        template: '<tags-input ng-model="tags">' +
        '<auto-complete source="loadTags($query)"></auto-complete>' +
        '</tags-input>' +
        '<input type="hidden" name="tags" value="<[flat_tags]>">'
    };
});


