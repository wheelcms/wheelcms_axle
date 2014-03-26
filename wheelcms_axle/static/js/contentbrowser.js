contentbrowser = angular.module('contentbrowser', []);

/*
 * props_or_browser is invoked by TinyMCE. Hook it into our AngularJS
 * controllers
 */
function props_or_browser(path, type, options, callback) {
    var scope =  angular.element($("#wheelcms-admin").get()).scope();

    scope.$apply(
        function() {
            scope.select_content(path, type, options, callback);
        }
    );
}

/*
 * Admin wide controller, bootstraps the calling of specific
 * dialogs
 */
app.controller('AdminCtrl', function($rootScope, $scope, $modal) {
    $scope.init = function(urlbase) {
        $rootScope.urlbase = urlbase;
    };

    var type = "link";

    $scope.select_content = function(path, _type, options, callback) {
      /*
       * This could be implemented as a sort of mainloop that switches between
       * the modals
       * - browse
       * - props
       * - upload
       *
       * E.g. browse may return props, upload should result in browse,
       * and so on.
       */
      type = _type;
      if(path) {
          open_props(path, type, options, callback);
      }
      else {
          open_browser(path, type, options, callback);
      }
    };

    function open_browser(path, type, options, callback) {
        console.log("open_browser(" + path + ")");
        var modalInstance = $modal.open({
            templateUrl: 'BrowseModal.html',
            windowClass: "browsemodal",
            controller: "BrowseCtrl",
            resolve: {
                path: function() { return path; },
                type: function() { return type; },
                options: function() { return options; }
            }
        });
        modalInstance.result.then(function (selected) {
            options = {};
            var args = options || {};
            args.download = false;

            open_props(selected, type, options, callback);
        }, function (result) {
            // reason = upload or dismissed
            if(result.reason == "upload") {
                open_upload(result.path, type, options, callback);
            }
        });
    }

    function open_upload(path, type, options, callback) {
        var modalInstance = $modal.open({
            templateUrl: 'UploadModal.html',
            controller: "UploadCtrl",
            resolve: {
                path: function() { return path; },
                type: function() { return type; }
            }
        });
        modalInstance.result.then(function(newpath) {
            open_browser(newpath, type, options, callback);
        }, function(reason) {
            // always close/dismiss
            open_browser(path, type, options, callback);
        });
    }

    function open_props(path, type, options, callback) {
        var modalInstance = $modal.open({
            templateUrl: 'PropsModal.html',
            controller: "PropsCtrl",
            resolve: {
                path: function() { return path; },
                type: function() { return type; },
                options: function() { return options; }
            }
        });
        modalInstance.result.then(function (selected) {
            if(callback) {
                /*
                 * Append a +download on local images and on files where that's
                 * been explicitly requested
                 */
                if(selected.path.indexOf("http") !== 0) {
                    if(type == "image" || selected.download) {
                        if(!/\/$/.test(selected.path)) {
                            selected.path += '/';
                        }
                        selected.path += '+download';
                    }
                }
                console.log("callback", selected);
                callback(selected.path, selected.props);
            }
        }, function (reason) {
            // reason = change or cancel
            if(reason == "change") {
                open_browser(path, type, options);
            }
        });

    };

    //$scope.open_browser("", "link", {}, function(res) { console.log("RESULT " + res); });
});

contentbrowser.factory("PropsModal", function() {
});

contentbrowser.factory("BrowseModal", function() {
});

contentbrowser.factory("UploadModal", function() {
});


