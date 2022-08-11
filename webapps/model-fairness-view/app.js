let webAppConfig = dataiku.getWebAppConfig();
let modelId = webAppConfig['modelId'];
let versionId = webAppConfig['versionId'];
(function() {
    'use strict';
    app.controller('VizController', function($scope, $http, $timeout, ModalService, ChartService) {
        $scope.$on("closeModal", function() {
            angular.element(".report-box").focus();
        });

        const chartList = [];
        $scope.activeMetric = 'demographicParity';
        $scope.hasResults = false;

        $http.get(getWebAppBackendUrl("get-feature-list/"+modelId+"/"+versionId))
            .then(function(response){
                $scope.columnList = response.data;
            }, function(e) {
                ModalService.createBackendErrorModal($scope, e.data);
            });

        $http.get(getWebAppBackendUrl("get-outcome-list/"+modelId+"/"+versionId))
            .then(function(response){
                $scope.outcomeList = response.data;
                $scope.advantageousOutcome = $scope.outcomeList[0];
            }, function(e) {
                ModalService.createBackendErrorModal($scope, e.data);
            });

        $http.get(getWebAppBackendUrl("check-model-type/"+modelId+"/"+versionId))
            .then(function(response){
                console.log('All good')
            }, function(e) {
                ModalService.createBackendErrorModal($scope, e.data);
            });

        $scope.updateValueList = function(){
            $http.get(getWebAppBackendUrl("get-value-list/"+modelId+"/"+versionId+"/"+$scope.sensitiveColumn))
                .then(function(response){
                    $scope.valueList = response.data
            }, function(e) {
                ModalService.createBackendErrorModal($scope, e.data);
            });
        };

        $scope.generateChart = function(chosenMetric) {
            $timeout(function () {
                $scope.populations.forEach(function(population, idx) {
                    const element = $("#bar-chart-" + idx);
                    const barChart = ChartService.draw(
                        element, chosenMetric, histograms[population.name], $scope.labelList
                    );
                    chartList.push(barChart);
                });
            });
        };

        let histograms;
        $scope.runAnalysis = function () {
            // remove old charts
            chartList.forEach(function(chart) {
                chart.destroy();
            });

            $scope.loadingAnalysisData = true;
            $http.get(getWebAppBackendUrl("get-data/"+modelId+"/"+versionId+"/"+$scope.advantageousOutcome+"/"+$scope.sensitiveColumn+"/"+$scope.referenceGroup))
                .then(function({data}) {
                    $scope.hasResults = true;

                    $scope.populations = data.populations;
                    $scope.disparity = data.disparity;
                    $scope.labelList = data.labels;
                    histograms = data.histograms;
                    $scope.generateChart('default');

                    $scope.loadingAnalysisData = false;
            }, function(e) {
                $scope.loadingAnalysisData = false;
                ModalService.createBackendErrorModal($scope, e.data);
            });
        }
    });
})();
