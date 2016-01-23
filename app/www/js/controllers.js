angular.module('halo.controllers', [])

.controller('DashCtrl', function($scope) {

  $scope.sensors = Dash.fetchSensorInfo();
  
  var hms = '00:04:33';   // your input string
  var a = hms.split(':'); // split it at the colons

  // minutes are worth 60 seconds. Hours are worth 60 minutes.
  $scope.total = (+a[0]) * 60 * 60 + (+a[1]) * 60 + (+a[2]);
    $scope.progress=5;
    $scope.add=function(){
      $scope.progress+=50;
    }


  var elem = document.querySelector('.draggable');
        // Find your root SVG element
  var svg = document.querySelector('svg');
  console.log(svg);
  // Create an SVGPoint for future math
  var pt = svg.createSVGPoint();

  // Get point in global SVG space
  function cursorPoint(evt){
    pt.x = evt.clientX; pt.y = evt.clientY;
    return pt.matrixTransform(svg.getScreenCTM().inverse());
  }
  function angle(ex, ey) {
    var dy = ey - 100;
    var dx = ex - 100;
    var theta = Math.atan2(dy, dx); // range (-PI, PI]
    theta *= 180 / Math.PI; // rads to degs, range (-180, 180]
    //if (theta < 0) theta = 360 + theta; // range [0, 360)
    return theta;
  }
  svg.addEventListener('mousedown',function(evt){
    var loc = cursorPoint(evt);
    // Use loc.x and loc.y here
    // console.log(Math.sqrt((100-loc.x)*(100-loc.x) + (100-loc.y)*(100-loc.y)));
    // console.log(Math.sqrt((100-loc.x)*(100-loc.x) + (100-loc.y)*(100-loc.y)) > 93 && Math.sqrt((100-loc.x)*(100-loc.x) + (100-loc.y)*(100-loc.y)) < 100)
    // console.log(Math.atan2( (loc.y), (loc.x)) * (180 / Math.PI));
    console.log("X: "+loc.x+" Y: "+loc.y);
    console.log(angle(loc.x,loc.y));
    console.log(2*Math.PI*96)*(angle(loc.x,loc.y)/360);
  },false);
})


});
