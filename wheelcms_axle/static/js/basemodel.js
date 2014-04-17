basemodel = angular.module('basemodel', []);

basemodel.factory('BaseModel',
                   ['$filter', '$rootScope', '$q', '$http',
                   function($filter, $rootScope, $q, $http) {

    /*
     * A service that retrieves, manages and saves "data", a collection of
     * individual objects that can be identified using a unique id
     */

    var _data = null;
    var added_ids = 0;

    return {
        method: '--error--',

        handle_data: function(data) { return data; },
        construct_method: function(method) {
            return $rootScope.urlbase + "+" + method + "/";
        },

        retrieve: function() {
            var deferred = $q.defer();
            var m = this;
            if(_data) {
                deferred.resolve(_data);
                return deferred.promise;
            }

            $http.get(this.construct_method(this.method)).success(
                function(data, status, headers, config) {
                    _data = m.handle_data(data);
                    deferred.resolve(data);
                });
            return deferred.promise;
        },


        save: function() {
            var deferred = $q.defer();
            var m = this;
            $http.post($rootScope.urlbase + "+" + this.method + "/", {
                    data:$filter('json')(_data)
            }).success(
                function(data, status, headers, config) {
                    _data = m.handle_data(data);
                    deferred.resolve(data);
                }
            );
            return deferred.promise;
        },

        async: function() {
            return this.retrieve();
        },

        data: function() { return _data; },

        find: function(id) {
                var i;
                for(i = 0; i < _data.existing.length; i++) {
                    if(_data.existing[i].id == id) {
                        return _data.existing[i];
                    }
                }
            },
        add: function(data) {
            _data.existing.unshift(data);
            data.state = "added";
            data.id = "added_" + added_ids++;
            return data.id;
        },
        remove: function(id) {
            var existing = this.find(id);
            existing.state = "deleted";
        },
        update: function(id, data) {
            var existing = this.find(id);
            angular.extend(existing, data);
            if(existing.state != "added") {
                existing.state = "modified";
            }
        }
    };
}]);
