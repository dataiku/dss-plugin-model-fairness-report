import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.utils import Bunch

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



"""
Implementation of group_summary function from fairlearn v0.4.6: https://github.com/fairlearn/fairlearn 
"""

def _convert_to_ndarray_and_squeeze(target):
    """Convert input to a `numpy.ndarray` and calls squeeze (to dispose of unit length dimensions).

    There is a special case to stop single element arrays being converted to scalars.
    """
    result = np.asarray(target)

    if result.size > 1:
        result = np.squeeze(result)
    else:
        result = result.reshape(1)

    return result


def _check_array_sizes(a, b, a_name, b_name):
    if len(a) != len(b):
        raise ValueError("Array {0} is not the same size as {1}".format(b_name, a_name))

# This loosely follows the pattern of _check_fit_params in
# sklearn/utils/validation.py
def _check_metric_params(y_true, metric_params,
                         indexed_params=None, indices=None):
    metric_params_validated = {}
    if indexed_params is None:
        indexed_params = {"sample_weight"}
    for param_key, param_value in metric_params.items():
        if (param_key in indexed_params and param_value is not None):
            _check_array_sizes(y_true, param_value, 'y_true', param_key)
            p_v = _convert_to_ndarray_and_squeeze(param_value)
            if indices is not None:
                p_v = p_v[indices]
            metric_params_validated[param_key] = p_v
        else:
            metric_params_validated[param_key] = param_value

    return metric_params_validated

def group_summary(metric_function, y_true, y_pred, *,
                  sensitive_features,
                  indexed_params=None,
                  **metric_params):
    r"""Apply a metric to each subgroup of a set of data.

    :param metric_function: Function with signature
        ``metric_function(y_true, y_pred, \*\*metric_params)``

    :param y_true: Array of ground-truth values

    :param y_pred: Array of predicted values

    :param sensitive_features: Array indicating the group to which each input value belongs

    :param indexed_params: Names of ``metric_function`` parameters that
        should be split according to ``sensitive_features`` in addition to ``y_true``
        and ``y_pred``. Defaults to ``None`` corresponding to ``{"sample_weight"}``.

    :param \*\*metric_params: Optional arguments to be passed to the ``metric_function``

    :return: Object containing the result of applying ``metric_function`` to the entire dataset
        and to each group identified in ``sensitive_features``
    :rtype: :py:class:`sklearn.utils.Bunch` with the fields ``overall`` and ``by_group``
    """
    _check_array_sizes(y_true, y_pred, 'y_true', 'y_pred')
    _check_array_sizes(y_true, sensitive_features, 'y_true', 'sensitive_features')

    # Make everything a numpy array
    # This allows for fast slicing of the groups
    y_t = _convert_to_ndarray_and_squeeze(y_true)
    y_p = _convert_to_ndarray_and_squeeze(y_pred)
    s_f = _convert_to_ndarray_and_squeeze(sensitive_features)

    # Evaluate the overall metric with the numpy arrays
    # This ensures consistency in how metric_function is called
    result_overall = metric_function(
        y_t, y_p,
        **_check_metric_params(y_t, metric_params, indexed_params))

    groups = np.unique(s_f)
    result_by_group = {}
    for group in groups:
        group_indices = (group == s_f)
        result_by_group[group] = metric_function(
            y_t[group_indices], y_p[group_indices],
            **_check_metric_params(y_t, metric_params, indexed_params, group_indices))

    return Bunch(overall=result_overall, by_group=result_by_group)
