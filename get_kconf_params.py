# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# Author     ：Bo Wang
# File       : get_kconf_params.py
# Time       ：2023/2/10 16:40
"""
from enum import Flag
import numpy as np
import traceback
import re
import threading
import time
import json
import logging
from unicodedata import category

from infra.kafka import (
    ConsumerParameter,
    KsKafkaConsumer,
    MessageContext,
    KafkaProducers,
    FinishConsumeException
)

from kconf.get_config import (get_int32_config, get_string_config,
                              get_int64_config, get_bool_config,
                              get_list_string_config, get_string_string_config,
                              get_string_int32_config, get_string_int64_config,
                              get_list_int64_config,
                              get_json_config, get_tail_number_config)
from kconf.exception import KConfError

from infra.perflog import create_perf_context


logger = logging.getLogger("__main__")


def setup_logger():
    fmt_str = ('%(asctime)s.%(msecs)03d %(levelname)7s '
               '[%(thread)d][%(process)d] %(message)s')
    fmt = logging.Formatter(fmt_str, datefmt='%H:%M:%S')
    handler = logging.handlers.TimedRotatingFileHandler('./consumer_server.log', when='D', interval=1, backupCount=30)
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def get_kconf_value(kconf_key, kconf_type):
    kconf_value = None
    try:
        if kconf_type == 'int32':
            kconf_value = get_int32_config(kconf_key)
        if kconf_type == 'string':
            kconf_value = get_string_config(kconf_key)
        if kconf_type == 'int64':
            kconf_value = get_int64_config(kconf_key)
        if kconf_type == 'bool':
            kconf_value = get_bool_config(kconf_key)
        if kconf_type == 'list':
            kconf_value = get_list_string_config(kconf_key)
        if kconf_type == 'map_string_string':
            kconf_value = get_string_string_config(kconf_key)
        if kconf_type == 'map_string_int32':
            kconf_value = get_string_int32_config(kconf_key)
        if kconf_type == 'map_string_int64':
            kconf_value = get_string_int64_config(kconf_key)
        if kconf_type == 'list_int64':
            kconf_value = get_list_int64_config(kconf_key)
        if kconf_type == 'list_string':
            kconf_value = get_list_string_config(kconf_key)
        if kconf_type == 'json':
            kconf_value = get_json_config(kconf_key)
        if kconf_type == 'tail_number':
            kconf_value = get_tail_number_config(kconf_key)
    except KConfError as e:
        logger.error(e)
    return kconf_value


if __name__ == "__main__":
    kconf_value = get_kconf_value("ad.algorithm.nieuwlandGeneration", "json")
    print(kconf_value)
