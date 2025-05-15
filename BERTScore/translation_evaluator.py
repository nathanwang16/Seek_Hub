#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
翻译质量评估程序 - 使用BERTScore
此程序接收中文和英文文本，评估翻译质量
支持文件输入输出，适合处理长文本
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
            rescale_with_baseline=False,
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
    parser.add_argument("--chinese-file", type=str, help="包含中文文本的文件路径")
    parser.add_argument("--english-file", type=str, help="包含英文文本的文件路径")
    parser.add_argument("--output", type=str, help="输出结果到文件")
    args = parser.parse_args()
    
    try:
        # 初始化评估器
        evaluator = TranslationEvaluator()
        
        # 从文件读取内容
        chinese_text = ""
        english_text = ""
        
        if args.chinese_file:
            if os.path.exists(args.chinese_file):
                with open(args.chinese_file, 'r', encoding='utf-8') as f:
                    chinese_text = f.read().strip()
            else:
                print(f"错误: 文件不存在 - {args.chinese_file}")
                sys.exit(1)
                
        if args.english_file:
            if os.path.exists(args.english_file):
                with open(args.english_file, 'r', encoding='utf-8') as f:
                    english_text = f.read().strip()
            else:
                print(f"错误: 文件不存在 - {args.english_file}")
                sys.exit(1)
        
        # 如果提供了命令行参数中的文本，使用命令行参数
        if args.chinese:
            chinese_text = args.chinese
            
        if args.english:
            english_text = args.english
        
        if args.interactive or (not chinese_text and not english_text):
            # 交互模式
            print("\n欢迎使用翻译质量评估工具\n")
            print("请输入中文文本 (输入 'q' 退出):")
            print("提示: 对于长文本，请使用 --chinese-file 和 --english-file 参数指定文件路径")
            
            while True:
                print("\n中文文本 (或输入'file:'后跟文件路径): ", end="")
                chinese_input = input()
                if chinese_input.lower() == 'q':
                    break
                    
                # 支持从文件读取
                if chinese_input.startswith("file:"):
                    file_path = chinese_input[5:].strip()
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            chinese_text = f.read().strip()
                        print(f"已从文件 {file_path} 读取中文文本")
                    except Exception as e:
                        print(f"读取文件失败: {e}")
                        continue
                else:
                    chinese_text = chinese_input
                
                print("英文文本 (或输入'file:'后跟文件路径): ", end="")
                english_input = input()
                if english_input.lower() == 'q':
                    break
                
                # 支持从文件读取
                if english_input.startswith("file:"):
                    file_path = english_input[5:].strip()
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            english_text = f.read().strip()
                        print(f"已从文件 {file_path} 读取英文文本")
                    except Exception as e:
                        print(f"读取文件失败: {e}")
                        continue
                else:
                    english_text = english_input
                
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
            if not chinese_text or not english_text:
                print("错误: 必须同时提供中文和英文文本")
                print("可以使用 --chinese-file 和 --english-file 参数指定包含文本的文件路径")
                sys.exit(1)
                
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
            else:
                print(output_text)
            
    except Exception as e:
        print(f"发生错误: {e}")
        print("\n请确保已安装所需依赖:")
        print("pip install torch numpy bert-score transformers")
        sys.exit(1)

if __name__ == "__main__":
    main() 