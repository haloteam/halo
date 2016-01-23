angular.module('halo.services', [])

.factory('Dash', function($http) {
   return {
     fetchSensorInfo: function(callback) {
       $http.get('https://a9a0t0l599.execute-api.us-east-1.amazonaws.com/prod/Halo').success(callback);
     }
   }
});
