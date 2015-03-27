# -*- coding: utf-8 -*-

from etl_utils import cpickle_cache, process_notifier
import os
import sqlitebck
import sqlite3
import shutil
from peewee import fn as peewee_fn

class DefaultFeatures(object):
    """
    Default processing features.

    Notice:
    1. process only one current_item at a time.

    Inteface:
    1. post_init: add your self.custom_features and self.typename

    Regenerate cache:
    1. delete *.db and *.idnamecache

    """

    def __init__(self):
        self.link_to_detdup = None

        self.current_item = None
        self.typename     = 'default'

        self.default_features = {
                "uniq_chars__len"   : int,
                "sqrt_chars__len"   : int,
                "sorted_freq_chars" : str,
# TODO sorted_mid_freq_chars
            }
        self.custom_features = dict()
        self.features_tree = None
        self.uniq_chars__len = 3

        # private
        self.columns = []

        self.post_init()

    def post_init(self):
        """
        e.g.

        self.typename      = 'choices'
        self.custom_features = {
                'answers_length': int,
                'sorted_answers_hash': str
                }
        """
        pass

    def table_columns(self):
        if self.columns: return self.columns
        self.columns = self.features_tree._meta.get_field_names()
        self.columns.remove('id')
        return self.columns

    def insert_item(self, q1):
        self.current_item = q1
        return self

    def feed_item(self, item1=None):
        self.current_item = item1 or self.current_item
        # query item_content through self.features_tree is slow, so add build a hash index directly.
        data_json = {k1: getattr(self.current_item, k1) for k1 in self.table_columns()}
        self.features_tree.create(**data_json)

    def delete_item_ids(self, oids):
        self.features_tree.delete().where(self.features_tree.item_id << oids).execute()

    def fetch_matched_item_ids(self):
        """
        如果不是一个一个从DefaultFeatures遍历查，然后筛选，那么就浪费了每次SQL查询的时间。

        因为有范围查找的原因，所以不能直接在特征数据库GroupBy基础上直接再排重，还是得一个一个排重。
        """
        item1 = self.current_item

        sqrt_chars__len_range_query_left  = self.features_tree.sqrt_chars__len >= (item1.sqrt_chars__len - 1)
        sqrt_chars__len_range_query_right = self.features_tree.sqrt_chars__len <= (item1.sqrt_chars__len + 1)

        # uniq_chars__len range query
        # NOTE 不用对数 是因为已经唯一过了。
        uniq_chars__len_range_query_left  = self.features_tree.uniq_chars__len >= (item1.uniq_chars__len - self.uniq_chars__len)
        uniq_chars__len_range_query_right = self.features_tree.uniq_chars__len <= (item1.uniq_chars__len + self.uniq_chars__len)

        # sorted_freq_chars equal query
        sorted_freq_chars = self.features_tree.sorted_freq_chars == item1.sorted_freq_chars

        default_query = uniq_chars__len_range_query_left & uniq_chars__len_range_query_right & sorted_freq_chars

        # extend query
        for feature_k1 in self.custom_features:
            # support custom int attribute query
            if isinstance(self.custom_features[feature_k1], int):
                feature_v1 = self.custom_features[feature_k1]
                delta_query1 = (getattr(self.features_tree, feature_k1) >= (getattr(item1, feature_k1) - feature_v1))
                delta_query2 = (getattr(self.features_tree, feature_k1) <= (getattr(item1, feature_k1) + feature_v1))
                delta_query  = delta_query1 & delta_query2
            else: # str
                delta_query = (getattr(self.features_tree, feature_k1) == getattr(item1, feature_k1))
            default_query = default_query & delta_query

        ffs = self.features_tree.select().where(default_query)

        return [f1.item_id for f1 in ffs]

    def build_features_tree(self):
        from peewee import SqliteDatabase, Model, IntegerField, CharField, BooleanField

        # built or connect database
        sqlite_path = {
                "memory" : ":memory:",
                "disk"   : self.sqlite3db_path(),
        }[self.link_to_detdup.storage_type]
        sqlite_database = SqliteDatabase(sqlite_path, check_same_thread=False)

        class BaseFeaturesTree(Model):
            uniq_chars__len     = IntegerField(default=0)
            sqrt_chars__len     = IntegerField(default=0)
            sorted_freq_chars   = CharField()
# TODO support item_id as int or str type
            item_id             = CharField()

            class Meta:
                database = sqlite_database
        self.features_tree = BaseFeaturesTree

        tablename = "_".join(self.custom_features).capitalize() or "DefaultFeaturesTree"

        # If customize more features
        if self.custom_features:
            self.features_tree = type(tablename, (BaseFeaturesTree,), dict())
            for feature_k1 in self.custom_features:
                # http://stackoverflow.com/questions/22358489/dynamically-define-fields-in-a-peewee-model
                feature_v1 = self.custom_features[feature_k1]
                # Compact with (int) instance
                if type(feature_v1) is int: feature_v1 = int
                field1 = {int: IntegerField, str: CharField}[feature_v1]()
                field1.add_to_class(self.features_tree, feature_k1)

        self.features_tree._meta.db_table = tablename

        # create table and indexes
        if not self.features_tree.table_exists():
            self.features_tree.create_table()
            sqlite_database.create_index(self.features_tree, "item_id".split(" "))

# TODO 让大str在前面，加快索引搜索速度
            index_columns = self.default_features.keys() + self.custom_features.keys()
            sqlite_database.create_index(self.features_tree, index_columns)

        print "[build_features_tree]", self.features_tree, "self.default_features :", self.default_features, "self.custom_features :", self.custom_features
        print

    def dump_features_tree(self): self.copy_features_tree('memory_to_file')
    def load_features_tree(self): self.copy_features_tree('file_to_memory')
    def copy_features_tree(self, schema='memory_to_file'):
# TODO reduce file disk size
        if not self.link_to_detdup: return False
        # 1. copy database
        backup_conn    = sqlite3.connect(self.sqlite3db_path())
        current_conn   = self.features_tree._meta.database.get_conn()
        if schema == 'memory_to_file': _from = current_conn; _to = backup_conn
        if schema == 'file_to_memory': _from = backup_conn ; _to = current_conn
        if not (_from or _to): raise Exception("schema don't match!")
        sqlitebck.copy(_from, _to)
        backup_conn.close()

        print "loaded %s by %s" % (self.sqlite3db_path(), schema)

    def sqlite3db_path(self): return os.path.join(self.link_to_detdup.features_dir, self.typename + '.db')

    def divided_into_two_parts(self):
        """ 重复毕竟是小部分, 所以_set只存可能是重复的ID列表 """
        candidate_set = set([])
        uniq_set      = set([])

        feature1_dict = dict(self.default_features.items() + self.custom_features.items())

        # group by 不支持范围，比如整数范围查询
        group_by_columns = [f1 for f1 in feature1_dict if feature1_dict[f1] == str]

        if group_by_columns:
            table = self.features_tree
            group_by_query = [getattr(table, f1) for f1 in group_by_columns]
            group_concat   = [peewee_fn.group_concat(table.item_id).alias('item_ids')]

            group_by_sql   = table.select(*(group_concat)).group_by(*group_by_query)
            for i1 in process_notifier(group_by_sql):
                items_len = len(i1.item_ids)
                if items_len > 24:
                    candidate_set = candidate_set | set(i1.item_ids.split(","))
                elif items_len == 24: # 只有一个object_id
                    uniq_set.add(i1.item_ids)
                else:
                    raise Exception("item_ids is invalid")
        else:
            print feature1, "has none features"

        return (list(candidate_set), list(uniq_set))
