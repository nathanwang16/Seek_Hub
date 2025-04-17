# 大家好！我们的项目即将重新启动，并且新加入了一位成员。这是我们的Github空间，我们以后的数据和成果要同步到这里。
# 我需要先说明一下整个项目的规划：
  我们的项目最终的目的是实现接近人类翻译质量的、成本接近于0的长文本翻译。我们项目分为以下几部分：
    1.第一阶段是四轮微调，下面会提到详细的计划；
    2.完成微调之后，我们需要评估翻译质量，这包括专家评审以及引入相关评估的方法。下面会提到关于翻译质量评估的内容；
    3.评估完翻译质量后有两种可能性：1.实现了我们最初的目标 2.翻译质量差强人意
        对于第一种可能性：我们立刻准备publication和商业化的工作，不再需要模型架构的改变，可能性不大；
        对于第二种可能性：先发文章，再准备模型底层架构的工作，比如使用稀疏注意力机制，使它更适合长文本处理
        但是无论怎么样，我向大家保证人人都能有一篇publication，哪怕我们最终失败了大家也有收获
    4.还有一种可能性：资金不够，训练成本上百万，尤其是后期改变模型架构后，需要重新训练的情况
        这时需要成立公司，分配股权，然后找投资人，再扩招团队
          如果没有投资人，项目失败；
          概率极小的情况下有投资人，就背水一战。

    我们前期的难度较低，有资金支持，微调和发表文章的工作很容易完成
    但是希望大家做好心理准备，我们最终的目的是商业化，要把这个软件卖出去，无论过程如何，难度极大
    希望大家共勉！
    

# 以下是微调相关的教程和资源：

【DeepSeek 671B微调指南】
https://company.hpc-ai.com/blog/shocking-release-deepseek-671b-fine-tuning-guide-revealed-unlock-the-upgraded-deepseek-suite-with-one-click-ai-players-ecstatic

【SiliconFlow Platform】
https://docs.siliconflow.cn/cn/userguide/introduction

【【DeepSeek+LoRA+FastAPI】开发人员如何微调大模型并暴露接口给后端调用】 
https://www.bilibili.com/video/BV1R6P7eVEtd/?share_source=copy_web&vd_source=1c639bb59610c225121de6410fe19657

【Fine-Tuning AI Large Language Models (LLM) for Precise Corporate Translations: A BLEU Score Study】
https://medium.com/@haberlah/fine-tuning-ai-large-language-models-llm-for-precise-corporate-translations-a-bleu-score-study-0fc3bf645a96

LLM长上下文的问题https://www.linsight.cn/c4da56c0.html
解决方案基本上1.微调使用长文本2.改变模型架构（稀疏注意力机制）

# 以下是第一轮微调前相关准备：

1.训练分4轮，每次训练的文本长度由8k-64k-128k-128k
  这是由于普通大模型的注意力机制，导致它只能很好地处理千字规模以内的文本。我们的实验证明，用deepseek去翻译长文本时会出现内容缩减的情况
  后期当我们四轮训练结束后，可能需要改变模型底层架构，比如使用稀疏注意力机制
  
2.我们使用云端部署，平台叫做Lambda Labs，训练时需租借24块H100芯片组成的算力集群，费用在每小时24刀左右
  https://lambda.ai/?srsltid=AfmBOoqx-rR0jXQmpLeQwfMNOADRpBthgGWcvQTDTHsyDHaCQZRqHra-

3.微调前的准备：
  1.准备数据集
    数据集的种类以文科书籍为主，包括所有的专业教材、小说、科普书以及无法分类的书籍。目前训练的科目不包括数学和物理。数据集同时需要加入少量诗歌
    训练数据基本来源于Z-library。第一轮的数据量在100本书左右。
    数据集的内容：
      第一轮的数据集暂定是各人文领域的基础教材30本+诗歌10本+小说30本+科普书30本
  2.编写爬虫程序去Zlib上大批量下载。
  如果遭到反爬导致下载失败，需要所有人一起去手动下载。到时候我会开通一个无限制下载的账号。
  3.统一数据格式，把不同类型的文件（pdf/txt/epub等）转化成统一的格式（txt）
  4.对翻译文本进行分段，每段长度8k字
  5.中英翻译配对，校对，再做成数据集的格式


# 翻译质量评估的任务：
在四轮微调结束之后，需要评估训练的成果，再决定是否涉及模型架构上的改变。
以下是两种思路，评估结果作为我们的背书，可以作为publication的一部分
1.专家评审
2.引入可量化的评估标准
  以下是几种可量化的评估标准：
    
