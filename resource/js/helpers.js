'use strict';

(function() {
    app.service("ModalService", function($compile, $http) {
        const DEFAULT_MODAL_TEMPLATE = "/plugins/model-fairness-report/resource/templates/modal.html";

        function create(scope, config, templateUrl=DEFAULT_MODAL_TEMPLATE) {
            $http.get(templateUrl).then(function(response) {
                const template = response.data;
                const newScope = scope.$new();
                const element = $compile(template)(newScope);

                angular.extend(newScope, config);

                newScope.close = function(event) {
                    if (event && !event.target.className.includes("modal-background")) return;
                    element.remove();
                    newScope.$emit("closeModal");
                };

                if (newScope.promptConfig && newScope.promptConfig.conditions) {
                    const inputField = element.find("input");
                    for (const attr in newScope.promptConfig.conditions) {
                        inputField.attr(attr, newScope.promptConfig.conditions[attr]);
                    }
                    $compile(inputField)(newScope);
                }

                angular.element("body").append(element);
                element.focus();
            });
        };
        return {
            createBackendErrorModal: function(scope, errorMsg) {
                create(scope, {
                    title: 'Backend error',
                    msgConfig: { error: true, msg: errorMsg }
                }, DEFAULT_MODAL_TEMPLATE);
            },
            create
        };
    });

    const metricOpacityMapping = {
        'default': [1,1,1,1],
        'demographicParity': [1,1,1,1],
        'equalizedOdds': [1,1,1,1],
        'equalityOfOpportunity': [1, 0.1, 1, 0.1],
        'predictiveRateParity':  [0.1, 0.1, 1, 1]
    };

    app.service("ChartService", function() {
        // Return with commas in between
        function numberWithCommas(x) {
            return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }

        return {
            draw: function (element, chosenMetric, data, labelList) {
                const concatted_array = data['predicted_0_true_1'].concat(data['predicted_0_true_0'], data['predicted_1_true_1'], data['predicted_1_true_0']);
                const max_y = Math.ceil( Math.max.apply(null, concatted_array) / 10) * 10;
                const label_x = ["0",  "", "", "", "", "", "", "", "", "1"];

                const [ opacity1, opacity2, opacity3, opacity4 ] = metricOpacityMapping[chosenMetric];

                const [ class0, class1 ] = labelList;

                return new Chart(element, {
                    type: 'bar',
                    data: {
                        labels: label_x,
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
                                    return data.datasets[tooltipItem.datasetIndex].label + ": " + numberWithCommas(tooltipItem.yLabel)+'%';
                                }
                            },
                            displayColors: true
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
                                    labelString: '% Population',
                                    fontFamily: "'Source Sans Pro', sans-serif",
                                    fontSize: 12
                                }
                            }],
                        },
                        legend: {
                            display: true,
                            position: "bottom",
                            labels: {
                                usePointStyle: true,
                                fontSize: 11,
                                fontColor: "#222222",
                                fontFamily: "'Source Sans Pro', sans-serif"
                            },
                        }
                    }
                });
            }
        };
    });
})();

app.directive("customDropdown", function() {
    return {
        scope: {
            form: '=?',
            itemImage: '=?',
            label: '@',
            itemName: '@',
            item: '=',
            items: '=',
            possibleValues: '=',
            notAvailableValues: '=',
            onChange: '=',
            display: '=?'
        },
        restrict: 'A',
        templateUrl:'/plugins/model-fairness-report/resource/templates/custom-dropdown.html',
        link: function(scope, elem, attrs) {
            const VALIDITY = "dropdown-not-empty" + (attrs.id ? ("__" + attrs.id) : "");
            function setValidity() {
                if (!scope.form) return;
                scope.form.$setValidity(VALIDITY, scope.item !== undefined || !!(scope.items || {}).size);
            }
            setValidity();

            scope.display = scope.display || (item => item === "__dku_missing_value__" ? "" : item);

            scope.canBeSelected = function(item) {
                if (!scope.notAvailableValues) return true;
                return item === scope.item || !(item in scope.notAvailableValues);
            };

            const isMulti = !!attrs.items;
            scope.isSelected = function(value) {
                if (isMulti) {
                    return scope.items.has(value);
                }
                return scope.item === value;
            };

            scope.updateSelection = function(value, event) {
                if (isMulti) {
                    if (scope.isSelected(value)) {
                        scope.items.delete(value);
                    } else {
                        scope.items.add(value);
                    }
                    event.stopPropagation();
                } else {
                    if (scope.item === value) return;
                    if (scope.onChange) {
                        scope.onChange(value, scope.item, elem);
                    }
                    scope.item = value;
                }
                setValidity();
            };

            scope.getPlaceholder = function() {
                if (isMulti) {
                    if (!(scope.items || {}).size) return "Select " + scope.itemName + "s";
                    return scope.items.size + " " + scope.itemName + (scope.items.size > 1 ? "s" : "");
                }
                if (scope.item == null) return "Select a " + scope.itemName;
                return scope.display(scope.item);
            };

            scope.toggleDropdown = function() {
                scope.isOpen = !scope.isOpen;
            };

            const dropdownElem = elem.find(".custom-dropdown");
            const labelElem = elem.find(".label-text");
            scope.$on("closeDropdowns", function(e, target) {
                if ((target) && ( angular.element(target).closest(dropdownElem)[0]
                    || angular.element(target).closest(labelElem)[0] )) { return; }
                scope.isOpen = false;
            });

            scope.$on("$destroy", function() {
                scope.form && scope.form.$setValidity(VALIDITY, true);
            });
        }
    }
});
