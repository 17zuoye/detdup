# -*- coding: utf-8 -*-

import os
root_dir = os.path.dirname(os.path.abspath(__file__))
cache_dir = root_dir + '/output'

import mongomock
OriginalModel = mongomock.Connection().db.OriginalModel
# 这里只有Python和JavaScript是重复的
pls = (u"Ruby Rails Python Python Java JavaScript JavaScript CoffeeScript Julia"
       u"Juila Closure Scala Groovy Objective-C C C++ Perl PHP Haskell Erlang R").split(u" ")

def generate_record(name, idx=None):
    d1 = {u"content" : name + u" programming language"}
    if idx: d1[u"subject_id"] = idx
    return d1

for idx, pl in enumerate(pls):
    OriginalModel.insert(generate_record(pl,  idx))

from detdup.data_model import DetDupDataModel
from model_cache import ModelCache

@ModelCache.connect(OriginalModel, storage_type='sqlite', \
                                   cache_dir=cache_dir, \
                                   included_class=DetDupDataModel)
class CleanModel():
    def init__load_data(self, record):
        if u"item_id" not in dir(self): self.item_id = record[u'_id']
        self.item_id      = unicode(self.item_id)
        self.item_content = record[u'content'].split(u" ")[0]

        self.desc         = u" ".join(record[u'content'].split(u" ")[1:])
        self.typename     = "pl"

from detdup.features.default import DefaultFeatures
class PLFeature(DefaultFeatures):
    def post_init(self):
        self.typename      = 'pl'

        self.custom_features = {
            'desc' : str,
          }
