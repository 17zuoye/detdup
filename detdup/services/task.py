# -*- coding: utf-8 -*-

# TODO 多进程 有木桶最短效应。但是目前没法解决变量共享。

import json
import math
import time

from ..utils import *
from ..core import DetDupCore

class DetDupTask(object):
    default_attrs = [
            "process_count",

            "cache_dir",

            "original_model",
            "items_model",

            "features",

            "query_check_columns",
        ]

    def __init__(self, opts):
        for key1 in DetDupTask.default_attrs:
            setattr(self, key1, opts.get(key1, None))
        self.process_count = self.process_count or max_process_count

        self.items_model               = opts['items_model']
        self.items_model.cache_dir     = self.cache_dir
        self.items_model.datadict_type = "sqlite"

        self.result_cPickle = os.path.join(self.cache_dir, "detdup.cPickle")
        self.result_json    = os.path.join(self.cache_dir, "detdup.json")

    def new_detdup_core(self, storage_type='memory'):
        """ new queryinterface """
        # 每个instance只能被generator, 否则这些进程同时访问一个IO, 那么所有CPU就都处于等待IO中不动了

        detdup = DetDupCore(self.cache_dir, self.items_model)

        detdup.is_inspect_detail = False

        detdup.storage_type = storage_type

        for feature1 in self.features:
            detdup.plug_features(feature1())

        # 确保不会覆盖 .original.db
        if (detdup.storage_type == 'memory') and detdup.feeded():
            detdup.load_features_from_db()

        self.items_model.core = detdup

        return detdup

    def extract(self):
        self.items_model.pull_data()

        """ 重新生成请全部删除 model.db 和 features.db 文件 """
        cprint("[建立 self.items_model 索引] ...", "blue")
        core = self.new_detdup_core()

        tmp_items = []
        def write(tmp_items):
            core.feed_items(tmp_items)
            return []

        for item_id1, item1 in self.items_model.iteritems():
            tmp_items.append(item1)
            if len(tmp_items) >= 10000:
                tmp_items = write(tmp_items)
        tmp_items = write(tmp_items)

    def train(self):
        core = self.new_detdup_core()

        def delete_item_ids(table, item_ids_1):
            step = 100
            for i1 in xrange(0, len(item_ids_1), step):
                table.delete().where(table.item_id << item_ids_1[i1:i1+step]).execute()

        pickle_filename = os.path.join(self.cache_dir, "detdup.cPickle")
        def load_result_func():
            core = self.new_detdup_core('memory')

            for feature1 in core.features:
                table = feature1.features_tree

                # 1. 先排除一定是不重复的
                candidate_list, uniq_list = feature1.divided_into_two_parts()

                delete_item_ids(table, uniq_list)

                # 2. 删除内容空白的条目
                table.delete().where(table.uniq_chars__len == 0).execute()

                core.candidate_dup_count = table.select().count()

                # 3. 正式排重
                for item1 in process_notifier(feature1.features_tree.select()):
                    dup_ids = core.detect_duplicated_items_verbose(item1.item_id, verbose=True)
                    delete_item_ids(table, dup_ids)

            return core.result
        result = cpickle_cache(pickle_filename, load_result_func)
        json.dump(result.result_json(), open(self.result_json, 'wb'))

    # def data_check(self):
        """ 验证正确率，随机找个重复的，遍历全库比对。 """
        """
        from random import randrange
        from etl_utils import String
        cases_count = 10

        recall_program_count = 0
        recall_real_count    = float(cases_count)

        for idx in xrange(cases_count):
            result = cpickle_cache(self.result_cPickle, lambda : True)
            core = self.new_detdup_core('memory')

            total_count = len(result.result)
            if not total_count:
                print 'NO DUPLICATION FOUND!'
                return
            program_similar_ids = result.result[randrange(total_count)]

            # 随机抽取的一个item
            current_item = self.items_model[program_similar_ids[0]]

            print "Begin to find %s's similar item_ids" % current_item.item_id
            real_similar_ids    = set([current_item.item_id])
            program_similar_ids = set(program_similar_ids)

            table = core.select_feature(current_item).features_tree
            basic_query = table.item_id != str(current_item.item_id)
            for column1 in self.query_check_columns:
                basic_query = basic_query & (getattr(table, column1) == getattr(current_item, column1))
            scope = table.select().where(basic_query) #.dicts()

            for i1 in process_notifier(scope):
                rate1 = String.calculate_text_similarity(current_item.item_content, self.items_model[i1.item_id].item_content)['similarity_rate']
                if rate1 > core.similarity_rate:
                    real_similar_ids.add(i1.item_id)
            print "real_similar_ids   :", sorted([str(i1) for i1 in real_similar_ids])
            print "program_similar_ids:", sorted([str(i1) for i1 in program_similar_ids])
            print
            if real_similar_ids == program_similar_ids:
                recall_program_count += 1
        print "recall :", recall_program_count / recall_real_count
        """
