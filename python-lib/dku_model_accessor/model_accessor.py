# -*- coding: utf-8 -*-
import logging
import pandas as pd
from dku_model_accessor.constants import DkuModelAccessorConstants

logger = logging.getLogger(__name__)

class ModelAccessor(object):
    def __init__(self, model_handler=None):
        self.model_handler = model_handler

    def get_prediction_type(self):
        """
        Wrap the prediction type accessor of the model
        """
        if DkuModelAccessorConstants.CLASSIFICATION_TYPE in self.model_handler.get_prediction_type():
            return DkuModelAccessorConstants.CLASSIFICATION_TYPE
        elif DkuModelAccessorConstants.REGRRSSION_TYPE in self.model_handler.get_prediction_type():
            return DkuModelAccessorConstants.REGRRSSION_TYPE
        else:
            return DkuModelAccessorConstants.CLUSTERING_TYPE

    def get_target_variable(self):
        """
        Return the name of the target variable
        """
        return self.model_handler.get_target_variable()

    def get_original_test_df(self, limit=DkuModelAccessorConstants.MAX_NUM_ROW):
        try:
            full_test_df = self.model_handler.get_test_df()[0]
            test_df = full_test_df[:limit]
            logger.info('Loading {}/{} rows of the original test set'.format(len(test_df), len(full_test_df)))
            return test_df
        except Exception as e:
            logger.warning('Can not retrieve original test set: {}. The plugin will take the whole original dataset.'.format(e))
            full_test_df = self.model_handler.get_full_df()[0]
            test_df = full_test_df[:limit]
            logger.info('Loading {}/{} rows of the whole original test set'.format(len(test_df), len(full_test_df)))
            return test_df

    def get_train_df(self, limit=DkuModelAccessorConstants.MAX_NUM_ROW):
        full_train_df = self.model_handler.get_train_df()[0]
        train_df = full_train_df[:limit]
        logger.info('Loading {}/{} rows of the original train set'.format(len(train_df), len(full_train_df)))
        return train_df

    def get_per_feature(self):
        return self.model_handler.get_per_feature()

    def get_predictor(self):
        return self.model_handler.get_predictor()

    def get_selected_and_rejected_features(self):
        """
        Return all features in the input dataset except the target
        """
        selected_features = []
        for feat, feat_info in self.get_per_feature().items():
            if feat_info.get('role') in ['INPUT', 'REJECT']:
                selected_features.append(feat)
        return selected_features

    def predict(self, df):
        return self.get_predictor().predict(df)
