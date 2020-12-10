import numpy as np
from sklearn.metrics import confusion_matrix

from dku_model_fairness_report.constants import DkuFairnessConstants


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
        demographic_parity just care about y_pred, but we keep y_true to have a homogeneous api
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