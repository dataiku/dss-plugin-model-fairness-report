import dataiku
import pandas as pd
import numpy as np
import logging
from flask import request
import simplejson
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
        series_final = dfx.unstack().fillna(0).stack()

        computed_df = pd.DataFrame(series_final, columns=['bin_value_new'])
        arrays = [['predicted_0_true_0', 'predicted_0_true_1', 'predicted_1_true_0', 'predicted_1_true_1'], np.arange(1, 11)]
        reference_df = pd.DataFrame(index=pd.MultiIndex.from_product(arrays, names=('prediction_result_type', 'bin_index')))
        reference_df['bin_value'] = 0
        result_df = pd.concat([reference_df, computed_df], axis=1, sort=False)
        # replace missing value by 0
        result_df['bin_value_final'] = result_df['bin_value_new'].fillna(result_df['bin_value'])

        dct = {}
        for i in result_df.index.levels[0]:
            dct[i] = result_df.xs(i, level='prediction_result_type')['bin_value_final'].values.tolist()

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

def remove_nan_from_list(lst):
    new_list = []
    for x in lst:
        if isinstance(x, float) and np.isnan(x):
            continue
        else:
            new_list.append(x)
    return new_list

@app.route("/get-value-list/<model_id>/<version_id>/<column>")
def get_value_list(model_id, version_id, column):
    try:
        model = dataiku.Model(model_id)
        model_handler = get_model_handler(model, version_id=version_id)
        model_accessor = ModelAccessor(model_handler)
        test_df = model_accessor.get_original_test_df()
        value_list = test_df[column].unique().tolist()  # should check for categorical variables ?
        filtered_value_list= remove_nan_from_list(value_list)
        return simplejson.dumps(filtered_value_list, ignore_nan=True, default=convert_numpy_int64_to_int)
    except:
        logger.error(traceback.format_exc())
        return traceback.format_exc(), 500


@app.route('/get-column-list/<model_id>/<version_id>')
def get_column_list(model_id, version_id):
    try:
        model = dataiku.Model(model_id)
        model_handler = get_model_handler(model, version_id=version_id)
        model_accessor = ModelAccessor(model_handler)
        column_list = model_accessor.get_selected_features()
        return simplejson.dumps(column_list, ignore_nan=True, default=convert_numpy_int64_to_int)
    except:
        logger.error(traceback.format_exc())
        return traceback.format_exc(), 500

@app.route('/get-outcome-list/<model_id>/<version_id>')
def get_outcome_list(model_id, version_id):
    try:
        model = dataiku.Model(model_id)
        model_handler = get_model_handler(model, version_id=version_id)
        model_accessor = ModelAccessor(model_handler)
        test_df = model_accessor.get_original_test_df()
        target = model_accessor.get_target_variable()
        outcome_list = test_df[target].unique().tolist()
        filtered_outcome_list = remove_nan_from_list(outcome_list)
        return simplejson.dumps(filtered_outcome_list, ignore_nan=True, default=convert_numpy_int64_to_int)

    except:
        logger.error(traceback.format_exc())
        return traceback.format_exc(), 500

@app.route('/get-data/<model_id>/<version_id>/<advantageous_outcome>/<sensitive_outcome>/<reference_group>')
def get_data(model_id, version_id, advantageous_outcome, sensitive_outcome, reference_group):
    try:
        populations, disparity_dct = get_metrics(model_id, version_id, advantageous_outcome, sensitive_outcome,reference_group)
        histograms = get_histograms(model_id, version_id, advantageous_outcome, sensitive_outcome)
        data = {'populations': populations,
                'histograms': histograms,
                'disparity': disparity_dct
                }
        return simplejson.dumps(data, ignore_nan=True, default=convert_numpy_int64_to_int)

    except:
        logger.error(traceback.format_exc())
        return traceback.format_exc(), 500


def get_histograms(model_id, version_id, advantageous_outcome, sensitive_outcome):

    model = dataiku.Model(model_id)
    model_handler = get_model_handler(model, version_id=version_id)
    model_accessor = ModelAccessor(model_handler)

    test_df = model_accessor.get_original_test_df()
    target_variable = model_accessor.get_target_variable()

    y_true = test_df.loc[:, target_variable]
    pred_df = model_accessor.predict(test_df)
    y_pred = pred_df.loc[:, 'prediction']

    advantageous_outcome_proba_col = 'proba_{}'.format(advantageous_outcome)
    y_pred_proba = pred_df.loc[:, advantageous_outcome_proba_col]
    sensitive_feature_values = test_df[sensitive_outcome]

    return get_histogram_data(y_true, y_pred, y_pred_proba, advantageous_outcome, sensitive_feature_values)



def get_metrics(model_id, version_id, advantageous_outcome, sensitive_column, reference_group):

    model = dataiku.Model(model_id)
    model_handler = get_model_handler(model, version_id=version_id)
    model_accessor = ModelAccessor(model_handler)

    test_df = model_accessor.get_original_test_df()
    target_variable = model_accessor.get_target_variable()
    test_df.dropna(subset=[sensitive_column, target_variable], how='any', inplace=True)

    y_true = test_df.loc[:, target_variable]
    pred_df = model_accessor.predict(test_df)
    y_pred = pred_df.loc[:, 'prediction']
    sensitive_feature_values = test_df[sensitive_column]

    model_report = ModelFairnessMetricReport(y_true, y_pred, sensitive_feature_values, advantageous_outcome)

    population_names = sensitive_feature_values.unique()

    metric_dct = {}
    disparity_dct = {}
    for metric_func in ModelFairnessMetric.get_available_metric_functions():
        metric_summary = model_report.compute_metric_per_group(metric_function=metric_func)
        metric_dct[metric_func.__name__] = metric_summary.get('by_group')
        metric_diff = model_report.compute_group_difference_from_summary(metric_summary, reference_group=reference_group)
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

        # make sure that NaN is replaced by a string (a dot here), for display purpose
        for k, v in dct.items():
            if not isinstance(v, str) and np.isnan(v):
                dct[k] = '.'
        populations.append(dct)

    return populations, disparity_dct

