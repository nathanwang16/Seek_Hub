# 翻译质量评估工具 (BERTScore)

这是一个使用BERTScore评估中英文翻译质量的工具。BERTScore基于BERT的语义相似度来评估翻译质量，比传统的基于n-gram匹配的方法(如BLEU)更能捕捉语义相似性。

## 安装

1. 克隆此仓库
2. 安装依赖:
```bash
pip install -r requirements.txt
```

## 使用方法

### 交互模式

直接运行程序，将启动交互模式:

```bash
python translation_evaluator.py
```

在交互模式下，程序将提示您输入中文和英文文本，然后给出评估结果。

### 命令行参数模式

您也可以通过命令行参数提供中文和英文文本:

```bash
python translation_evaluator.py --chinese "这是一个测试句子" --english "This is a test sentence"
```

### 参数说明

- `--interactive`: 启动交互模式
- `--chinese`: 中文文本
- `--english`: 英文文本

## 评估结果说明

程序输出以下评估指标:

- **精确度 (Precision)**: 衡量翻译文本中的词语是否出现在参考文本中
- **召回率 (Recall)**: 衡量参考文本中的词语是否出现在翻译文本中
- **F1分数 (F1-Score)**: 精确度和召回率的调和平均数
- **质量评级**: 对翻译质量的定性评价

## 注意事项

- 首次运行时，程序会下载BERT模型，这可能需要一些时间
- 如果有GPU可用，程序会自动使用GPU加速计算
