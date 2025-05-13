#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
翻译质量评估器的示例用法
"""

from translation_evaluator import TranslationEvaluator

def main():
    # 初始化评估器
    evaluator = TranslationEvaluator()
    
    # 示例文本对 1 - 好的翻译
    chinese_1 = "人工智能正在改变我们的世界。"
    english_1 = "Artificial intelligence is changing our world."
    
    # 示例文本对 2 - 较差的翻译
    chinese_2 = "他昨天去了商店买了一些水果。"
    english_2 = "He went to the store yesterday."  # 缺少"买水果"的部分
    
    # 评估示例1
    print("\n示例 1:")
    print(f"中文: {chinese_1}")
    print(f"英文: {english_1}")
    results_1 = evaluator.evaluate(chinese_1, english_1)
    print("\n评估结果:")
    print(f"精确度 (Precision): {results_1['precision']:.4f}")
    print(f"召回率 (Recall): {results_1['recall']:.4f}")
    print(f"F1分数 (F1-Score): {results_1['f1']:.4f}")
    print(f"质量评级: {evaluator.interpret_score(results_1['f1'])}")
    
    # 评估示例2
    print("\n" + "-" * 50)
    print("\n示例 2:")
    print(f"中文: {chinese_2}")
    print(f"英文: {english_2}")
    results_2 = evaluator.evaluate(chinese_2, english_2)
    print("\n评估结果:")
    print(f"精确度 (Precision): {results_2['precision']:.4f}")
    print(f"召回率 (Recall): {results_2['recall']:.4f}")
    print(f"F1分数 (F1-Score): {results_2['f1']:.4f}")
    print(f"质量评级: {evaluator.interpret_score(results_2['f1'])}")

if __name__ == "__main__":
    main() 