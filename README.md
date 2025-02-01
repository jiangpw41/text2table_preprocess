# 概述
这个项目服务于TKGT，对主要的text2table数据集进行预处理形成统一的格式用于TKGT

# 数据集列表
目前，该项目涵盖下面数据集
- CPL：TKGT中提出的数据集
- e2e
- rotowire
- LiveSum

为了避免体系臃肿，仅在方法层面进行代码复用，为每个raw数据集创建一套预处理方案（preprocess文件夹下）。
此外，分raw/pair_data/data三层，分别为原始数据集、数据对、适用于下游任务的pickle数据

# 输出格式
对每个数据集，输出一对列表，分别为text和table
- text: 每行一个文档
- table：每个文档一个三元组/二元组集合，大多为三元组，二元组仅适用于单entity数据集如e2e