import dataiku
import logging
import simplejson
import traceback
from dataiku.customwebapp import get_webapp_config
from dataiku.doctor.posttraining.model_information_handler import PredictionModelInformationHandler
from dku_model_accessor import ModelAccessor, DkuModelAccessorConstants
from dku_webapp import remove_nan_from_list, convert_numpy_int64_to_int, get_metrics, get_histograms, DkuWebappConstants

logger = logging.getLogger(__name__)

model_accessor = ModelAccessor()

@app.route("/check-model-type")
def check_model_type():
    try:
        fmi = get_webapp_config().get("trainedModelFullModelId")
        if fmi is None:
            model_id, version_id = get_webapp_config()["modelId"], get_webapp_config().get("versionId")

            fmi = "S-{project_key}-{model_id}-{version_id}".format(
                project_key=dataiku.default_project_key(), model_id=model_id, version_id=version_id
            )

        model_handler = PredictionModelInformationHandler.from_full_model_id(fmi)
        model_accessor.model_handler = model_handler

        if model_accessor.get_prediction_type() in [DkuModelAccessorConstants.REGRRSSION_TYPE, DkuModelAccessorConstants.CLUSTERING_TYPE]:
            raise ValueError('Model Fairness Report only supports binary classification model.')
        return 'ok'
    except:
        logger.error("When trying to call check-model-type endpoint: {}.".format(traceback.format_exc()))
        return "{}Check backend log for more details.".format(traceback.format_exc()), 500

@app.route("/get-value-list/<column>")
def get_value_list(column):
    try:
        if column == 'undefined' or column == 'null':
            raise ValueError('Please choose a column.')

        test_df = model_accessor.get_original_test_df()
        value_list = test_df[column].unique().tolist()  # should check for categorical variables ?
        filtered_value_list = remove_nan_from_list(value_list)

        if len(filtered_value_list) > DkuWebappConstants.MAX_NUM_CATEGORIES:
            raise ValueError('Column "{2}" is either of numerical type or has too many categories ({0}). Max {1} are allowed.'.format(len(filtered_value_list), DkuWebappConstants.MAX_NUM_CATEGORIES, column))

        return simplejson.dumps(filtered_value_list, ignore_nan=True, default=convert_numpy_int64_to_int)
    except:
        logger.error("When trying to call get-value-list endpoint: {}.".format(traceback.format_exc()))
        return "{}Check backend log for more details.".format(traceback.format_exc()), 500

@app.route('/get-feature-list')
def get_feature_list():
    try:
        column_list = model_accessor.get_selected_and_rejected_features()
        return simplejson.dumps(column_list, ignore_nan=True, default=convert_numpy_int64_to_int)
    except:
        logger.error("When trying to call get-feature-list endpoint: {}.".format(traceback.format_exc()))
        return "{}Check backend log for more details.".format(traceback.format_exc()), 500

@app.route('/get-outcome-list')
def get_outcome_list():
    try:
        # note: sometimes when the dataset is very unbalanced, the original_test_df does not have all the target values
        test_df = model_accessor.get_original_test_df()
        target = model_accessor.get_target_variable()
        outcome_list = test_df[target].unique().tolist()
        filtered_outcome_list = remove_nan_from_list(outcome_list)
        return simplejson.dumps(filtered_outcome_list, ignore_nan=True, default=convert_numpy_int64_to_int)
    except:
        logger.error("When trying to call get-outcome-list endpoint: {}.".format(traceback.format_exc()))
        return "{}Check backend log for more details.".format(traceback.format_exc()), 500

@app.route('/get-data/<advantageous_outcome>/<sensitive_column>/<reference_group>')
def get_data(advantageous_outcome, sensitive_column, reference_group):
    try:
        if sensitive_column == 'undefined' or sensitive_column == 'null':
            raise ValueError('Please choose a column.')
        if reference_group == 'undefined' or reference_group == 'null':
            raise ValueError('Please choose a sensitive group.')
        if  advantageous_outcome == 'undefined' or advantageous_outcome == 'null':
            raise ValueError('Please choose an outcome.')

        populations, disparity_dct, label_list = get_metrics(model_accessor, advantageous_outcome, sensitive_column, reference_group)
        histograms = get_histograms(model_accessor, advantageous_outcome, sensitive_column)
        # the following strings are used only here, too lazy to turn them into constant variables
        data = {
            'populations': populations,
            'histograms': histograms,
            'disparity': disparity_dct,
            'labels': label_list
        }
        return simplejson.dumps(data, ignore_nan=True, default=convert_numpy_int64_to_int)
    except:
        logger.error("When trying to call get-data endpoint: {}.".format(traceback.format_exc()))
        return "{}Check backend log for more details.".format(traceback.format_exc()), 500
