import dataiku
import pandas as pd
import numpy as np
import logging
import json
import traceback

dataiku.use_plugin_libs('model-fairness-report')
from model_metadata import get_model_handler
from dku_model_accessor.model_accessor import ModelAccessor
from dku_model_fairness_report.fairness_metric_report import ModelFairnessMetricReport, ModelFairnessMetric

logger = logging.getLogger(__name__)


def get_histogram_data(y_true, y_pred, y_pred_proba, advantageous_outcome, sensitive_feature_values):
    df = pd.DataFrame()
    df['bin_index'] = np.digitize(y_pred_proba, np.arange(0, 1, step=0.1))  # 20 bins
    df['prediction_result_type'] = get_prediction_result_type(y_true, y_pred, advantageous_outcome)
    df['sensitive_feature'] = sensitive_feature_values

    histogram_dict = {}
    for v in df['sensitive_feature'].unique():

        df2 = df[df['sensitive_feature'] == v]
        dfx = np.round(100 * df2.groupby(['prediction_result_type', 'bin_index']).size() / len(df2), 3)
        df_final = dfx.unstack().fillna(0).stack()

        dct = {}
        for i in df_final.index.levels[0]:
            dct[i] = df_final[i].values.tolist()

        histogram_dict[v] = dct

    return histogram_dict


def convert_numpy_int64_to_int(o):
    if isinstance(o, np.int64):
        return int(o)
    raise TypeError


def get_prediction_result_type(y_true, y_pred, advantageous_outcome):
    df = pd.DataFrame()
    df['predicted'] = y_pred
    df['true'] = y_true

    result_type = []

    for predicted_label, true_label in zip(y_pred, y_true):
        if predicted_label != advantageous_outcome and true_label != advantageous_outcome:
            result_type.append('predicted_0_true_0')
        elif predicted_label != advantageous_outcome and true_label == advantageous_outcome:
            result_type.append('predicted_0_true_1')
        elif predicted_label == advantageous_outcome and true_label == advantageous_outcome:
            result_type.append('predicted_1_true_1')
        elif predicted_label == advantageous_outcome and true_label != advantageous_outcome:
            result_type.append('predicted_1_true_0')
        else:
            raise ValueError('Unknown combination.')

    return result_type


@app.route("/get-value-list/<column>")
def get_value_list(column):
    lst = []
    if column == 'a':
        lst = [1, 2, 3]
    elif column == 'b':
        lst = [4, 5, 6]
    else:
        lst = [7, 8, 9]

    return json.dumps(lst, allow_nan=False, default=convert_numpy_int64_to_int)


@app.route('/get-column-list')
def get_column_list():
    lst = ['a', 'b', 'c']

    return json.dumps(lst, allow_nan=False, default=convert_numpy_int64_to_int)


@app.route('/get-outcome-list')
def get_outcome_list():
    lst = ['5000+', '5000-']

    return json.dumps(lst, allow_nan=False, default=convert_numpy_int64_to_int)


@app.route('/get-data')
def get_data():
    try:
        print('Getting data')
        populations, disparity_dct = get_metrics()
        histograms = get_histograms()
        data = {'populations': populations,
                'histograms': histograms,
                'disparity': disparity_dct
                }

        return json.dumps(data, allow_nan=False, default=convert_numpy_int64_to_int)

    except:
        logger.error(traceback.format_exc())
        return traceback.format_exc(), 500


def get_histograms():
    try:
        print('histograms')
        model = dataiku.Model('LZ1rGMmQ')
        model_handler = get_model_handler(model)
        model_accessor = ModelAccessor(model_handler)

        advantageous_outcome = '50000+.'
        test_df = model_accessor.get_original_test_df()
        target_variable = model_accessor.get_target_variable()

        y_true = test_df.loc[:, target_variable]
        pred_df = model_accessor.predict(test_df)
        y_pred = pred_df.loc[:, 'prediction']
        advantageous_outcome_proba_col = 'proba_{}'.format(advantageous_outcome)
        y_pred_proba = pred_df.loc[:, advantageous_outcome_proba_col]
        sensitive_feature_values = test_df['sex']

        return get_histogram_data(y_true, y_pred, y_pred_proba, advantageous_outcome, sensitive_feature_values)
    except:
        logger.error(traceback.format_exc())
        return traceback.format_exc(), 500


def get_metrics():
    try:
        print('metrics')

        model = dataiku.Model('LZ1rGMmQ')
        model_handler = get_model_handler(model)
        model_accessor = ModelAccessor(model_handler)

        advantageous_outcome = '50000+.'
        test_df = model_accessor.get_original_test_df()
        target_variable = model_accessor.get_target_variable()

        y_true = test_df.loc[:, target_variable]
        pred_df = model_accessor.predict(test_df)
        y_pred = pred_df.loc[:, 'prediction']
        sensitive_feature_values = test_df['sex']

        model_report = ModelFairnessMetricReport(y_true, y_pred, sensitive_feature_values, advantageous_outcome)

        population_names = sensitive_feature_values.unique()

        metric_dct = {}
        disparity_dct = {}
        for metric_func in ModelFairnessMetric.get_available_metric_functions():
            metric_summary = model_report.compute_metric_per_group(metric_function=metric_func)
            metric_dct[metric_func.__name__] = metric_summary.get('by_group')

            metric_diff = model_report.compute_group_difference_from_summary(metric_summary, reference_group='Male')
            v = np.array(list(metric_diff.get('by_group').values())).reshape(1, -1).squeeze()
            max_disparity = max(v, key=abs)
            disparity_dct[metric_func.__name__] = max_disparity

        populations = []
        for name in population_names:
            dct = {'name': name}
            for m, v in metric_dct.items():
                if m == 'demographic_parity':
                    dct['positive_rate'] = v[name]
                if m == 'equalized_odds':
                    dct['true_positive_rate'], dct['false_positive_rate'] = v[name]
                if m == 'predictive_rate_parity':
                    dct['positive_predictive_value'] = v[name]
            populations.append(dct)

        return populations, disparity_dct

    except:
        logger.error(traceback.format_exc())
        return traceback.format_exc(), 500
