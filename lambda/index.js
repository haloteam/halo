console.log('Loading function');

var AWS = require('aws-sdk');
var doc = require('dynamodb-doc');
var dynamo = new doc.DynamoDB();
var docClient = new AWS.DynamoDB.DocumentClient()
/**
 * Provide an event that contains the following keys:
 *
 *   - operation: one of the operations in the switch statement below
 *   - tableName: required for operations that interact with DynamoDB
 *   - payload: a parameter to pass to the operation being performed
 */

exports.handler = function(event, context) {
    console.log('Received event:', JSON.stringify(event, null, 2));
    //context.succeed("success : " + JSON.stringify(event));
    var tableName = "halo_devices";
    if(event.action === "save") {
        var deviceId = event.deviceId;
        for(var i = 0; i < event.updates.length; i++) {
            var type = event.updates[i].type;
            if(type === "temperature") {
                var updateExpression = "set currentTemp = :attrValue";
                var tempValue = event.updates[i].value;
            }
            else if(type === "gas") {
                var updateExpression = "set currentGas = :attrValue";
                var gasValue = event.updates[i].value;
            }
            else if(type === "rain") {
                var updateExpression = "set currentRain = :attrValue";
                var rainValue = event.updates[i].value;
            }
        }
        console.log(tempValue, gasValue, rainValue, 'values');
        docClient.update({
            "TableName" : tableName,
            "Key" : {
                "DeviceId":String(deviceId)
            },
            "UpdateExpression" : "set currentTemp = :tempValue, currentGas = :gasValue, currentRain = :rainValue",

            "ExpressionAttributeValues" : {
                ":tempValue" : tempValue,
                ":gasValue" : gasValue,
                ":rainValue" : rainValue
            }

        }, function(error, data) {
          context.done(error, data);
        });

    }
    else {
        var params = {
          TableName : tableName,
          Key: {
            DeviceId: "1"
          }
        };
        docClient.get(params, function(error, data) {
          context.done(error, data);
        });


    }
    // var tableName = "halo_devices";
    // var deviceId = event.deviceId;
    // var data_type = event.data_type;
    // var data_value = event.data_value;
    // var data_timestamp = event.data_timestamp;

    // if(data_type === "temperature") {
    //     var updateExpression = "set temperature = list_append(temperature, :attrValue); set current = " + data_value;
    // }

    // docClient.update({
    // "TableName" : tableName,
    // "Key" : {
    //     "DeviceId": deviceId
    // },
    // "UpdateExpression" : updateExpression,

    // "ExpressionAttributeValues" : {
    //     ":attrValue" : [{
    //           "value" : data_value,
    //           "timestamp": data_timestamp
    //       }]
    // }
    // }, function(err, data) {
    // console.log(err, data);
    // context.done(err, data);
    // });

};
