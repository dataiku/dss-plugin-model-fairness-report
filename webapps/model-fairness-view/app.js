let webAppConfig = dataiku.getWebAppConfig();
let modelId = webAppConfig['modelId'];
let versionId = webAppConfig['versionId'];
var chart_list = [];

(function() {
    'use strict';

app.controller('vizController', function($scope, $http, $timeout, ModalService) {

        $scope.activeMetric = 'demographicParity';
        $http.get(getWebAppBackendUrl("get-feature-list/"+modelId+"/"+versionId))
            .then(function(response){
                $scope.columnList = response.data;
                $scope.sensitiveColumn = response.data[0];
                $scope.updateValueList();
            }, function(e) {
                $scope.createModal.error(e.data);
            });


        $http.get(getWebAppBackendUrl("get-outcome-list/"+modelId+"/"+versionId))
            .then(function(response){
                $scope.outcomeList = response.data;
                $scope.advantageousOutcome = $scope.outcomeList[0];
            }, function(e) {
                $scope.createModal.error(e.data);
            });

        $scope.modal = {};
        $scope.removeModal = function(event) {
            if (ModalService.remove($scope.modal)(event)) {
                angular.element(".template").focus();
            }
        };
        $scope.createModal = ModalService.create($scope.modal);

        $scope.updateValueList = function(){
            $http.get(getWebAppBackendUrl("get-value-list/"+modelId+"/"+versionId+"/"+$scope.sensitiveColumn))
                .then(function(response){
                  $scope.valueList = response.data
            }, function(e) {
                $scope.createModal.error(e.data);
            });
        }

        $scope.generateChart = function(chosenMetric) {
            $timeout(function () {
                for (var i = 0; i < $scope.population_list.length; i++) {
                    var element = $("#bar-chart-"+i);
                    var population = $scope.population_list[i];
                   draw(element, chosenMetric, $scope.histograms[population], $scope.label_list);
                }
            });
        }

        $scope.runAnalysis = function () {
             markRunning(true);
             $scope.activeMetric = 'demographicParity';
             $('#error_message').html('');
             // remove old charts
            for (var j = 0; j < chart_list.length; j++) {
                    chart_list[j].destroy();
            };
            $http.get(getWebAppBackendUrl("get-data/"+modelId+"/"+versionId+"/"+$scope.advantageousOutcome+"/"+$scope.sensitiveColumn+"/"+$scope.referenceGroup))
                .then(function(response){
                    $scope.populations = response.data.populations;
                    $scope.histograms = response.data.histograms;
                    $scope.disparity = response.data.disparity;
                    $scope.label_list = response.data.labels
                    $scope.population_list = Object.keys($scope.histograms);
                    $scope.generateChart('default');
                    $('.result-state').show();
                    markRunning(false);
            }, function(e) {
                markRunning(false);
                $scope.createModal.error(e.data);
            });
        }
});
})();

var metricOpacityMapping = {
    'default': [1,1,1,1],
    'demographicParity': [1,1,1,1],
    'equalizedOdds': [1,1,1,1],
    'equalityOfOpportunity': [1, 0.1, 1, 0.1],
    'predictiveRateParity':  [0.1, 0.1, 1, 1]
}


function markRunning(running) {
    if (running) {
        $('.running-state').show();
        $('.landing-page').hide()
        $('.notrunning-state').hide();
        $('.result-state').hide();
    } else {
        $('.running-state').hide();
        $('.notrunning-state').show();
    }
}

function draw(element, chosenMetric, data, label_list){
    // Return with commas in between
      var numberWithCommas = function(x) {
        return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      };
    var concatted_array = data['predicted_0_true_1'].concat(data['predicted_0_true_0'], data['predicted_1_true_1'], data['predicted_1_true_0'])
    var max_y = Math.ceil( Math.max.apply(null, concatted_array) / 10) * 10;
    var dates = ["0",  "", "", "", "", "", "", "", "", "1"];

    var [opacity1, opacity2, opacity3, opacity4] = metricOpacityMapping[chosenMetric]

    var class0 = label_list[0];
    var class1 =label_list[1];

    var bar_chart = new Chart(element, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
            {
                label: 'predicted = '+ class0 + ', true = '+ class1,
                data: data['predicted_0_true_1'],
                backgroundColor: "rgb(95, 137, 181,"+ opacity1 + ")",
                hoverBackgroundColor: "rgb(95, 137, 181, 0.15)",
                hoverBorderWidth: 0,
                pointStyle:"circle",
                borderWidth: 0
            },
            {
                label: 'predicted = '+class0+', true = '+class0,
                data: data['predicted_0_true_0'],
                backgroundColor: "rgb(121, 158, 195,"+ opacity2 +")",
                hoverBackgroundColor: "rgb(121, 158, 195, 0.14)",
                hoverBorderWidth: 0,
                pointStyle:"circle",
                borderWidth: 0
            },
            {
                label: 'predicted = '+class1+', true = '+class1,
                data: data['predicted_1_true_1'],
                backgroundColor: "rgb(239, 148, 93," + opacity3 + ")",
                hoverBackgroundColor: "rgb(239, 148, 93)",
                hoverBorderWidth: 0,
                pointStyle:"circle",
                borderWidth: 0
            },
              {
                label: 'predicted = '+class1+', true = '+class0,
                data: data['predicted_1_true_0'],
                backgroundColor: "rgb(247, 194, 154, " + opacity4 + ")",
                hoverBackgroundColor: "rgb(247, 194, 154)",
                hoverBorderWidth: 0,
                pointStyle:"circle",
                borderWidth: 0
            }
            ]
        },
         options: {
                animation: {
                duration: 10,
            },
              tooltips: {
                        mode: 'label',
              callbacks: {
              label: function(tooltipItem, data) { 
                return data.datasets[tooltipItem.datasetIndex].label + ": " + numberWithCommas(tooltipItem.yLabel);
              }
              }
             },
            scales: {
              xAxes: [{ 
                stacked: true, 
                gridLines: { display: false },
                  scaleLabel: {
                    display: true,
                    labelString: 'Prediction probability',
                    fontFamily: "'Source Sans Pro', sans-serif",
                    fontSize: 12
                  }
                }],
              yAxes: [{ 
                stacked: true, 
                ticks: {
                        callback: function(value) { return numberWithCommas(value); },
                        beginAtZero: true, 
                        min: 0,
                        max: max_y
                        },
              gridLines: { display: false },
               scaleLabel: {
                    display: true,
                    labelString: 'Population ratio',
                    fontFamily: "'Source Sans Pro', sans-serif",
                    fontSize: 12
                  }
                }],
            }, // scales
            legend: {
                display: true, 
                position: "bottom",
                labels:{
                    usePointStyle: true, 
                    fontSize: 11,
                    fontColor: "#222222",
                    fontFamily: "'Source Sans Pro', sans-serif"
                },

            }
        } // options
       }
    );
    chart_list.push(bar_chart);
}
