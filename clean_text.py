#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文本清洗脚本 - 根据特定规则处理注释
1. 当①等符号在句子开头时，删除整个句子（作为注释）
2. 当①等符号在句子中间时，只删除符号本身（保留句子内容）
"""

import re
import os
import logging
from collections import Counter
from pathlib import Path
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 定义常量
_SENT_END = r"[.!?。！？]"
_HEADER_THRESHOLD = 0.6
# 注释符号模式
_NOTE_SYMBOLS = r'[①②③④⑤⑥⑦⑧⑨⑩]|【\d+】|\[\d+\]|\(\d+\)'

def postprocess(raw: str) -> str:
    """
    清洗文本，按照特定规则处理注释
    """
    logging.info(f"正在处理文本 ({len(raw)} 字符)")
    txt = (
        raw.replace("\r\n", "\n")
           .replace("\r", "\n")
           .lstrip("\ufeff")
    )
    txt = re.sub(r"[\x00-\x09\x0B-\x1F\x7F]", "", txt)
    lines = txt.split("\n")
    logging.info(f"拆分为 {len(lines)} 行")
    
    # 页码模式
    pat_page = re.compile(r"^\s*(?:Page\s*)?\d{1,4}\s*(?:页|Page)?\s*$")
    # 注释符号开头的模式
    pat_note_start = re.compile(r'^\s*(?:' + _NOTE_SYMBOLS + r')')
    
    trimmed = [ln.strip() for ln in lines if ln.strip()]
    common  = {ln for ln, c in Counter(trimmed).items()
                     if c > len(lines) * _HEADER_THRESHOLD and len(ln) < 80}
    logging.info(f"识别出 {len(common)} 个常见页眉/页脚行需要移除")
    
    # 筛选掉页码、页眉页脚和以注释符号开头的行
    def is_noise(line: str) -> bool:
        return pat_page.match(line) or line.strip() in common or pat_note_start.match(line)
    
    content_lines = [ln for ln in lines if not is_noise(ln)]
    note_lines_removed = len(lines) - len(content_lines)
    logging.info(f"移除了 {note_lines_removed} 行以注释符号开头的整行")
    logging.info(f"噪音清除后保留了 {len(content_lines)} 行内容")
    
    # 处理句子中间的注释符号 - 只删除符号本身
    processed_lines = []
    note_symbols_removed = 0
    
    for line in content_lines:
        if line.strip():
            # 替换句子中间的注释符号
            original_len = len(line)
            # 只替换符号本身，不删除后面的内容
            line = re.sub(_NOTE_SYMBOLS, '', line)
            note_symbols_removed += original_len - len(line)
            processed_lines.append(line)
        else:
            processed_lines.append(line)  # 保留空行
    
    logging.info(f"在保留的文本中删除了 {note_symbols_removed} 个注释符号")
    
    # 合并段落
    merged, buf = [], ""
    for ln in processed_lines:
        if not ln.strip():
            if buf:
                merged.append(buf)
                buf = ""
            continue
        buf += ln.strip()
        if re.search(_SENT_END + r"$", ln):
            merged.append(buf)
            buf = ""
        else:
            buf += " "
    if buf:
        merged.append(buf)
    
    text_block = "\n".join(merged)
    text_block = re.sub(r"-\s*\n([a-zA-Z])", r"\1", text_block)
    text_block = re.sub(r"\n{3,}", "\n\n", text_block)
    
    logging.info(f"最终文本: {len(merged)} 段落, {len(text_block)} 字符")
    return text_block.strip()

def main():
    if len(sys.argv) < 2:
        print("用法: python clean_text.py <输入文件路径> [输出文件路径]")
        return
    
    input_file = sys.argv[1]
    
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # 自动生成输出文件名
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}")
    
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 {input_file}")
        return
    
    try:
        # 读取文件
        logging.info(f"正在读取文件: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 处理文本
        cleaned_text = postprocess(content)
        
        # 保存结果
        logging.info(f"正在保存清洗后的文本到: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        logging.info(f"文本清洗完成! 原始大小: {len(content)} 字符, 清洗后: {len(cleaned_text)} 字符")
        print(f"\n清洗完成! 结果已保存到: {output_file}")
        
    except Exception as e:
        logging.error(f"处理失败: {str(e)}")
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    main() 