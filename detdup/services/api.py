# -*- coding: utf-8 -*-

from .task import *
from ..data_model.fake_item_ids import FakeItemIds

class DetDupApi(DetDupTask):

    def init_api(self, storage_type='disk'):
        self.items_model.bind_a_fake_item_ids_store()

        self.core = self.new_detdup_core(storage_type)
        self.core.should_reduce_items = False

    def is_all_duplicated(self, item_ids):
        """ Check item_ids is same to each other """
        if item_ids <= 1: return True

        result = list()
        for item_id1 in item_ids:
            ids = self.core.detect_duplicated_items_verbose(item_id1)
            ids.remove(item_id1)
            result.extend(ids)
        return sorted(set(result)) == sorted(item_ids)

    def process_record(self, record):
        # 被动式清理 老的数据，在它的下一次数据请求前
        self.items_model.fake_item_ids_store.remove_all()

# NOTE 这里就不能直接往 items.cPickleCache 里直接写了
        # 1. insert item
        item1 = self.items_model(record)

        # 参考 .task.py
        self.items_model.feed_data([item1]) # 提供给 #[] 使用

        # 2. append to indexes
        self.core.feed_items([item1], persist=False)

        return item1

    def query_item_features(self, record):
        item1 = self.process_record(record)

        return item1.inspect()


    def detect_duplicated_items(self, record):
        item1 = self.process_record(record)

        # 3. query duplicated
        result = self.core.detect_duplicated_items_verbose(item1.item_id)

        # 4. remove self
        result.remove(item1.item_id)

        return result
