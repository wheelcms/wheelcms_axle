/*
 * AngularJS browser modal rewrite
 */

app = angular.module('wheelcms-admin', ['ui.bootstrap'],
 function ($interpolateProvider) {
    $interpolateProvider.startSymbol('<[');
    $interpolateProvider.endSymbol(']>');
});

app.config(['$httpProvider', function($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

    // http://victorblog.com/2012/12/20/make-angularjs-http-service-behave-like-jquery-ajax/
    //
    $httpProvider.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8';
    // Override $http service's default transformRequest
    $httpProvider.defaults.transformRequest = [function(data)
    {
      /**
       * The workhorse; converts an object to x-www-form-urlencoded serialization.
       * @param {Object} obj
       * @return {String}
       */ 
      var param = function(obj)
      {
        var query = '';
        var name, value, fullSubName, subName, subValue, innerObj, i;
        
        for(name in obj)
        {
          value = obj[name];
          
          if(value instanceof Array)
          {
            for(i=0; i<value.length; ++i)
            {
              subValue = value[i];
              fullSubName = name + '[' + i + ']';
              innerObj = {};
              innerObj[fullSubName] = subValue;
              query += param(innerObj) + '&';
            }
          }
          else if(value instanceof Object)
          {
            for(subName in value)
            {
              subValue = value[subName];
              fullSubName = name + '[' + subName + ']';
              innerObj = {};
              innerObj[fullSubName] = subValue;
              query += param(innerObj) + '&';
            }
          }
          else if(value !== undefined && value !== null)
          {
            query += encodeURIComponent(name) + '=' + encodeURIComponent(value) + '&';
          }
        }
        
        return query.length ? query.substr(0, query.length - 1) : query;
      };
      
      return angular.isObject(data) && String(data) !== '[object File]' ? param(data) : data;
    }];
  }
]);
/* csrf support */
/*app.run(function ($http, $cookies) {
    $http.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];
}); */

/*
 * Fix for broken <select> tag
 * http://jsfiddle.net/alalonde/dZDLg/9/ https://github.com/angular/angular.js/issues/638
 */
app.directive('optionsDisabled', function($parse) {
    var disableOptions = function(scope, attr, element, data, fnDisableIfTrue) {
        // refresh the disabled options in the select element.
        $("option[value!='?']", element).each(function(i, e) {
            var locals = {};
            locals[attr] = data[i];
            $(this).attr("disabled", fnDisableIfTrue(scope, locals));
        });
    };
    return {
        priority: 0,
        require: 'ngModel',
        link: function(scope, iElement, iAttrs, ctrl) {
            // parse expression and build array of disabled options
            var expElements = iAttrs.optionsDisabled.match(/^\s*(.+)\s+for\s+(.+)\s+in\s+(.+)?\s*/);
            var attrToWatch = expElements[3];
            var fnDisableIfTrue = $parse(expElements[1]);
            scope.$watch(attrToWatch, function(newValue, oldValue) {
                if(newValue) {
                    disableOptions(scope, expElements[2], iElement, newValue, fnDisableIfTrue);
                }
            }, true);

            // handle model updates properly
            scope.$watch(iAttrs.ngModel, function(newValue, oldValue) {
                var disOptions = $parse(attrToWatch)(scope);
                if(newValue) {
                    disableOptions(scope, expElements[2], iElement, disOptions, fnDisableIfTrue);
                }
            });
        }
    };
});

/*
 * props_or_browser is invoked by TinyMCE. Hook it into our AngularJS
 * controllers
 */
function props_or_browser(path, type, options, callback) {
    var scope =  angular.element($("#wheelcms-admin").get()).scope();

    if(path) {
        scope.$apply(function() { scope.open_props(path, type, options, callback); });

    }
    else {
        scope.$apply(function() { scope.open_browser(path, type, options, callback); });
    }
}

/*
 * Admin wide controller, bootstraps the calling of specific
 * dialogs
 */
app.controller('AdminCtrl', function($rootScope, $scope, $modal) {
    $scope.init = function(urlbase) {
        $rootScope.urlbase = urlbase;
    };

    $scope.open_browser = function(path, type, options, callback) {
        var modalInstance = $modal.open({
            templateUrl: 'BrowseModal.html',
            controller: "BrowseCtrl",
            resolve: {
                path: function() { return path; },
                type: function() { return type; },
                options: function() { return options; },
                callback: function() { return callback; }
            }
        });
        modalInstance.result.then(function (selected) {
            callback(selected); // more or less
        }, function () {
            // dismissed
        });
    };

    $scope.open_props = function(path, type, options, callback) {
        var modalInstance = $modal.open({
            templateUrl: 'PropsModal.html',
            controller: "PropsCtrl",
            resolve: {
                path: function() { return path; },
                type: function() { return type; },
                options: function() { return options; },
                callback: function() { return callback; }
            }
        });
        modalInstance.result.then(function (selected) {
            callback(selected); // more or less
        }, function () {
            // dismissed
        });

    };
});

app.factory("PropsModal", function() {
});

app.factory("BrowseModal", function() {
});

app.controller('PropsCtrl', ["$scope", "PropsModal",
                             function($scope, PropsModal, path, type, properties) {
    $scope.show = function(type, options, callback) {
        console.log("Props Show");
    };
}]);

app.controller('BrowseCtrl', ["$scope", "BrowseModal",
                              function($scope, BrowseModal, path, type, properties) {

    $scope.tabs = [ {active: true, disabled: false },
                    {active: false, disabled: false },
                    {active: false, disabled: false }];

    function init(path, mode, options, callback) {
        console.log("Browse Show");

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

    }

    init(path, type, properties);

}]);

