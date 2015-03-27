# -*- coding: utf-8 -*-

from etl_utils import StringUtils, UnicodeUtils, cached_property
from bson.objectid import ObjectId
import os, math, json
from .fake_item_ids import FakeItemIds

class DetDupDataModel(object):
    """
    Usage:
    1. implement #init__load_data
    2. DetDupDataModel.feed_data, #[]
    """

    core                = None
    fake_item_ids_store = None

    @classmethod
    def bind_a_fake_item_ids_store(cls):
        FakeItemIds(cls)

    def check_valid_id_in_record(self, record): return u'_id' in record

    def init__before(self, record):
        # ensure_an_item_id_or_fake
        if not self.check_valid_id_in_record(record):
            self.item_id = unicode(ObjectId())
            self.fake_item_ids_store.insert(self.item_id, self.dump_record(record))

    def init__after(self, record):
        # 会把全角都转换为半角
        self.item_content = UnicodeUtils.stringQ2B(self.item_content)

        # common extract data part
        info1                  = StringUtils.frequence_chars_info(self.item_content, lambda len1 : len1 * 0.75)
        self.uniq_chars__len   = info1['uniq_chars__len']
        self.sorted_freq_chars = info1['sorted_freq_chars']
        self.sqrt_chars__len   = int(round(math.sqrt(len(self.item_content))))

    def inspect(self):
        info = []
        for col1 in type(self).attr_columns():
            if not hasattr(self, col1): continue # 是别的feature才有的
            val1 = getattr(self, col1)
            if isinstance(val1, unicode): val1 = val1.encode("UTF-8")
            info.append(' '.join([col1.rjust(24, ' '), ":", str(val1), ';']))
            if type(val1) in [str, unicode]:
                info.append(' '.join(["".rjust(26, ' '), str(len(val1))]))
        info.append("\n")
        print "\n".join(info)
        return info

    @classmethod
    def attr_columns(cls):
        """ 枚举 ETL 出来的所有字段 """

        _attr_columns = []
        for feature1 in cls.core.features:
            _attr_columns.extend(feature1.table_columns())
        _attr_columns = list(set(_attr_columns))
        _attr_columns.remove('item_id')
        _attr_columns.insert(0, 'item_id')
        _attr_columns.append('item_content')
        return _attr_columns
