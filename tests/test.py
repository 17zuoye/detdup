# -*- coding: utf-8 -*-

import os, time, sys
os.system("rm -rf tests/output/*")

current_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, current_dir)

from tests.models import *
from tests.api import *

import unittest
class TestDetDup(unittest.TestCase):
    def test_detdup(self):
        # 1. 冷启动全流程
        ddt.extract()
        ddt.train()

        # 2. 热启动全流程
        print "\n"*80
        similar_ids = [i1.item_id for i1 in CleanModel.values() if i1.item_content == 'Python']
        self.assertTrue(dda.is_all_duplicated(similar_ids))
        print "\n"*80

        temp_record = generate_record("CoffeeScript")
        target_id   = [i1.item_id for i1 in CleanModel.values() if i1.item_content == 'CoffeeScript'][0]
        result      = dda.detect_duplicated_items(temp_record)
        self.assertTrue(str(target_id) in result, "Found duplicated CoffeeScript")
        assert len(result), 2

        assert dda.detect_duplicated_items(temp_record), 2 # 再排重一次
        dup_storage = CleanModel.fake_item_ids_store.storage
        self.assertEqual(dup_storage.select().count(), 2, "Find twice")
        self.assertEqual(dup_storage.select().where(dup_storage.is_deleted==True).count(), 1, "Find is_deleted only one, the last one will be deleted at the next time")

if __name__ == '__main__': unittest.main()
#import pdb; pdb.set_trace()
