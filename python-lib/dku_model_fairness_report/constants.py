# -*- coding: utf-8 -*-

class DkuFairnessConstants(object):

    TIMESTAMP = 'timestamp'
    MODEL_ID = 'model_id'
    VERSION_ID = 'version_id'
    TRAIN_DATE = 'train_date'

    MIN_NUM_ROWS = 500
    MAX_NUM_ROW = 100000
    CUMULATIVE_PERCENTAGE_THRESHOLD = 90
    PREDICTION_TEST_SIZE = 100000

    REGRRSSION_TYPE = 'REGRESSION'
    CLASSIFICATION_TYPE = 'CLASSIFICATION'
    CLUSTERING_TYPE = 'CLUSTERING'

    FEAT_IMP_CUMULATIVE_PERCENTAGE_THRESHOLD = 95
    RISKIEST_FEATURES_RATIO_THRESHOLD = 0.65

    FEATURE = 'feature'
    IMPORTANCE = 'importance'
    CUMULATIVE_IMPORTANCE = 'cumulative_importance'
    RANK = 'rank'
    CLASS = 'class'
    PERCENTAGE = 'percentage'
    ORIGINAL_DATASET = 'original_dataset'
    NEW_DATASET = 'new_dataset'

    OVERALL = 'overall' # can not change as fairlearn returns this value
    BY_GROUP = 'by_group'

    NUMBER_OF_DECIMALS = 3