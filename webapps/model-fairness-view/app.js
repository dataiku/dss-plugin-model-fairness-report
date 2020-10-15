var mainApp = angular.module("mainApp", []);
mainApp.controller('vizController', function($scope, $http, $timeout) {

        $http.get(getWebAppBackendUrl("get-column-list"))
            .then(function(response){
                $scope.columnList = response.data;
                $scope.sensitiveColumn = response.data[0];
                $scope.updateValueList();
            }, function(e) {
                dataiku.webappMessages.displayFatalError(e);
            });


        $http.get(getWebAppBackendUrl("get-outcome-list"))
            .then(function(response){
                $scope.outcomeList = response.data;
                $scope.advantageousOutcome = $scope.outcomeList[0];
            }, function(e) {
                dataiku.webappMessages.displayFatalError(e);
            });

        $scope.updateValueList = function(){
            $http.get(getWebAppBackendUrl("get-value-list/"+$scope.sensitiveColumn))
                .then(function(response){
                  $scope.valueList = response.data
                  $scope.referenceGroup = $scope.valueList[0];
            }, function(e) {
                dataiku.webappMessages.displayFatalError(e);
            });
        }

        $scope.activeMetric = 'demographicParity';
        $scope.initChart = function(chosenMetric) {
        $timeout(function () {
            for (var i = 0; i < $scope.population_list.length; i++) {
                var element = $("#bar-chart-"+i);
                var population = $scope.population_list[i];
               draw(element, chosenMetric, $scope.histograms[population]);
            }
        });
        }

       $scope.updateChart = function(chosenMetric) {
           for (var i = 0; i < $scope.population_list.length; i++) {
               var element = $("#bar-chart-"+i);
                var population = $scope.population_list[i];
               draw(element, chosenMetric, $scope.histograms[population]);
           }
       }

        $scope.runAnalysis = function () {
            markRunning(true);
            $http.get(getWebAppBackendUrl("get-data"))
                .then(function(response){
                    $scope.populations = response.data.populations;
                    $scope.histograms = response.data.histograms;
                    $scope.disparity = response.data.disparity;
                    $scope.population_list = Object.keys($scope.histograms);
                    $scope.initChart('default');
                    $('.result-state').show();
                    markRunning(false);
            }, function(e) {
                dataiku.webappMessages.displayFatalError(e);
            });
        }
});


var metricOpacityMapping = {
    'default': [1,1,1,1],
    'demographicParity': [1,1,1,1],
    'equalizedOdds': [1,1,1,1],
    'equalityOfOpportunity': [0.1, 0.1, 1, 1],
    'predictiveRateParity': [1, 0.1, 1, 0.1]
}


function markRunning(running) {
    if (running) {
        $('.running-state').show();
        $('.notrunning-state').hide();
        $('.result-state').hide();
    } else {
        $('.running-state').hide();
        $('.notrunning-state').show();
    }
}

function draw(element, chosenMetric, data){
    // Return with commas in between
      var numberWithCommas = function(x) {
        return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      };
    //var dates = ["0", "", "", "", "", "", "", "", "", "","", "", "", "", "", "", "", "", "", "1"];
    var concatted_array = data['predicted_0_true_1'].concat(data['predicted_0_true_0'], data['predicted_1_true_1'], data['predicted_1_true_0'])
    var max_y = Math.ceil( Math.max.apply(null, concatted_array) / 10) * 10;
    var dates = ["0",  "", "", "", "", "", "", "", "", "1"];

    var [opacity1, opacity2, opacity3, opacity4] = metricOpacityMapping[chosenMetric]
    //var bar_ctx = document.getElementById(canvas_id);

    var bar_chart = new Chart(element, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
            {
                label: 'predicted = 0, true = 1',
                data: data['predicted_0_true_1'],
                backgroundColor: "rgb(95, 137, 181,"+ opacity1 + ")", //"#5F89B5",
                hoverBackgroundColor: "rgb(95, 137, 181, 0.15)",
                hoverBorderWidth: 0,
                pointStyle:"circle",
                borderWidth: 0
            },
            {
                label: 'predicted = 0, true = 0',
                data: data['predicted_0_true_0'],
                backgroundColor: "rgb(121, 158, 195,"+ opacity2 +")",//"#799EC3",
                hoverBackgroundColor: "rgb(121, 158, 195, 0.14)",
                hoverBorderWidth: 0,
                pointStyle:"circle",
                borderWidth: 0
            },
            {
                label: 'predicted = 1, true = 1',
                data: data['predicted_1_true_1'],
                backgroundColor: "rgb(239, 148, 93," + opacity3 + ")",
                hoverBackgroundColor: "rgb(239, 148, 93)",
                hoverBorderWidth: 0,
                pointStyle:"circle",
                borderWidth: 0
            },
              {
                label: 'predicted = 1, true = 0',
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
                    labelString: 'Probability'
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
                    labelString: 'Population ratio'
                  }

                }],
            }, // scales
            legend: {
                display: true, 
                position: "bottom",
                labels:{
                    usePointStyle: true, 
                    fontSize: 11,
                    fontColor: "#666666",
                    fontFamily: "Source Sans Pro"                    
                },

            }
        } // options
       }
    );
}