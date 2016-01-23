angular.module('halo.services', [])

.factory('Dash', function($http, $q) {
   return {
     fetchSensorInfo: function(callback) {
        var defer = $q.defer();
         $http.get('https://a9a0t0l599.execute-api.us-east-1.amazonaws.com/prod/Halo').success(function(data){
             defer.resolve(data);
        });
        return defer.promise;

    },
    startListening: function(callback) {
        var defer = $q.defer();
         $http.get('https://a9a0t0l599.execute-api.us-east-1.amazonaws.com/prod/Halo?action=talk').success(function(data){
             defer.resolve(data);
        });
        return defer.promise;

     }
   }
});
