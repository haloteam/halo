angular.module('halo.controllers', [])

.controller('DashCtrl', function($scope, Dash) {
    $scope.sensors = Dash.fetchSensorInfo();

});

});
