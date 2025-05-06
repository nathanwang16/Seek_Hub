# 项目说明
大家好！我们的项目即将重新启动，并且新加入了一位成员。这是我们的Github空间，我们以后的数据和成果要同步到这里。

### 我们的工作
我们致力于做出接近人类顶级翻译水平的，并且成本极低的翻译软件，实现AI在翻译领域取代人。我们细分的领域是多种语言翻译成中文的长文本翻译（英译中为主），目前为止市场上没有成熟的产品，因此这是一个蓝海。最终的目的是商业化，把这个产品卖给有翻译需求的机构或者个人，比如出版社、译者们以及一些高校。

我们也在考虑其他相关的项目，比如电影和漫画的汉化工作，这同样富有商业前景，并且实现的难度更低。但是由于翻译的工作最有意义，我们优先选择这个项目。

我们最终的营收由所有人平分，前期投入由创始人一人承担即可，但是欢迎大家对这个项目的投资！

### 我们的团队
创始人：赵奕鸣 UCSB物理专业大一 

王萧语Nathan UCLA 生物工程专业

邱烁Hank 香港


### 团队理念
解决问题，效率至上

### 整个项目的规划
我们项目分为以下几部分：

1.四轮微调，之后会提到详细的计划；
  
2.完成微调之后，我们需要评估翻译质量，这包括专家评审以及引入相关评估的方法。
    
3.评估完翻译质量后有两种可能性：
- 实现了我们最初的目标
  
  我们立刻准备publication和商业化的工作，不再需要模型架构的改变，可能性不大
- 翻译质量差强人意
  
    先发文章，再准备模型底层架构的工作

但是无论怎么样，我向大家保证人人都能有一篇publication，哪怕我们最终失败了大家也有收获
        
4.还有一种可能性：资金不够，训练成本上百万，尤其是后期改变模型架构后，需要重新训练的情况
    
这时需要成立公司，分配股权，然后找投资人，再扩招团队
- 如果没有投资人，项目失败；
- 概率极小的情况下有投资人，继续前进。

我们前期的难度较低，有资金支持，微调和发表文章的工作很容易完成

但是希望大家做好心理准备，我们最终的目的是商业化，要把这个软件卖出去，无论过程如何，难度极大

希望大家共勉！

### 相关论文
https://ghost.oxen.ai/no-hype-deepseek-r1-reading-list/

包含了很多经典文献，以及Deepseek的技术报告，每个人都需要过一遍

### 微调相关的教程和资源：

【DeepSeek 671B微调指南】
https://company.hpc-ai.com/blog/shocking-release-deepseek-671b-fine-tuning-guide-revealed-unlock-the-upgraded-deepseek-suite-with-one-click-ai-players-ecstatic

【SiliconFlow Platform】
https://docs.siliconflow.cn/cn/userguide/introduction

【【DeepSeek+LoRA+FastAPI】开发人员如何微调大模型并暴露接口给后端调用】 
https://www.bilibili.com/video/BV1R6P7eVEtd/?share_source=copy_web&vd_source=1c639bb59610c225121de6410fe19657

【Fine-Tuning AI Large Language Models (LLM) for Precise Corporate Translations: A BLEU Score Study】
https://medium.com/@haberlah/fine-tuning-ai-large-language-models-llm-for-precise-corporate-translations-a-bleu-score-study-0fc3bf645a96

LLM长上下文导致精度丢失的问题https://www.linsight.cn/c4da56c0.html

解决方案基本上就是：微调使用长文本+改变模型架构（稀疏注意力机制）

### 第一轮微调前相关准备

1.训练分4轮，每次训练的文本长度由8k-64k-128k-128k。这是由于普通大模型的注意力机制，导致它只能很好地处理千字规模以内的文本。我们的实验证明，用deepseek去翻译长文本时会出现内容缩减的情况。后期当我们四轮训练结束后，可能需要改变模型底层架构，比如使用稀疏注意力机制
  
2.我们使用云端部署，平台叫做Lambda Labs，训练时需租借24块H100芯片组成的算力集群，费用在每小时24刀左右
  https://lambda.ai/?srsltid=AfmBOoqx-rR0jXQmpLeQwfMNOADRpBthgGWcvQTDTHsyDHaCQZRqHra-

3.微调前的准备：

- 准备数据集。数据集的种类以文科书籍为主，包括所有的专业教材、小说、科普书以及无法分类的书籍。目前训练的科目不包括数学和物理。数据集同时需要加入少量诗歌。训练数据基本来源于Z-library。第一轮的数据量在100本书左右。第一轮的数据集暂定是各人文领域的基础教材30本+诗歌10本+小说30本+科普书30本
      
- 编写爬虫程序去Zlib上大批量下载。如果遭到反爬导致下载失败，需要所有人一起去手动下载。到时候我会开通一个无限制下载的账号。
  
- 统一数据格式，把不同类型的文件（pdf/txt/epub等）转化成统一的格式（txt）
  
- 对翻译文本进行分段，每段长度8k字
  
- 中英翻译配对，校对，再做成数据集的格式


### 翻译质量评估的任务：
在四轮微调结束之后，需要评估训练的成果，再决定是否涉及模型架构上的改变。

以下是两种思路，评估结果作为我们的背书，可以作为publication的一部分

  1.专家评审

  2.引入可量化的评估标准

