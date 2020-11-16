import dataiku
import logging
import simplejson
import traceback
from dku_model_accessor import get_model_handler, ModelAccessor
from dku_webapp import remove_nan_from_list, convert_numpy_int64_to_int, get_metrics, get_histograms,DkuWebappConstants

logger = logging.getLogger(__name__)

@app.route("/get-value-list/<model_id>/<version_id>/<column>")
def get_value_list(model_id, version_id, column):
    try:
        model = dataiku.Model(model_id)
        model_handler = get_model_handler(model, version_id=version_id)
        model_accessor = ModelAccessor(model_handler)
        test_df = model_accessor.get_original_test_df()
        value_list = test_df[column].unique().tolist()  # should check for categorical variables ?
        filtered_value_list = remove_nan_from_list(value_list)

        if len(filtered_value_list) > DkuWebappConstants.MAX_NUM_CATEGORIES:
            raise ValueError('Column "{2}" has too many categories ({0}). Max {1} are allowed'.format(len(filtered_value_list), DkuWebappConstants.MAX_NUM_CATEGORIES, column))

        return simplejson.dumps(filtered_value_list, ignore_nan=True, default=convert_numpy_int64_to_int)
    except:
        logger.error("{}. Check backend log for more details.".format(traceback.format_exc()))
        return traceback.format_exc(), 500

@app.route('/get-feature-list/<model_id>/<version_id>')
def get_feature_list(model_id, version_id):
    try:
        model = dataiku.Model(model_id)
        model_handler = get_model_handler(model, version_id=version_id)
        model_accessor = ModelAccessor(model_handler)
        column_list = model_accessor.get_selected_features()
        return simplejson.dumps(column_list, ignore_nan=True, default=convert_numpy_int64_to_int)
    except:
        logger.error("{}. Check backend log for more details.".format(traceback.format_exc()))
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
        logger.error("{}. Check backend log for more details.".format(traceback.format_exc()))
        return traceback.format_exc(), 500

@app.route('/get-data/<model_id>/<version_id>/<advantageous_outcome>/<sensitive_column>/<reference_group>')
def get_data(model_id, version_id, advantageous_outcome, sensitive_column, reference_group):
    try:
        populations, disparity_dct, label_list = get_metrics(model_id, version_id, advantageous_outcome, sensitive_column, reference_group)
        histograms = get_histograms(model_id, version_id, advantageous_outcome, sensitive_column)
        # the following strings are used only here, too lazy to turn them into constant variables
        data = {'populations': populations,
                'histograms': histograms,
                'disparity': disparity_dct,
                'labels': label_list
                }
        return simplejson.dumps(data, ignore_nan=True, default=convert_numpy_int64_to_int)
    except:
        logger.error("{}. Check backend log for more details.".format(traceback.format_exc()))
        return traceback.format_exc(), 500
