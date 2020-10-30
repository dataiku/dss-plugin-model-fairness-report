# -*- coding: utf-8 -*-
import logging
import numpy as np
from fairlearn.metrics import group_summary
from sklearn.utils import Bunch
from sklearn.metrics import confusion_matrix
from dku_model_fairness_report.constants import DkuFairnessConstants

logger = logging.getLogger(__name__)


class ModelFairnessMetric(object):

    @staticmethod
    def get_available_metric_names():
        return [ModelFairnessMetric.demographic_parity.__name__,
                ModelFairnessMetric.equality_of_opportunity.__name__,
                ModelFairnessMetric.equalized_odds.__name__,
                ModelFairnessMetric.predictive_rate_parity.__name__]

    @staticmethod
    def get_available_metric_functions():
        return [ModelFairnessMetric.demographic_parity,
                ModelFairnessMetric.equality_of_opportunity,
                ModelFairnessMetric.equalized_odds,
                ModelFairnessMetric.predictive_rate_parity
            ]

    @staticmethod
    def _compute_confusion_matrix_metrics(y_true, y_pred, label_list, sample_weight=None):
        conf_matrix = confusion_matrix(y_true, y_pred, labels=label_list, sample_weight=sample_weight)

        true_negative = conf_matrix[0][0]
        false_negative = conf_matrix[1][0]
        true_positive = conf_matrix[1][1]
        false_positive = conf_matrix[0][1]

        return true_negative, false_negative, true_positive, false_positive

    @staticmethod
    def demographic_parity(y_true, y_pred, label_list, sample_weight=None):
        """
        demographic_parity just care about y_pred, but we keep y_true to have a homogene api
        """

        # last label is the advantageous one
        return np.round(np.sum(y_pred == label_list[-1], dtype=float) / len(y_pred), DkuFairnessConstants.NUMBER_OF_DECIMALS)

    @staticmethod
    def equality_of_opportunity(y_true, y_pred, label_list, sample_weight=None):
        true_negative, false_negative, true_positive, false_positive = ModelFairnessMetric._compute_confusion_matrix_metrics(y_true, y_pred, label_list, sample_weight)
        # Sensitivity, hit rate, recall, or true positive rate
        true_positive_rate = np.round(true_positive / (true_positive + false_negative), DkuFairnessConstants.NUMBER_OF_DECIMALS)
        return true_positive_rate

    @staticmethod
    def equalized_odds(y_true, y_pred, label_list, sample_weight=None):
        true_negative, false_negative, true_positive, false_positive = ModelFairnessMetric._compute_confusion_matrix_metrics(y_true, y_pred, label_list, sample_weight)
        true_positive_rate = np.round(true_positive / (true_positive + false_negative), DkuFairnessConstants.NUMBER_OF_DECIMALS)
        false_positive_rate = np.round(false_positive / (true_negative + false_positive), DkuFairnessConstants.NUMBER_OF_DECIMALS)
        return true_positive_rate, false_positive_rate

    @staticmethod
    def predictive_rate_parity(y_true, y_pred, label_list, sample_weight=None):
        true_negative, false_negative, true_positive, false_positive = ModelFairnessMetric._compute_confusion_matrix_metrics(y_true, y_pred, label_list, sample_weight)
        # Precision or positive predictive value
        positive_predictive_value = np.round(true_positive / (true_positive + false_positive), DkuFairnessConstants.NUMBER_OF_DECIMALS)
        return positive_predictive_value


class ModelFairnessMetricReport(object):
    def __init__(self, y_true, y_pred, sensitive_feature_values, advantageous_outcome=None, sample_weight=None):
        self.y_true = y_true  # 1D array
        self.y_pred = y_pred  # 1D array
        self.sensitive_feature_values = sensitive_feature_values  # 1D array
        self.advantageous_outcome = advantageous_outcome  # string
        self.sample_weight = sample_weight  # 1D array
        self._check()

        self.label_list = self.get_label_list()

    def _check(self):
        possible_outcomes = set(self.y_true.unique()).union(set(self.y_pred.unique()))
        if self.advantageous_outcome is not None and self.advantageous_outcome not in possible_outcomes:
            raise ValueError('The chosen positive outcome, "{}", does not exist in either y_true or y_pred.'.format(self.advantageous_outcome))

        if len(possible_outcomes) != 2:
            raise ValueError('Only support binary classification, found {} possible values.'.format(len(possible_outcomes)))

    def _check_reference_group(self, reference_group, summary):
        if reference_group not in summary.get(DkuFairnessConstants.BY_GROUP).keys():
            raise ValueError('The chosen reference group "{0}" does not exist in the input metric summary.'.format(reference_group))

    def get_label_list(self):
        label_list = [x for x in np.unique(self.y_true) if x != self.advantageous_outcome]
        label_list.append(self.advantageous_outcome)

        return label_list

    def compute_metric_per_group(self, metric_function):
        """
        metric_function is a function with signature metric_function(y_true, y_pred, *metric_params)
        """
        return group_summary(metric_function,
                             self.y_true,
                             self.y_pred,
                             sensitive_features=self.sensitive_feature_values,
                             label_list=self.label_list)

    def _get_reference_group(self, reference_group, summary):
        # if there is no reference group, take the overall metric
        if reference_group == DkuFairnessConstants.OVERALL:
            reference_metrics = summary.get(DkuFairnessConstants.OVERALL)
        else:
            self._check_reference_group(reference_group, summary)
            reference_metrics = summary[DkuFairnessConstants.BY_GROUP][reference_group]
        return np.array(reference_metrics)

    def _compute_group_func_from_summary(self, summary, reference_group, func):
        func_by_group = {}
        reference_metrics = self._get_reference_group(reference_group, summary)
        for group, group_metrics in summary.get(DkuFairnessConstants.BY_GROUP).items():
            func_by_group[group] = np.round(func(group_metrics, reference_metrics), DkuFairnessConstants.NUMBER_OF_DECIMALS)

        # TODO decide if it is a good idea to put overall metric here
        func_by_group[DkuFairnessConstants.OVERALL] = np.round(func(summary.get(DkuFairnessConstants.OVERALL), reference_metrics), DkuFairnessConstants.NUMBER_OF_DECIMALS)
        return Bunch(reference_group=reference_group, by_group=func_by_group)

    def compute_group_difference_from_summary(self, summary, reference_group=DkuFairnessConstants.OVERALL):
        def diff_func(group_metric, reference_metric):
            return group_metric - reference_metric
        return self._compute_group_func_from_summary(summary, reference_group, diff_func)

    def compute_group_ratio_from_summary(self, summary, reference_group=DkuFairnessConstants.OVERALL):
        def ratio_func(group_metric, reference_metric):
            if any(np.array(reference_metric)) == 0:
                logger.warning('Reference metric value = 0. Ratio function will return nan or inf.')
            return group_metric/reference_metric
        return self._compute_group_func_from_summary(summary, reference_group, ratio_func)