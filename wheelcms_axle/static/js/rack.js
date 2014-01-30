app.controller('RackEditCtrl', function($http, $scope) {
    var selection_start = -1;
    var selection_end = -1;
    var selection_side = "both";

    $scope.rack = "";

    $scope.RackSelected = function() {
    };

    $scope.getRackTemplate = function() {
        if($scope.rack) {
            return $scope.urlbase + "+rackconfig?id=" + $scope.rack;
        }
    };

    $scope.Save = function() {
        console.log("Save ", selection_start, selection_end, selection_side);
        $http.post($scope.urlbase + "+rack/",
              {start:selection_start,
               end:selection_end,
               side:selection_side,
               rack_id:$scope.rack
               }, function() {

        });
    };

    $scope.RackSelection = function(s, e, side) {
        selection_start = s>e?e:s;
        selection_end = s>e?s:e;
        selection_side = side;
    };
});

app.controller('RackCtrl', function($scope, $element) {
    //$($element).selectable({filter:"li.available"});
    
    var rowstart = -1;
    var rowend = -1;
    var posstart = "";
    var both = false; // front + end
    var moved = false;

    var selecting = false;

    function noselection() {
        return (rowstart == -1 && rowend == -1 && posstart === "");
    }

    $scope.StartSelection = function(row, pos) {
        moved = noselection();
        rowstart = rowend = parseInt(row, 10);
        posstart = pos;
        both = false;
        selecting = true;
    };
    $scope.EndSelection = function(row, pos) {
        selecting = false;

        if(!moved) {
            rowstart = -1;
            rowend = -1;
            posstart = "";
            both = false;
            $scope.RackSelection(-1, -1, "both");
            return;
        }
        var side = both?"both":posstart;
        // can't $apply since we're already applied -> $rootScope:inprog
        // How about emit?
        $scope.RackSelection(rowstart, rowend, side);
    };


    $scope.MouseOver = function(row, pos) {
        if(selecting) {
            both = pos != posstart;
            rowend = parseInt(row, 10);

            if(pos != posstart || row != rowend) {
                moved = true;
            }
        }
    };
    $scope.isSelected = function(row, pos) {
        row = parseInt(row, 10);
        /* Should stop if we bump into inuse row */
        if(both || (pos == posstart)) {
            if(row >= rowstart && row <= rowend) {
                return true;
            }
            if(row <= rowstart && row >= rowend) {
                return true;
            }
        }
    };
});

/*
 * Some issues with this directive:
 *
 * - It still requires ng-class to set the ui-selected class
 * - It allows selection *over* positions that are in use
 * - You cannot deselect a selection. Once something has been selected,
 *   something will remain selected
 */

app.directive("rackSelect", function() {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            /*
             * It would be nice to move the ng-class behaviour
             * to this directive as well
             */
            element.bind("mouseover", function() {
                scope.$apply(function(scope) {
                   scope.MouseOver(attrs.row, attrs.pos);
                });
            });
            element.bind("mousedown", function() {
                scope.$apply(function(scope) {
                   scope.StartSelection(attrs.row, attrs.pos);
                });
            });
            element.bind("mouseup", function() {
                scope.$apply(function(scope) {
                   scope.EndSelection(attrs.row, attrs.pos);
                });
            });
        }
    };
});


