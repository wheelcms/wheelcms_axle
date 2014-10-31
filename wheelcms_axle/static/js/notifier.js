notifier = angular.module('notifier', []);

notifier.factory('Notifier', function() {
    var notification = {};

    return {
        notification: function() {
            return notification;
        },
        notify: function(type, message) {
            notification = {type:type, message: message};
        }
    };
});

notifier.controller('NotifierCtrl', function($scope, Notifier) {
    $scope.notification = {};
    $scope.$watch(function(scope) {
                      return Notifier.notification();
                  },
                  function(n, o) {
                      $scope.notification = {}; // clear old
                      $scope.notification[n.type] = n.message;
                  }
    );
});
