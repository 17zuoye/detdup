Requirements
----------------------
1. Install required python library from requirements.txt
2. storage: 1. sqlite library,  2. cPickle, 3. redis(optional)

项目架构流程
----------------------
具体代码流程见 services/task.py

### extract

* 为要处理的数据 继承DetDupDataModel类, 提供 多种数据特征 和 清洗后的文本内容, 具体见文档注释。
* 并导入特征数据库。

### train

* 去除特征数据库里没有同类的
* 检测重复条目
* 合并并打印结果列表
* 检测召回率

Usage
----------------------
1. 接口服务见 detdup/services
2. 示例见     tests

文本相似度 性能数据
-----------------------
1. 文本相似度在 0.95时，排重几乎全是正确的, 重复元素有3199个, 组有1463个。
2. 文本相似度在 0.90时，排重一点点错误，重复元素有3297个, 组有1507个。

相当于重复元素多了98个, 重复组多了44个, 重复[组]90-95之间多了 44 / 1463.0 = 3.0%, 重复元素90-100%元素约为 7.4%。
在文本相似度为90%时，误判率大概在 重复元素 19 / 3297.0 = 0.57%, 重复组在 9 / 1507.0 = 0.59%;

性能和总数以及重复元素总量成线性增长关系。

90万数据
data_extract 13分钟, 8核
data_index 11分钟, 1核
data_index_remove_unneeded 1分钟, 1核
data_detdup 5.5分钟, 8核

160万数据
data_extract 26-32分钟, 8核，比上面慢的原因是90万数据是用SSD读的。
data_index 25分钟, 1核
data_index_remove_unneeded 1分钟, 1核
data_detdup 5.75分钟, 8核

读取数据 编程接口
-----------------------
```txt
>>> import json
>>> data = json.load(open("detdup.json", "rb"))
>>> data.result[0:3]
[[a3c67f3da591b518cb535bd7, 76d6aeed4b31b569310db1a6], [e05f6e6da5aff02a81411342, 75a8e395b87ad910e0cef062],
[75e7db33f06264d80c77b669, 99b6ef2b6a32d2f8317763fc, 770e993816f258edc7f3fe6b],]
```
