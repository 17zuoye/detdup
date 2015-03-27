标题 100 pt
次标题 80 pt
脚注 36 pt
列表 50 pt
列表缩进 15 pt
列表大字 30, 18

# DetDup
Detect duplicated items.

重复示意图

# Agenda
1. "重复内容"的定义
2. 两两比较复杂度
3. 相似性算法挑选
4. 软件工程架构和优化

# "重复内容"的定义
1. [长度] 基本相似或相等, 两者长度的平方根相差不超过1。
2. [重复] 在任意位置, 多个逗号, 空格, s字符等。
3. [同义] 全角半角编码。分隔符号不同。am, 'm。
4. [顺序] 内部句子位子换了，比如从连线题里抽取的数据。

原始字符 VS 分词: 文本越小，分词效果的差异越大。

# 相似性算法挑选
AGoodnightGoodmorning勾选
AGoodnightGoodmorning圈选

分词 10/12 # => 83.33%
unicode   44/46 # => 95.65%

# "两两比较"时间复杂度
一个朴素的问题

n log n

# simhash
选择的特征都很大
TODO


shingle(瓦), 4-grams
{ (a,rose,is,a), (rose,is,a,rose), (is,a,rose,is), (a,rose,is,a), (rose,is,a,rose) } = { (a,rose,is,a), (rose,is,a,rose), (is,a,rose,is) }


# 软件架构

  Task        API

              Core

 ModelCache   Features-Trees


Task = [`extract`, `train`]
API  = [`is_all_duplicated`, `process_record`, `query_item_features`, `detect_duplicated_items`]
Core = 管理Features-Trees

# 配置特征
通用
`uniq_chars__len
sqrt_chars__len
sorted_freq_chars`

业务
`options_uniq_chars__len
options_sorted_freq_chars
options__len
...`

from detdup.features.default import DefaultFeatures
class PLFeature(DefaultFeatures):
    """ programming language """
    def post_init(self):
        # 在特征数据库级别划分
        self.typename      = 'pl'

        self.custom_features = {
            'desc' : str,
          }

# 数据准备
操作 extract => build features-trees and model-cache
存储 cPickle      sqlite and ModelCache

# 预先排重
1. 选出需要排重的item-ids
`SELECT
        t1."sorted_freq_chars", group_concat(t1."item_id") AS item_ids
 FROM
        "DefaultFeaturesTree" AS t1
 GROUP BY
        t1."sorted_freq_chars`

2. 给每一个item划分排重域
`SELECT
        t1."id", t1."uniq_chars__len", t1."sqrt_chars__len", t1."sorted_freq_chars", t1."item_id", t1."desc"
 FROM
        "Desc" AS t1
 WHERE
       (((((t1."uniq_chars__len" >= 3)) AND (t1."uniq_chars__len" <= 9)) AND (t1."sorted_freq_chars" = 'hn')) AND (t1."desc" = 'programming language'))

3. 排重缓存。

item1 => [item1, item2, item3]
item2 => 缓存命中(ItemsGroupAndIndexes)

# 实时排重

放入排重特征库中比对
1. 临时(FakeItemIds)
2. 永久

# 软件工程优化
1. 多进程数据清洗
2. sqlitebck 内存磁盘相互拷贝
3. 动态定义特征数据库表

# 性能数据
-----------------------
1. 文本相似度在 0.95时，排重几乎全是正确的, 重复元素有3199个, 组有1463个。
2. 文本相似度在 0.90时，排重一点点错误，重复元素有3297个, 组有1507个。

相当于重复元素多了98个, 重复组多了44个, 重复[组]90-95之间多了 44 / 1463.0 = 3.0%, 重复元素90-100%元素约为 7.4%。
在文本相似度为90%时，误判率大概在 重复元素 19 / 3297.0 = 0.57%, 重复组在 9 / 1507.0 = 0.59%;

性能和总数以及重复元素总量成线性增长关系。

# 其他开源项目

fill_broken_words model_cache phrase_recognizer tfidf article_segment region_unit_recognizer compare_word etl_utils split_block



http://weibo.com/1665335994/Alp0uAOL9?type=comment&sudaref=www.aszxqw.com
http://dl.acm.org/citation.cfm?id=509965
http://www.lanceyan.com/tech/arch/simhash_hamming_distance_similarity.html
http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.78.7794&rep=rep1&type=pdf
simhash与Google的网页去重 http://leoncom.org/?p=650607 对比较域进行优化，没看懂。
http://www.aszxqw.com/work/2014/01/30/simhash-shi-xian-xiang-jie.html simhash算法原理及实现
