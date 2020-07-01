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
    def get_available_metrics():
        return [ModelFairnessMetric.demographic_parity.__name__,
                ModelFairnessMetric.equality_of_opportunity.__name__,
                ModelFairnessMetric.equalized_odds.__name__,
                ModelFairnessMetric.predictive_rate_parity.__name__]

    @staticmethod
    def _compute_confusion_matrix_metrics(y_true, y_pred, advantage_outcome, sample_weight=None):
        label_list = [x for x in np.unique(y_true) if x != advantage_outcome]
        label_list.append(advantage_outcome)
        conf_matrix = confusion_matrix(y_true, y_pred, labels=label_list, sample_weight=sample_weight)

        true_negative = conf_matrix[0][0]
        false_negative = conf_matrix[1][0]
        true_positive = conf_matrix[1][1]
        false_positive = conf_matrix[0][1]

        return true_negative, false_negative, true_positive, false_positive

    @staticmethod
    def demographic_parity(y_true, y_pred, advantage_outcome, sample_weight=None):
        """
        demographic_parity just care about y_pred, but we keep y_true to have a homogene api
        """
        return np.sum(y_pred == advantage_outcome, dtype=float) / len(y_pred)

    @staticmethod
    def equality_of_opportunity(y_true, y_pred, advantage_outcome, sample_weight=None):
        true_negative, false_negative, true_positive, false_positive = ModelFairnessMetric._compute_confusion_matrix_metrics(y_true, y_pred, advantage_outcome, sample_weight)
        # Sensitivity, hit rate, recall, or true positive rate
        true_positive_rate = true_positive / (true_positive + false_negative)

        return true_positive_rate


    @staticmethod
    def equalized_odds(y_true, y_pred, advantage_outcome, sample_weight=None):
        true_negative, false_negative, true_positive, false_positive = ModelFairnessMetric._compute_confusion_matrix_metrics(y_true, y_pred, advantage_outcome, sample_weight)
        true_positive_rate = true_positive / (true_positive + false_negative)
        false_positive_rate = false_positive / (true_negative + false_positive)
        return true_positive_rate, false_positive_rate

    @staticmethod
    def predictive_rate_parity(y_true, y_pred, advantage_outcome, sample_weight=None):
        true_negative, false_negative, true_positive, false_positive = ModelFairnessMetric._compute_confusion_matrix_metrics(y_true, y_pred, advantage_outcome, sample_weight)
        # Precision or positive predictive value
        positive_predictive_value = true_positive / (true_positive + false_positive)
        return positive_predictive_value


class ModelFairnessMetricReport(object):
    def __init__(self, y_true, y_pred, sensitive_features, reference_group=None, advantage_outcome=None,
                 sample_weight=None):
        self.y_true = y_true  # 1D array
        self.y_pred = y_pred  # 1D array
        self.sensitive_features = sensitive_features  # 1D array
        self.reference_group = reference_group  # string
        self.advantage_outcome = advantage_outcome  # string
        self.sample_weight = sample_weight  # 1D array

    def compute_metric_per_group(self, metric_function):
        """
        metric_function is a function with signature metric_function(y_true, y_pred, *metric_params)
        """
        return group_summary(metric_function,
                             self.y_true,
                             self.y_pred,
                             sensitive_features=self.sensitive_features,
                             advantage_outcome=self.advantage_outcome)

    def compute_group_difference_from_summary(self, summary, reference_group=DkuFairnessConstants.OVERALL):

        difference_by_group = {}
        # if there is no reference group, take the overall metric
        if reference_group == DkuFairnessConstants.OVERALL:
            reference_metrics = summary.get(DkuFairnessConstants.OVERALL)
        else:
            if reference_group not in summary.get(DkuFairnessConstants.BY_GROUP).keys():
                raise ValueError(
                    'The chosen reference group "{0}" is not in the input metric summary.'.format(reference_group))
            reference_metrics = summary[DkuFairnessConstants.BY_GROUP][reference_group]

        for group, group_metrics in summary.get(DkuFairnessConstants.BY_GROUP).items():
            difference_by_group[group] = np.array(group_metrics) - np.array(reference_metrics)

        # TODO decide if it is a good idea to put overall metric here
        difference_by_group[DkuFairnessConstants.OVERALL] = np.array(summary.get(DkuFairnessConstants.OVERALL)) - np.array(reference_metrics)

        return Bunch(reference_group=reference_group, by_group=difference_by_group)

    def compute_group_ratio_from_summary(self, summary, reference_group=DkuFairnessConstants.OVERALL):

        ratio_by_group = {}
        # if there is no reference group, take the overall metric
        if reference_group == DkuFairnessConstants.OVERALL:
            reference_metrics = summary.get(DkuFairnessConstants.OVERALL)
        else:
            if reference_group not in summary.get(DkuFairnessConstants.BY_GROUP).keys():
                raise ValueError('The chosen reference group "{0}" is not in the input metric summary.'.format(reference_group))
            reference_metrics = summary[DkuFairnessConstants.BY_GROUP][reference_group]

        for group, group_metrics in summary.get(DkuFairnessConstants.BY_GROUP).items():
            ratio_by_group[group] = np.array(group_metrics) / np.array(reference_metrics)

        # TODO decide if it is a good idea to put overall metric here
        ratio_by_group[DkuFairnessConstants.OVERALL] = np.array(summary.get(DkuFairnessConstants.OVERALL)) / np.array(reference_metrics)

        return Bunch(reference_group=reference_group, by_group=ratio_by_group)