#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
翻译质量评估程序 - 使用BERTScore
此程序接收中文和英文文本文件，评估翻译质量
"""

import torch
import numpy as np
from bert_score import BERTScorer
import argparse
import sys
import os

class TranslationEvaluator:
    def __init__(self, model_type="bert-base-multilingual-cased"):
        """
        初始化BERTScore评估器
        
        参数:
            model_type: 使用的预训练模型，默认使用支持多语言的BERT模型
        """
        print("正在加载BERT模型，这可能需要一些时间...")
        self.scorer = BERTScorer(
            model_type=model_type,
            lang="zh-en",  # 支持中英文
            rescale_with_baseline=False,  # 修改为False以避免基线文件问题
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        print(f"模型已加载，运行于 {self.scorer.device}")
        
    def evaluate(self, chinese_text, english_text):
        """
        评估中英文翻译质量
        
        参数:
            chinese_text: 中文文本(源文本或参考翻译)
            english_text: 英文文本(待评估的翻译)
            
        返回:
            dict: 包含P(精确度)、R(召回率)和F1评分
        """
        # 将文本转换为列表格式
        refs = [chinese_text]
        cands = [english_text]
        
        # 计算BERTScore分数
        P, R, F1 = self.scorer.score(cands, refs)
        
        # 转换为numpy数组便于处理
        P_np = P.cpu().numpy()
        R_np = R.cpu().numpy()
        F1_np = F1.cpu().numpy()
        
        return {
            "precision": float(P_np[0]),  # 精确度
            "recall": float(R_np[0]),     # 召回率
            "f1": float(F1_np[0]),        # F1分数
            "normalized_f1": (float(F1_np[0]) + 1) / 2  # 归一化到0-1范围
        }
    
    def interpret_score(self, score):
        """
        解释BERTScore分数
        
        参数:
            score: F1分数
            
        返回:
            str: 对分数的定性解释
        """
        normalized = (score + 1) / 2  # BERTScore范围从-1到1，归一化到0-1
        
        if normalized >= 0.85:
            return "优秀 (Excellent)"
        elif normalized >= 0.70:
            return "良好 (Good)"
        elif normalized >= 0.60:
            return "一般 (Fair)"
        elif normalized >= 0.45:
            return "较差 (Poor)"
        else:
            return "很差 (Very Poor)"

def main():
    parser = argparse.ArgumentParser(description="使用BERTScore评估中英文翻译质量")
    parser.add_argument("--chinese-file", type=str, required=True, help="包含中文文本的文件路径")
    parser.add_argument("--english-file", type=str, required=True, help="包含英文文本的文件路径")
    parser.add_argument("--output", type=str, help="输出结果到文件")
    args = parser.parse_args()
    
    try:
        # 初始化评估器
        evaluator = TranslationEvaluator()
        
        # 从文件读取内容
        chinese_text = ""
        english_text = ""
        
        # 读取中文文件
        if not os.path.exists(args.chinese_file):
            print(f"错误: 文件不存在 - {args.chinese_file}")
            sys.exit(1)
        
        with open(args.chinese_file, 'r', encoding='utf-8') as f:
            chinese_text = f.read().strip()
            
        # 读取英文文件
        if not os.path.exists(args.english_file):
            print(f"错误: 文件不存在 - {args.english_file}")
            sys.exit(1)
            
        with open(args.english_file, 'r', encoding='utf-8') as f:
            english_text = f.read().strip()
        
        print(f"已读取中文文件: {args.chinese_file} ({len(chinese_text)} 字符)")
        print(f"已读取英文文件: {args.english_file} ({len(english_text)} 字符)")
        
        # 评估翻译质量
        results = evaluator.evaluate(chinese_text, english_text)
        
        # 输出结果
        output_text = "\n评估结果:\n"
        output_text += f"精确度 (Precision): {results['precision']:.4f}\n"
        output_text += f"召回率 (Recall): {results['recall']:.4f}\n"
        output_text += f"F1分数 (F1-Score): {results['f1']:.4f}\n"
        output_text += f"质量评级: {evaluator.interpret_score(results['f1'])}"
        
        # 输出到文件或控制台
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"结果已保存到文件: {args.output}")
        
        # 始终在控制台显示结果
        print(output_text)
            
    except Exception as e:
        print(f"发生错误: {e}")
        print("\n请确保已安装所需依赖:")
        print("pip install torch numpy bert-score transformers")
        sys.exit(1)

if __name__ == "__main__":
    main() 