- 以下是几种可量化的评估标准：
    
    1. 词汇重叠指标
       
      1.1 BLEU
       
            BLEU（Bilingual Evaluation Understudy）通过计算候选译文与多个参考译文之间的 n‑gram 重叠率，并结合长度惩罚来打分，是最早也是最广泛使用的自动评估指标之一。
       
            https://www.wbolt.com/tw/bleu-metric.html?utm_source=chatgpt.com
       
            https://zhuanlan.zhihu.com/p/659633044
       
      1.2 METEOR
       
            METEOR 在考虑 n‑gram 匹配的基础上，进一步引入词干、同义词匹配以及惩罚词序不一致等机制，通常与 BLEU 配合使用，以提高对语义和可读性的敏感度​
       
            https://zhuanlan.zhihu.com/p/659729027
       
    2. 编辑距离与字符级指标
  
      2.1 TER
       
            TER（Translation Error Rate）通过计算将候选译文变换为参考译文所需的最少插入、删除、替换和移位操作次数，再以参考长度归一化，直接反映译文需要多少改动才能完全匹配参考
       
            https://machinetranslate.org/ter
       
      2.2 chrF
       
            chrF（Character‑level F‑score）使用字符级 n‑gram 而非词级 n‑gram，特别适合形态变化丰富的语言，通过字符 n‑gram F1 分数衡量差异，能够更好地捕捉词形变化
       
            https://machinetranslate.org/chrF
       
    4. 基于语言模型或嵌入的指标
       
      3.1 BERTScore
       
            BERTScore 利用 BERT 等预训练深度模型提取候选与参考的上下文嵌入，然后计算二者在向量空间的匹配度，能较好地反映语义相似性，弥补了纯 n‑gram 指标对重写、同义替换不敏感的缺陷
       
            https://machinetranslate.org/bertscore
       
      3.2 YiSi
       
            YiSi 是一种统一的语义评估与质量估计指标，通过共享语义表示将评估和预测任务结合，能够在资源丰富或稀缺语言上都获得稳定效果
       
            https://aclanthology.org/W19-5358/
       
      3.3 BLEURT
       
            BLEURT（Bilingual Evaluation Understudy with Representations from Transformers）在 BERTScore 思路上加入了专门的回归层，并用人工评估数据进行微调，进一步提升了与人工评分的一致性和鲁棒性
       
            https://oecd.ai/en/catalogue/metrics/bleurt-bilingual-evaluation-understudy-with-representations-from-transformers
       
            https://huggingface.co/spaces/evaluate-metric/bleurt/blob/main/README.md
       
     6. 基于学习/监督型指标
        
      4.1 BARTScore
        
            BARTScore 将评估任务视为“生成”问题：给定候选或参考，使用 BART 模型计算将其“转”回另一侧的概率，分值越高表明译文质量越好，可从流利度、保真度等不同视角评估
        
            https://arxiv.org/abs/2106.11520
        
            https://paperswithcode.com/paper/bartscore-evaluating-generated-text-as-text
        
      4.2 Prism
        
            Prism 利用多语种 NMT 系统作为零样本“释义”模型，将候选译文和参考同源化，通过系统自身对参考的重构能力来打分，在多语言场景表现出色
        
            https://github.com/thompsonb/prism
        
            https://anwarvic.github.io/machine-translation/Evaluation
        
      4.3 COMET
        
            COMET 基于跨编码器（Cross-encoder）架构，结合上下文信息和多个语义层面特征，通过有监督训练来拟合人类判断，是当前 WMT 上表现最好的参考型指标之一
        
            https://github.com/Unbabel/COMET
        
      4.4 COMET-QE（质量估计）
        
            COMET-QE 是无参考（reference-free）的质量估计版本，仅基于源文和译文给出质量分，无需参考译文，可用于在线翻译系统的实时评估和监控​
        
            https://aclanthology.org/2022.wmt-1.6/
            
    有些（比如BLEURT/COMET）可以进行针对长文本的微调
  
    人工评审+量化的评估标准，可以综合检验我们的翻译成果。



### 长文本训练的相关问题
![image](https://github.com/user-attachments/assets/87ee6bb2-4c15-4b48-ae33-1a816bfef79e)
![image](https://github.com/user-attachments/assets/5db3460e-5478-4585-a4fa-975bf41cf0ce)
![image](https://github.com/user-attachments/assets/5b010896-315f-4138-9bc5-b6e625c0eb84)
![image](https://github.com/user-attachments/assets/e4698752-d8da-4d27-aca7-a07682026b27)
![image](https://github.com/user-attachments/assets/472b45b7-6744-4842-8169-c3251e390034)



### 后期模型架构相关问题
![image](https://github.com/user-attachments/assets/dca12d96-1739-40d9-92c6-72e1871a42ca)
![image](https://github.com/user-attachments/assets/1aa9550b-690e-4568-a0ea-ee552bafa83a)
![image](https://github.com/user-attachments/assets/117c7a84-61b3-4ffd-a4c7-d257d70b246f)
![image](https://github.com/user-attachments/assets/ef9bb5cf-f2ae-45ae-92dc-537206251ff8)
![image](https://github.com/user-attachments/assets/9b7300ae-b5a7-480a-9d7b-00cc888744d6)








