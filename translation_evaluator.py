#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
翻译质量评估程序 - 使用BERTScore
此程序接收中文和英文文本，评估翻译质量
"""

import torch
import numpy as np
from bert_score import BERTScorer
import argparse
import sys

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
            rescale_with_baseline=True,
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
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    parser.add_argument("--chinese", type=str, help="中文文本")
    parser.add_argument("--english", type=str, help="英文文本")
    args = parser.parse_args()
    
    try:
        # 初始化评估器
        evaluator = TranslationEvaluator()
        
        if args.interactive or (not args.chinese and not args.english):
            # 交互模式
            print("\n欢迎使用翻译质量评估工具\n")
            print("请输入中文文本 (输入 'q' 退出):")
            
            while True:
                chinese_text = input("\n中文文本: ")
                if chinese_text.lower() == 'q':
                    break
                    
                english_text = input("英文文本: ")
                if english_text.lower() == 'q':
                    break
                
                if not chinese_text or not english_text:
                    print("错误: 两种语言的文本都必须提供")
                    continue
                
                # 评估翻译质量
                results = evaluator.evaluate(chinese_text, english_text)
                
                # 输出结果
                print("\n评估结果:")
                print(f"精确度 (Precision): {results['precision']:.4f}")
                print(f"召回率 (Recall): {results['recall']:.4f}")
                print(f"F1分数 (F1-Score): {results['f1']:.4f}")
                print(f"质量评级: {evaluator.interpret_score(results['f1'])}")
                print("\n" + "-" * 50)
        else:
            # 命令行参数模式
            if not args.chinese or not args.english:
                print("错误: 必须同时提供中文和英文文本")
                sys.exit(1)
                
            # 评估翻译质量
            results = evaluator.evaluate(args.chinese, args.english)
            
            # 输出结果
            print("\n评估结果:")
            print(f"精确度 (Precision): {results['precision']:.4f}")
            print(f"召回率 (Recall): {results['recall']:.4f}")
            print(f"F1分数 (F1-Score): {results['f1']:.4f}")
            print(f"质量评级: {evaluator.interpret_score(results['f1'])}")
            
    except Exception as e:
        print(f"发生错误: {e}")
        print("\n请确保已安装所需依赖:")
        print("pip install torch numpy bert-score transformers")
        sys.exit(1)

if __name__ == "__main__":
    main() 