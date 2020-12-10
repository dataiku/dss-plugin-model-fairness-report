# -*- coding: utf-8 -*-

"""
    Simple functions helpers
"""

import logging
import sys

logger = logging.getLogger(__name__)

logger.info("Python version: {}".format(sys.version))
# python3 does not have basetring
try:
    basestring
except NameError:
    basestring = str


def schema_are_compatible(df1, df2):
    """
    Return True if df1 and df2 have the same columns
    :param df1: Pandas dataframe
    :param df2: Pandas dataframe
    :return:
    """
    return set(df1.columns) == set(df2.columns)


def not_enough_data(df, min_len=1):
    """
        Compare length of dataframe to minimum lenght of the test data.
        Used in the relevance of the measure.
    :param df: Input dataframe
    :param min_len:
    :return:
    """
    return len(df) < min_len


def nothing_to_do(stuff):
    return stuff is None