contentbrowser.controller('PropsCtrl',
           ["$scope", "$modalInstance", "$compile", "$http", "PropsModal", "path", "type", "options",
    function($scope, $modalInstance, $compile, $http, PropsModal, path, type, options) {

    $scope.propsform = options;

    function init(type, options) {
        var params = angular.copy(options);
        params.path = path;
        params.type = type;

        $http.get($scope.urlbase + "panel_selection_details",
                  {params: params}
                  ).success(
          function(data, status, headers, config) {
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
        $modalInstance.close({path:path, props:$scope.propsform});
    };

}]);
contentbrowser.controller('UploadCtrl',
               ["$scope", "$modalInstance", "$compile", "$http", "UploadModal", "path", "type",
               function($scope, $modalInstance, $compile, $http, UploadModal, path, type) {

    $scope.state = {};

    console.log("UploadCtr(" + path + ")");
    if(path === "") {
        path = "/";
    }

    var upload = null;

    function patch_form() {
        /* inject jquery.upload magic + handlers. */
        var fileinput = $("#fileupload input[type=file]");
        fileinput.replaceWith('<div id="filepreview" ></div><span class="btn btn-success fileinput-button"><i class="glyphicon glyphicon-plus icon-white"></i><span id="filelabel">Add file</span><input id="' + fileinput.attr('id') + '" type="file" name="' + fileinput.attr('name') + '"></span>');
        //var preview = $("#fileupload input[type=file]").parent(".controls")
        $('#fileupload').fileupload({
            url: path + 'fileup',
            dataType: 'json',
            autoUpload: false,
            previewMaxwidth: 100,
            previewMaxHeight: 100,
            previewCrop: true
        }).on('fileuploadadd', function(e, data) {
            upload = data;
        }).bind('fileuploadprocessalways', function(e, data) {
            var file = data.files[data.index];

            // ordinary files don't have a preview
            // XXX angularify this
            if(file.preview) {
                $("#filepreview").html(file.preview).append($('<h4/>').text(file.name));
            }
            else {
                $("#filepreview").append($('<h4/>').text(file.name));
            }
            // XXX angularify this
            $("#filelabel").text("Replace file");
        }).on('fileuploaddone', function (e, data) {
            if(data.result.status == "ok") {
              var path = data.result.path;
              $modalInstance.close(path);
            }
            else {
                // if anything went wrong, it must have been with the uploaded file
                // XXX angularify this
                $(".upload-alert").text(data.result.errors);
                $(".upload-alert").addClass("alert alert-danger");
            }
        });
    }

    function load_contentform() {
        // relative pad used here
        $http.get("fileup",
                  {params: {
                      type: $scope.state.content_type.id
                  }}
                  ).success(
          function(data, status, headers, config) {
              var uploadform = $(".uploadform");
              uploadform.html($compile(data.form)($scope));
              patch_form();
          });
    }
    function init(type) {
        load_contentform();
    }

    $scope.canSave = function() {
        return upload !== null;
    };

    $scope.type_change = function() {
        console.log($scope.state.content_type);
        load_contentform();
    };


    $scope.upload_title = function() {
        if(type == "image") {
            return "Upload an image";
        }
        return "Upload content";
    };

    if(type == "image") {
        $scope.upload_types = [{id:"wheelcms_spokes.image", title:"an Image"}];
        $scope.state.content_type = $scope.upload_types[0];
    }
    else {
        $scope.upload_types = [{id:"wheelcms_spokes.image", title:"an Image"},
                {id:"wheelcms_spokes.file", title:"a File"}];
        $scope.state.content_type = $scope.upload_types[1];
    }

    init(type);

    $scope.cancel = function() {
      $modalInstance.dismiss('cancel');
    };

    $scope.ok = function() {
        upload.submit();
    };

}]);

/*
 * selectable
 * - currently encoded in ng-click-openURL. But also returned by panels, latter suffices?
 */
contentbrowser.controller('BrowseCtrl',
               ["$scope", "$modalInstance", "$compile", "$http", "BrowseModal", "path",
                "type", "options",
               function($scope, $modalInstance, $compile, $http, BrowseModal,
                        path, type, options) {

    var startpath = ""; // the initial path
    var tab = "browse"; // browse, url, image

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
        $scope.selected.external_url = "";


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

    $scope.browse_tab = function() {
        tab = "browse";
    }
    $scope.external_url_tab = function() {
        tab = "url";
    }
    $scope.external_image_tab = function() {
        tab = "image";
    }
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
      if(tab == "browse") {
        path = $scope.path;
      } else { // (external) url or image
        path = $scope.selected.external_url;
      }
      $modalInstance.close(path);
    };

    $scope.upload = function () {
      $modalInstance.dismiss({reason:"upload", path:$scope.path});
    };

    $scope.cancel = function () {
      $modalInstance.dismiss({reason:'cancel'});
    };
}]);
