# -*- coding: utf-8 -*-

import os
import glob, sys
from bson.objectid import ObjectId
from termcolor import colored, cprint
from datetime import datetime
import logging

from etl_utils import cpickle_cache, process_notifier, HashUtils
hashvalue_with_sorted = HashUtils.hashvalue_with_sorted

# system info
import multiprocessing
max_process_count = ('Darwin' in os.uname()) and (multiprocessing.cpu_count()-1) or 8
