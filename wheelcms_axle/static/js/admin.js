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

    console.log(path);
    if(path) {
        scope.$apply(function() { scope.open_props(path, type, options, callback, false); });
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
            templateUrl: 'UploadModal.html',
            windowClass: "",
            controller: "UploadCtrl",
            resolve: {
                path: function() { return path; },
                type: function() { return type; },
                options: function() { return options; },
                callback: function() { return callback; }
            }
        });
        modalInstance.result.then(function (selected) {
            if(selected == "upload") {
                openUploadModal();
            }
            else {
                console.log("X");
                console.log(selected);
                callback(selected); // more or less
            }
        }, function () {
            // dismissed
        });
    };

    function openUploadModal() {
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

    }

    $scope.open_props = function(path, type, options, callback, newselection) {
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

        }, function () {
            console.log("dismiss");
            // dismissed
        });

    };

    $scope.open_browser("", "link", {}, function(res) { console.log(res); });
});

app.factory("PropsModal", function() {
});

app.factory("BrowseModal", function() {
});

app.controller('PropsCtrl',
               ["$scope", "$modalInstance", "PropsModal", "path", "type", "options",
               function($scope, $modalInstance, PropsModal, path, type, options) {
    $scope.show = function(type, options, callback) {
        console.log("Props Show");
    };
}]);

/*
 * selectable
 * - currently encoded in ng-click-openURL. But also returned by panels, latter suffices?
 */
app.controller('BrowseCtrl',
               ["$scope", "$modalInstance", "$compile", "$http", "BrowseModal", "path",
                "type", "options",
               function($scope, $modalInstance, $compile, $http, BrowseModal,
                        path, type, options) {

    var startpath = ""; // the initial path

    $scope.selected = {};
    $scope.path = '';
    $scope.mode = 'link';
    $scope.selectable = false;

    $scope.tabs = [ {active: true, disabled: false },
                    {active: false, disabled: false },
                    {active: false, disabled: false }];

    function init(path, mode, options) {

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
            load_panels(path || '');

        }
        else if($scope.link_type) {
            $scope.tabs[1].active = true;
            $scope.selected.external_url = path;
        }
        else {
            $scope.tabs[2].active = true;
        }

        $scope.path = path.replace(/\/\+[\w_\-]+$/, '');
        startpath = $scope.path;
        $scope.mode = mode;

        /* depending on internal/external path, open local/browse or 
         * external tab
         */

    }
    function load_panels(path) {
        $http.get($scope.urlbase + "panel",
                  {params: {
                    path: path,
                    original: startpath,
                    mode: $scope.mode
                  }}
                  ).success(
        function(data, status, headers, config) {
            var panels = data.panels;
            var crumbs = data.crumbs;
            var upload = data.upload;
            $scope.selectable = data.selectable;
            $scope.path = data.path;

            for(var i=0; i < 3; i++) {
                $(".panel"+i).empty();
            }

            for(var i=0; i < panels.length; i++) {
                var paneldata = panels[i];
                var panel = $(".panel" + i);
                panel.html($compile(paneldata)($scope));
            }
            $(".crumbcontainer").html($compile(crumbs)($scope));
        });
    }

    init(path, type, options);

    $scope.openURL = function(newpath) {
        console.log("klik " + newpath);
        load_panels(newpath);
        $scope.path = newpath;
    };

    /*
     * Enablers/disablers
     */
    $scope.select_enabled = function() {
        if($scope.link_type && $scope.selected.external_url) {
            return true;
        }
        else if($scope.browse && $scope.selectable) {
            return true;
        }
        return false;
    };

    $scope.upload_enabled = function() {
        return false;
    };

    /*
     * Button actions
     */
    $scope.ok = function () {
      console.log("OK " + $scope.path);
      $modalInstance.close($scope.path);
    };

    $scope.upload = function () {
      $modalInstance.close("upload");
    };

    $scope.cancel = function () {
      $modalInstance.dismiss('cancel');
    };
}]);

