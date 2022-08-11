let webAppConfig = dataiku.getWebAppConfig();
let modelId = webAppConfig['modelId'];
let versionId = webAppConfig['versionId'];
(function() {
    'use strict';
    app.controller('VizController', function($scope, $http, $timeout, ModalService, ChartService) {
            var chart_list = [];
            $scope.activeMetric = 'demographicParity';
            $scope.hasResults = false;

            $http.get(getWebAppBackendUrl("get-feature-list/"+modelId+"/"+versionId))
                .then(function(response){
                    $scope.columnList = response.data;
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

            $http.get(getWebAppBackendUrl("check-model-type/"+modelId+"/"+versionId))
                .then(function(response){
                    console.log('All good')
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
            };

            $scope.generateChart = function(chosenMetric) {
                $timeout(function () {
                    for (var i = 0; i < $scope.populations.length; i++) {
                        var population = $scope.populations[i]['name'];
                        var element = $("#bar-chart-"+i);
                        var bar_chart = ChartService.draw(element, chosenMetric, $scope.histograms[population], $scope.label_list);
                        chart_list.push(bar_chart);
                    }
                });
            };

            $scope.runAnalysis = function () {
                // remove old charts
                chart_list.forEach(function(chart) {
                    chart.destroy();
                });

                $scope.loadingAnalysisData = true;
                $http.get(getWebAppBackendUrl("get-data/"+modelId+"/"+versionId+"/"+$scope.advantageousOutcome+"/"+$scope.sensitiveColumn+"/"+$scope.referenceGroup))
                    .then(function(response) {
                        $scope.hasResults = true;

                        $scope.populations = response.data.populations;
                        $scope.histograms = response.data.histograms;
                        $scope.disparity = response.data.disparity;
                        $scope.label_list = response.data.labels;
                        $scope.population_list = Object.keys($scope.histograms);
                        $scope.generateChart('default');

                        $scope.loadingAnalysisData = false;
                }, function(e) {
                    $scope.loadingAnalysisData = false;
                    $scope.createModal.error(e.data);
                });
            }
    });
})();
