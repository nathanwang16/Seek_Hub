下面是一份 **可直接运行的 Python 脚本**（`bertscore_eval.py`），从 0 开始演示如何使用 [BERTScore](https://github.com/Tiiiger/bert_score) 评估英→中翻译质量。它支持两种场景：

1. **候选译文 vs. 中文参考译文** → 采用中文 BERT 权重做同语 BERTScore
2. **英文原文 vs. 中文候选译文** → 采用多语 XLM-R 权重做跨语 BERTScore

> ⚙️ **前置环境**
>
> ```bash
> pip install bert-score transformers torch
> ```

```python
#!/usr/bin/env python
# bertscore_eval.py
"""
BERTScore evaluator for English→Chinese translation.

Usage (交互):
    python bertscore_eval.py
        然后按提示输入:
            ① 英文原文 或 中文参考译文
            ② 中文候选译文
            ③ 选择评测模式: 1=中-中; 2=英-中

Usage (命令行):
    python bertscore_eval.py \
        --src "The weather is nice today." \
        --tgt "今天天气很好。" \
        --mode en-zh
"""

import argparse
from typing import List, Tuple

from bert_score import score  # pip install bert-score


def compute_bertscore(
    refs: List[str],
    hyps: List[str],
    mode: str,
    model: str = None,
    use_idf: bool = False,
    rescale: bool = True,
) -> Tuple[float, float, float]:
    """
    Compute BERTScore for given reference / candidate lists.

    Args:
        refs: list of reference sentences (中文或英文)
        hyps: list of candidate sentences (中文)
        mode: 'zh-zh' 或 'en-zh'
        model: 指定 HuggingFace 模型名；若为空则根据 mode 选择默认模型
        use_idf: 是否使用 IDF 加权
        rescale: 是否 rescale_with_baseline=True

    Returns:
        (Precision, Recall, F1) 均值三元组
    """
    if mode not in {"zh-zh", "en-zh"}:
        raise ValueError("mode 必须是 'zh-zh' 或 'en-zh'")

    if model is None:
        # 根据任务自动选择预训练权重
        model = (
            "bert-base-chinese"
            if mode == "zh-zh"
            else "xlm-roberta-large"
        )

    P, R, F1 = score(
        cands=hyps,
        refs=refs,
        lang="zh" if mode == "zh-zh" else "en",
        # lang2 仅 cross-lingual 时使用；新版 bert-score 支持
        lang2="zh" if mode == "en-zh" else None,
        model_type=model,
        idf=use_idf,
        rescale_with_baseline=rescale,
    )
    return P.mean().item(), R.mean().item(), F1.mean().item()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute BERTScore for English→Chinese translation."
    )
    parser.add_argument(
        "--src",
        type=str,
        help="英文原文或中文参考译文；若省略则进入交互模式。",
    )
    parser.add_argument(
        "--tgt",
        type=str,
        help="中文候选译文；若省略则进入交互模式。",
    )
    parser.add_argument(
        "--mode",
        choices=["zh-zh", "en-zh"],
        help="评测模式: zh-zh(中文参考) 或 en-zh(英文原文).",
    )
    parser.add_argument("--model", type=str, default=None, help="自定义 HuggingFace 模型名")
    parser.add_argument("--idf", action="store_true", help="是否启用 IDF 加权")
    return parser.parse_args()


def interactive() -> None:
    print(">>> BERTScore 翻译质量评估器 <<<\n")
    print("第一步: 输入英文原文 (或中文参考译文): ")
    src = input().strip()
    print("\n第二步: 输入 **中文候选译文**:")
    tgt = input().strip()

    print(
        "\n第三步: 请选择评测模式\n"
        "  1. src 是中文参考译文 (同语 zh-zh)\n"
        "  2. src 是英文原文 (跨语 en-zh)"
    )
    mode_choice = input("选择 1 或 2: ").strip()
    mode = "zh-zh" if mode_choice == "1" else "en-zh"

    P, R, F1 = compute_bertscore([src], [tgt], mode)
    print(
        f"\n=== 评测结果 ({mode}) ===\n"
        f"Precision: {P:.4f}\n"
        f"Recall   : {R:.4f}\n"
        f"F1-score : {F1:.4f}"
    )


def main() -> None:
    args = parse_args()
    if args.src is None or args.tgt is None:
        # 进入交互模式
        interactive()
        return

    mode = args.mode or "zh-zh"
    P, R, F1 = compute_bertscore(
        [args.src],
        [args.tgt],
        mode=mode,
        model=args.model,
        use_idf=args.idf,
    )
    print(
        f"=== BERTScore ({mode}) ===\n"
        f"Precision: {P:.4f}\n"
        f"Recall   : {R:.4f}\n"
        f"F1-score : {F1:.4f}"
    )


if __name__ == "__main__":
    main()
```

### 使用说明

1. **交互模式**

   ```bash
   python bertscore_eval.py
   ```

   按提示依次输入

   * 英文原文 *或* 中文参考译文
   * 中文候选译文
   * 选择评测模式

2. **命令行直传**

   ```bash
   python bertscore_eval.py \
       --src "The weather is nice today." \
       --tgt "今天天气很好。" \
       --mode en-zh
   ```

   * 若有高质量**中文参考译文**：

     ```bash
     python bertscore_eval.py \
         --src "今天天气晴朗宜人。" \
         --tgt "今天天气很好。" \
         --mode zh-zh
     ```

3. **自定义权重与 IDF**

   ```bash
   python bertscore_eval.py --src ... --tgt ... --model microsoft/infoxlm-large --idf --mode en-zh
   ```

### 结果解读

* **Precision** 偏向惩罚过译（生成了参考中没有的内容）
* **Recall** 偏向惩罚漏译（参考中的含义未覆盖）
* **F1-score** 综合两者，一般用作主要指标
* 分数区间 0–1（若 `--rescale_with_baseline` 为 True，脚本默认已启用）

> 若需批量评测多个句对，可把 `compute_bertscore` 部分封装进数据管线：
>
> ```python
> refs = open("refs.txt").read().splitlines()
> hyps = open("hyps.txt").read().splitlines()
> P, R, F1 = compute_bertscore(refs, hyps, mode="zh-zh")
> ```

脚本即拿即用，帮助你在 DeepSeek-V3 微调迭代中快速衡量英译中系统的语义质量。祝实验顺利!
