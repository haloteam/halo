angular.module('halo.controllers', [])

.controller('DashCtrl', function($scope, Dash) {

    $scope.total = 100;
    $scope.temp = $scope.gas = $scope.rain = 0;
    $scope.progressGas = $scope.progressRain = "Safe";
    $scope.rainColor = $scope.gasColor = "#64DD17";
    setTimeout(function() {
      location.reload();
    }, 10000)
    function parseSensorData() {
        Dash.fetchSensorInfo().then(function(data){
            $scope.temp = Math.round(data.Item.currentTemp);
            $scope.gas = Math.round(data.Item.currentGas);
            $scope.rain = Math.round(data.Item.currentRain);
        }).then(function(data){
            if ($scope.temp > 90){
                $scope.tempColor = "#d50000";
            } else if ($scope.temp > 80 && $scope.temp < 90){
                $scope.tempColor = "#FFAB00";
            } else if ($scope.temp > 50 && $scope.temp < 80){
                $scope.tempColor = "#EFEFEF";
            } else if ($scope.temp > 40 && $scope.temp < 50){
                $scope.tempColor = "#FFAB00";
            } else if ($scope.temp < 40){
                $scope.tempColor = "#d50000";
            }

            if ($scope.gas > 80){
                $scope.progressGas = "Alert!";
                $scope.gasColor = "#EFEFEF";
            }
            if ($scope.rain < 150){
                $scope.progressRain = "Alert!";
                $scope.rainColor = "#d50000";
            }
        });
    }

    parseSensorData();

    /* for (var i = 0; i < 100; i++) {
        (function (i) {
            setTimeout(function () {
                parseSensorData();
            }, 3000)
        })(i)
    } */

    var elem = document.querySelector('.draggable');
    // Find your root SVG element
    var svg = document.querySelector('svg');
    console.log(svg);
    // Create an SVGPoint for future math
    var pt = svg.createSVGPoint();

    function ContentController($scope, $ionicSideMenuDelegate) {
        $scope.toggleLeft = function() {
            $ionicSideMenuDelegate.toggleLeft();
        };
    }

})

.controller('WeatherCtrl', function($scope, Question) {
  $scope.submitQuestion = function() {
    Question.askQuestion($scope.questionInput).then(function(data) {
      console.log(data)
      $scope.answer = data;
      $scope.results = answer.AllResults;
      console.log($scope.results);
    });
  }

});
