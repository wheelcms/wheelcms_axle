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

app.config(function($locationProvider) {
    // required so we can intercept the #hash
    // http://stackoverflow.com/a/20788246/320057
    $locationProvider.html5Mode(true).hashPrefix('!');
});

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
            templateUrl: 'BrowseModal.html',
            windowClass: "browsemodal",
            controller: "BrowseCtrl",
            resolve: {
                path: function() { return path; },
                type: function() { return type; },
                options: function() { return options; },
                callback: function() { return callback; }
            }
        });
        modalInstance.result.then(function (selected) {
            if(selected == "upload") {
                openUploadModal("");
            }
            else {
                console.log("X");
                console.log(selected);
                options = {};
                var args = options || {};
                args.download = false;

                // open link or image properties
                //
                //callback(selected, options); // more or less
                // newselection is true if a selection has been made in the
                // browser, false for existing selections that need update
                var newselection = true;
                $scope.open_props(selected, type, options, callback, newselection);
            }
        }, function () {
            // dismissed
        });
    };

    function openUploadModal(path) {
        var modalInstance = $modal.open({
            templateUrl: 'UploadModal.html',
            controller: "UploadCtrl",
            resolve: {
                path: function() { return path; }
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
                newselection: function() { return newselection; }
            }
        });
        modalInstance.result.then(function (selected) {
            console.log("props selected");
            console.log(selected);
            if(callback) {
                callback(selected.path, selected.props);
            }
        }, function (reason) {
            // reason = change or cancel
            console.log("dismiss");
            console.log(reason);
            // dismissed
        });

    };

    //$scope.open_browser("", "link", {}, function(res) { console.log("RESULT " + res); });
});

app.factory("PropsModal", function() {
});

app.factory("BrowseModal", function() {
});

/*
 * Is newselection nodig? handler gebruiket het om default title in te stellen,
 * wordt deze bij non-newselection niet overschreven?
 *
 * Is callback nodig? return details ipv. vanuit props callback aanroepen?
*/


app.controller('PropsCtrl',
               ["$scope", "$modalInstance", "$compile", "$http", "PropsModal", "path", "type", "options", "newselection",
               function($scope, $modalInstance, $compile, $http, PropsModal, path, type, options, newselection) {

    console.log("Props", options);

    $scope.propsform = options;

    function init(type, options, callback) {
        var params = angular.copy(options);
        params.path = path;
        params.type = type;
        params.newselection = newselection;

        $http.get($scope.urlbase + "panel_selection_details",
                  {params: params}
                  ).success(
          function(data, status, headers, config) {
              console.log(data);
              var template = data.template;
              var initial = data.initialdata;
              $scope.propsform = initial;
              // passed properties are always leading
              angular.extend($scope.propsform, options);
              var propsform = $("#detailsModalBody");
              propsform.html($compile(template)($scope));
          });
    }

    init(type, options);

    $scope.cancel = function() {
      $modalInstance.dismiss('cancel');
    };

    $scope.change = function() {
      $modalInstance.dismiss('change');
    };


    $scope.ok = function() {
        console.log("OK props");
        console.log($scope.propsform);
        $modalInstance.close({path:path, props:$scope.propsform});
    };

}]);
app.controller('UploadCtrl',
               ["$scope", "$modalInstance", "PropsModal", "path",
               function($scope, $modalInstance, PropsModal, path) {
    $scope.show = function(type, options, callback) {
        console.log("Upload Show");
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
        return true;
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

app.controller('EditCtrl', function($rootScope, $scope, $location) {
    $scope.advanced_open = $location.hash() == "collapseadvanced";
});

