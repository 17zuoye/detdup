# -*- coding: utf-8 -*-

import os, sys
current_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(current_dir)

from detdup.services.task import DetDupTask

from tests.models import cache_dir, OriginalModel, CleanModel, PLFeature

detdup_opts = {
        "process_count"             : 3,

        "cache_dir"                 : cache_dir,

        "original_model"            : OriginalModel,
        "items_model"               : CleanModel,

        "features"                  : [PLFeature],

        "query_check_columns"       : ["desc"],
    }
ddt = DetDupTask(detdup_opts)
