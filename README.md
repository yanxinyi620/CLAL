# CLAL

Contrast learning and active learning.

## Dataset

* 微波链路数据介绍
  [microwave-link](http://www.microwave-link.com/)

* 参考论文
  [Proactive Microwave Link Anomaly Detection in Cellular Data Networks](https://www.cse.cuhk.edu.hk/~pclee/www/pubs/comnet19.pdf)

* 数据集
  [下载](http://adslab.cse.cuhk.edu.hk/software/pmads)

## Contrast learning

* 多元时间序列对比学习：[usrlts](https://github.com/White-Link/UnsupervisedScalableRepresentationLearningTimeSeries)
  * paper: Unsupervised Scalable Representation Learning for Multivariate Time Series (Jean-Yves Franceschi, Aymeric Dieuleveut and Martin Jaggi)
  * Copyright: White-Link(Jean-Yves Franceschi)
  * [Apache-2.0 License](https://github.com/White-Link/UnsupervisedScalableRepresentationLearningTimeSeries/blob/master/LICENSE)

* node2vec: [node2vec](https://github.com/aditya-grover/node2vec)
  * paper: node2vec: Scalable Feature Learning for Networks. Aditya Grover and Jure Leskovec. Knowledge Discovery and Data Mining, 2016.
  * Copyright (c) 2016 Aditya Grover
  * [MIT License](https://github.com/aditya-grover/node2vec/blob/master/LICENSE.md)

* cosine similarity
  * 计算微波链路数据节点的空间距离

* loss
  * Loss1：[参考文献](https://arxiv.org/abs/1901.10738)
  * InfoNCE：[参考文献](https://arxiv.org/pdf/1807.03748v2.pdf)

* 正负样本抽样方式：
  * USRLTS：选择当前样本某一时间片段作为ref，当前样本另一片段作为pos，其他随机10个样本各取1个片段作为10个neg。
  * 抽样方式1：选择当前样本作为ref，当前样本将部分数据去掉（即含部分缺失值）作为pos，其他随机10个样本作为10个neg。
  * 抽样方式2：时间信息使用USRLTS或抽样方式1，空间信息通过计算余弦相似性，选择最相近的1个正样本，最远的10个负样本。

## Active learning

* 流程
  * 1. 使用对比学习 encoder 得到 embedding 结果
  * 2. 使用 KMeans 聚类算法将所有样本分为 10 类
  * 3. 将聚类的得到 10 个类别，分别随机选择 5 个样本进行标注
  * 4. 使用上一步得到的 50 个样本作为训练集，使用 RF 算法得到分类预测结果
  * 5. 再次使用对比学习 encoder 得到新的 embedding 结果（利用分类及预测结果更新正负样本抽样方式）
  * 6. 将对比学习中 batchsize=500 中选择 loss 最大的 10 个样本进行标注
  * 7. 将所有标注样本作为训练集，重新使用 RF 得到分类预测结果
  * 重复上述 5~7 的过程，直到总的训练集达到 3000 停止。

* los计算及正负样本抽样：
  * 抽样方式(3ref + 3pos + 30neg)
    * 时间序列（正样本）：一共3个pos样本。其中对比学习中抽样方式2获得1个pos + 已有训练集中随机选择1个真实类型和当前样本预测类型一致的样本作为1个pos + 测试集中随机选择1个预测类型和当前样本预测类型一致的样本作为1个pos。
    * 时间序列（负样本）: 三种来源分别各取10条，一共30个neg。
    * 空间信息（正样本）：一共3个pos样本。其中对比学习中抽样方式2获得1个pos + 已有训练集中随机选择1个真实类型和当前样本预测类型一致的样本作为1个pos + 测试集中随机选择1个预测类型和当前样本预测类型一致的样本作为1个pos。
    * 空间信息（负样本）: 三种来源分别各取10条，一共30个neg。
  * loss 计算
    * 将不同来源的 loss 累计，并保存下来，选择每轮 500 个样本中 loss 最大的 50个样本进行标注。

## Result

* Contrast learning
  * $prauc \approx 0.935$
    `对比学习(space + time) 结合 RF 分类`
  * $prauc \approx 0.963$
    `19 个统计特征 + X(n2v) 结合 RF 分类（统计特性为人工提取，等同时间信息，X(n2v)为空间信息，均不经过对比学习过程）`
  * 总结
    * 对比学习为非监督学习，可以达到与人工提取统计特征相似的分类效果（分类过程需要标注样本）。在实际业务场景中，可以减少人工特征提取过程。
    * 在对比学习中仅使用空间信息或时间信息，仅使用19个统计特征或X(n2v)信息，或者直接使用其他时间序列的分类算法，prauc 仅为 0.6 ~ 0.8.

* Active learning
  * $prauc \approx 0.893$
    `从对比学习(space + time) 中应用主动学习流程选择 3000 样本进行标注`
  * $prauc \approx 0.923$
    `从19 个统计特征 + X(n2v) 中应用主动学习流程选择 3000 样本进行标注`
  * $prauc \approx 0.738$
    `从对比学习(space + time) 中随机选择 3000 样本进行标注`
  * $prauc \approx 0.821$
    `从19 个统计特征 + X(n2v) 中随机选择 3000 样本进行标注`
  * 总结
    * 完整数据集为4w+，其中train集2w+，test集2w+。应用主动学习可以在标注样本达到 3000 时可以获得近似于2w+样本的分类预测效果。
