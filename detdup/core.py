# -*- coding: utf-8 -*-

from .utils import *

from etl_utils import String, Speed, BufferLogger, ItemsGroupAndIndexes

# TODO 检测 item.typename() 存在

from .features import DefaultFeatures

class DetDupCore(object):
    """
    Detect duplicated items, use decision tree.

    Usage:
    -----------
    """

    similarity_rate = 0.90

    def __init__(self, features_dir, detdup_data_model):
        self.features_dir          = features_dir

        self.model                 = detdup_data_model

        self.features              = [DefaultFeatures()]
        self.features_map          = dict()

        self.storage_type          = ['memory', 'disk'][0]

        self.is_logger             = True
        self.is_inspect_detail     = False
        self.buffer_logger         = BufferLogger(os.path.join(self.features_dir, 'process.log'))

        self.result                = ItemsGroupAndIndexes()
        self.count                 = 0

        self.candidate_dup_count   = None

    def select_feature(self, item1):
        f1 = item1.typename
        if not isinstance(f1, str) and not isinstance(f1, unicode): f1 = f1()
        return self.features_map[f1].insert_item(item1)

    def feeded(self):
        for feature1 in self.features:
            # 这个Feature是否有效
            if not feature1.link_to_detdup:
                continue
            # 之前已经导出数据库啦?!
            if os.path.exists(feature1.sqlite3db_path()):
                return True
        return False

    def load_features_from_db(self):
        for feature1 in self.features: feature1.load_features_tree()

    def dump_features_from_memory(self):
        for feature1 in self.features: feature1.dump_features_tree()

    def feed_items(self, obj, persist=True):
        """ Feed items to features """
        # 1. insert it into memory
        [self.select_feature(item1).feed_item() for item1 in process_notifier(obj)]
        # 2. backup into files fully!
        if persist:
            self.dump_features_from_memory()
        return self

    def plug_features(self, features1):
        """
        1. Plug features, and bind typename to classify items
        2. init features tree, memory or disk
        """
        if not isinstance(features1, list): features1 = [features1]
        self.features.extend(features1)
        for f1 in self.features:
            f1.link_to_detdup = self
            f1.build_features_tree()

        for f1 in self.features:
            self.features_map[f1.typename] = f1
        return self

    time_sql = 0
    time_calculate_text_similarity = 0
    time_fetch_content = 0

    def detect_duplicated_items(self, item1):
        feature1 = self.select_feature(item1)
        speed   = Speed()

        t1 = datetime.now()
        item_ids = feature1.fetch_matched_item_ids()
        t2 = datetime.now(); self.time_sql += (t2 - t1).total_seconds();

        # 4. 看看题目相似度
        # 相似度得大于 95%
        new_ids = list()
        for item_id1 in item_ids:
            # 2. 排除自己
            if item_id1 == unicode(item1.item_id): continue

            if item_id1 not in self.model:
                # 删除不一致数据, 以在self.model里为准
                feature1.delete_item_ids([item_id1])
                continue

            t11 = datetime.now()
            content1 = self.model[item_id1].item_content
            t12 = datetime.now(); self.time_fetch_content += (t12 - t11).total_seconds();

            t11 = datetime.now()
            res1 = String.calculate_text_similarity(item1.item_content,
                            content1,
                            inspect=True,
                            skip_special_chars=True,
                            similar_rate_baseline=self.similarity_rate)
            t12 = datetime.now(); self.time_calculate_text_similarity += (t12 - t11).total_seconds();

            if res1['similarity_rate'] > self.similarity_rate:
                new_ids.append(item_id1)
                self.buffer_logger.append(res1['info'])
                self.buffer_logger.inspect()
        print "字符串相似度 [前]", (len(item_ids) - 1), "个，[后]", len(new_ids), "个"

        item_ids = new_ids

        # 如果要排除已处理过为排重的
        speed.tick().inspect()

        print "self.time_sql", self.time_sql
        print "self.time_calculate_text_similarity", self.time_calculate_text_similarity
        print "self.time_fetch_content", self.time_fetch_content

        return item_ids

    def detect_duplicated_items_verbose(self, item_id1, verbose=False):
        self.count += 1
        print "\n"*5, "从", self.candidate_dup_count, "个候选题目中 排重第", self.count, "个题目。", item_id1

        # 如果结果已经计算出来
        if self.result.exists(item_id1):
            return self.result.find(item_id1)

        self.buffer_logger.append("-"*80)
        self.buffer_logger.append("要处理的记录")

        item1 = self.model[item_id1]
        if verbose: item1.inspect()

        self.buffer_logger.append("")
        item_ids = self.detect_duplicated_items(item1)
        self.buffer_logger.append("疑似和", item1.item_id, "重复的条目有", len(item_ids), "个")
        for item_id1 in item_ids:
            if verbose: self.model[item_id1].inspect()
        self.buffer_logger.append("")

        # 输出日志
        if (len(item_ids) > 0) and self.is_logger:
            self.buffer_logger.inspect()
        else:
            self.buffer_logger.clear()

        item_ids.append(unicode(item1.item_id))

        # 有重复结果，就存储一下
        if len(item_ids) > 1:
            self.result.add([i1 for i1 in item_ids])

        return item_ids
