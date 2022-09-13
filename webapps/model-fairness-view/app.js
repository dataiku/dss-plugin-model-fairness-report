(function() {
    'use strict';
    app.controller('VizController', function($scope, $http, $timeout, ModalService, ChartService) {
        $scope.$on("closeModal", function() {
            angular.element(".report-box").focus();
        });

        const chartList = [];
        $scope.activeMetric = 'demographicParity';
        $scope.hasResults = false;

        $http.get(getWebAppBackendUrl("set-model"))
            .then(function() {
                $http.get(getWebAppBackendUrl("get-feature-and-outcome-lists"))
                    .then(function({ data }) {
                        $scope.columnList = data.featureList;
                        $scope.outcomeList = data.outcomeList;
                        $scope.advantageousOutcome = $scope.outcomeList[0];
                    }, function(e) {
                        ModalService.createBackendErrorModal($scope, e.data);
                    });
            }, function(e) {
                ModalService.createBackendErrorModal($scope, e.data);
            });

        $scope.updateValueList = function(sensitiveColumn) {
            delete $scope.referenceGroup;
            delete $scope.valueList;
            $http.get(getWebAppBackendUrl("get-value-list/" + sensitiveColumn))
                .then(function({data}){
                    $scope.valueList = data
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
            $http.get(getWebAppBackendUrl(`get-fairness-data/${$scope.advantageousOutcome}/${$scope.sensitiveColumn}/${$scope.referenceGroup}`))
                .then(function({data}) {
                    $scope.hasResults = true;

                    $scope.populations = data.populations;
                    $scope.disparity = data.disparity;
                    $scope.labelList = data.labels;
                    $scope.currentReferenceGroup = data.referenceGroup;
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
