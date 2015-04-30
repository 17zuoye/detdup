DetDup
======================
[![Build Status](https://img.shields.io/travis/17zuoye/detdup/master.svg?style=flat)](https://travis-ci.org/17zuoye/detdup)
[![Coverage Status](https://coveralls.io/repos/17zuoye/detdup/badge.svg)](https://coveralls.io/r/17zuoye/detdup)
[![Health](https://landscape.io/github/17zuoye/detdup/master/landscape.svg?style=flat)](https://landscape.io/github/17zuoye/detdup/master)
[![Download](https://img.shields.io/pypi/dm/detdup.svg?style=flat)](https://pypi.python.org/pypi/detdup)
[![License](https://img.shields.io/pypi/l/detdup.svg?style=flat)](https://pypi.python.org/pypi/detdup)

Detect duplicated items. 内容排重框架。

Usage
----------------------
见 USAGE.markdown

演讲稿
-------------
https://speakerdeck.com/mvj3/detdup

内容排重功能列表
----------------------
1. 返回 重复题目列表。
2. 发送题目ID，服务器端载入对应题库到内存中，查找和该项重复的条目，并返回题目ID列表。

常见内容重复特征
----------------------
1. [长度] 基本相似或相等, 两者长度的平方根相差不超过1。
2. [重复] 在任意位置, 多个逗号, 空格, s字符等。
3. [同义] 全角半角编码。分隔符号不同。am, 'm。
4. [顺序] 内部句子位子换了，比如从连线题里抽取的数据

导致不能使用基于分词的倒排索引。

召回率 和 正确率
----------------------
召回率: 如果特征抽取不是太准确的话，会导致有些groups漏了一两个。
正确率: 几乎100%的，因为是按原文本相似度算的。

DetDup 和 simhash, shingling 的关系。
----------------------
1. 其中 1 和 2 的功能 类似与simhash里 把文本变短为01序列的局部敏感hash 以及分块快速检索比较。
   simhash不利于 题库排重的原因见 #参考文献# , 这边几十个字符占很大比例, simhash适合于大网页的排重,
   而且simhash调hash参数应该比较繁琐和难以解释。
2. 3 类似于 shingling, 区别是 shingling 用的是分词, 这边直接比较全部字符。
   以兼容类似 `_range` 和 `orange` 的比较。

文本相似度定义
----------------------
把两段文本共同的字母都取出来 除以 两者文本的总长度得出的比率。比如 of 和 off 的文本相似度为 4 / 5 = 80%

参考文献
-----------------------
[海量数据相似度计算之simhash和海明距离](http://www.lanceyan.com/tech/arch/simhash_hamming_distance_similarity.html)

```txt
2、通过大量测试，simhash用于比较大文本，比如500字以上效果都还蛮好，距离小于3的基本都是相似，误判率也比较低。但是如果我们处理的是微博信息，最多也就140个字，使用simhash的效果并不那么理想。看如下图，在距离为3时是一个比较折中的点，在距离为10时效果已经很差了，不过我们测试短文本很多看起来相似的距离确实为10。如果使用距离为3，短文本大量重复信息不会被过滤，如果使用距离为10，长文本的错误率也非常高，如何解决？
```
