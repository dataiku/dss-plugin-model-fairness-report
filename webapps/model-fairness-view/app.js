var mainApp = angular.module("mainApp", []);
mainApp.controller('vizController', function($scope, $http, $timeout) {
       $scope.activeMetric = 'demographicParity';    
        $scope.data = {"Female": {"predicted_0_true_0": [66.406, 10.734, 5.529, 3.899, 3.232, 2.755, 2.202, 1.716, 0.801, 0.0], "predicted_0_true_1": [0.038, 0.095, 0.124, 0.133, 0.133, 0.229, 0.238, 0.257, 0.305, 0.0], "predicted_1_true_0": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.21, 0.477], "predicted_1_true_1": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.162, 0.324]}, "Male": {"predicted_0_true_0": [43.144, 8.502, 5.866, 5.626, 5.199, 4.814, 4.522, 4.428, 3.334, 0.0], "predicted_0_true_1": [0.052, 0.083, 0.104, 0.229, 0.24, 0.469, 0.5, 0.813, 1.084, 0.0], "predicted_1_true_0": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.927, 3.49], "predicted_1_true_1": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.458, 6.116]}}
        $scope.population_list = Object.keys($scope.data);
        $scope.disparity = {'Female': 0.0, 'Male': 0.41};
        $scope.disparity = {
            "demographic_parity": 0.8,
            "equalized_odds": 0.95,
            "equality_of_opportunity": 0.245,
            "predictive_rate_parity": 0.05
        }
        $scope.populations = [
            { 
                "name": "Female",
                "positive_rate": 0.5,
                "false_positive_rate": 0.6,
                "true_positive_rate": 0.7,
                "positive_predictive_value": 0.8
            },
            { 
                "name": "Make",
                "positive_rate": 0.8,
                "false_positive_rate": 0.126,
                "true_positive_rate": 0.749,
                "positive_predictive_value": 0.801
            }
        ]
        console.log('toto', $scope.populations);
    
    
        $scope.initChart = function(chosenMetric) {
        $timeout(function () {
            for (var i = 0; i < $scope.population_list.length; i++) {
                var element = $("#bar-chart-"+i);
                var population = $scope.population_list[i];
               draw(element, chosenMetric, $scope.data[population]);
            }                
        });
        }
        
       $scope.loadChart = function(idElement, chosenMetric) {
        var value = idElement.score;
        var element = $("#bar-chart-"+idElement.id);
        draw(element, chosenMetric, $scope.data);
       }
       
       $scope.updateChart = function(chosenMetric) {
           for (var i = 0; i < $scope.population_list.length; i++) {
               var element = $("#bar-chart-"+i);
                var population = $scope.population_list[i];
               draw(element, chosenMetric, $scope.data[population]);            }  
       }
});


var metricOpacityMapping = {
    'default': [1,1,1,1],
    'demographicParity': [1,1,1,1],
    'equalizedOdds': [1,1,1,1],
    'equalityOfOpportunity': [0.1, 0.1, 1, 1], 
    'predictiveRateParity': [1, 0.1, 1, 0.1]
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