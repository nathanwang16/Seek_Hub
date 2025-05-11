# -*- coding: utf-8 -*-
"""
英文 txt + 中文 txt → 句级对齐 → 聚合 ≈8k 汉字 → Alpaca JSONL
依赖：sentence-transformers[LaBSE]、bertalign、nltk、regex、opencc、tqdm
"""

import json, uuid, time, random
from pathlib import Path
import regex as re
import nltk
from opencc import OpenCC
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer
from bertalign.aligner import Aligner

# ---------------- 常量配置 ----------------
CHUNK_SIZE = 8_000                 # 目标中文片段长度（汉字）
OUT_DIR = Path("dataset_alpaca")    # 输出目录
OUT_DIR.mkdir(exist_ok=True)

# ---------------- 初始化 ------------------
nltk.download("punkt", quiet=True)
cc = OpenCC("t2s")                                  # 繁→简
embed_model = SentenceTransformer("sentence-transformers/LaBSE")
aligner = Aligner(model=embed_model)

# ---------------- 文本清洗 -----------------
def clean_txt(raw: str, lang="zh") -> str:
    txt = raw.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"[\x00-\x09\x0B-\x1F\x7F]", "", txt)   # 控制字符
    txt = re.sub(r"\n{3,}", "\n\n", txt)                 # 折叠空行
    return cc.convert(txt) if lang == "zh" else txt.strip()

# ---------------- 分句函数 -----------------
def split_en(text):  # 英文
    return nltk.sent_tokenize(text)

def split_zh(text):  # 中文
    return [s for s in re.split(r'(?<=[。！？])\s*', text) if s.strip()]

# ---------------- 句级对齐 -----------------
def align_sentences(en_sents, zh_sents):
    return aligner.align(en_sents, zh_sents, threshold=0.5)

# ---------------- 片段写出 -----------------
def write_chunk(buf_en, buf_zh, fout):
    record = {
        "role": "",
        "instruction": "",
        "input": " ".join(buf_en),
        "output": "".join(buf_zh)
    }
    fout.write(json.dumps(record, ensure_ascii=False) + "\n")

# ---------------- 构建数据集 ---------------
def build_dataset(en_path: str | Path, zh_path: str | Path):
    en_txt = clean_txt(Path(en_path).read_text(encoding="utf-8"), "en")
    zh_txt = clean_txt(Path(zh_path).read_text(encoding="utf-8"), "zh")

    en_sents = split_en(en_txt)
    zh_sents = split_zh(zh_txt)
    pairs = align_sentences(en_sents, zh_sents)

    basename = Path(en_path).stem.rsplit("_", 1)[0]
    out_file = OUT_DIR / f"{basename}.jsonl"

    buf_en, buf_zh, buf_len = [], [], 0
    with open(out_file, "w", encoding="utf-8") as fout, tqdm(total=len(pairs), desc=basename) as bar:
        for en_idx, zh_idx in pairs:
            es, zs = en_sents[en_idx], zh_sents[zh_idx]
            buf_en.append(es)
            buf_zh.append(zs)
            buf_len += len(zs)
            bar.update(1)

            if buf_len >= CHUNK_SIZE:
                write_chunk(buf_en, buf_zh, fout)
                buf_en, buf_zh, buf_len = [], [], 0

        # 收尾不足 8k 的残段（保留 ≥30% 长度）
        if buf_en and buf_len > CHUNK_SIZE * 0.3:
            write_chunk(buf_en, buf_zh, fout)

    print(f"✓ {basename} 完成 → {out_file}")

# ---------------- 批量入口 ----------------
def batch_process(txt_dir="txt_clean"):
    zh_files = list(Path(txt_dir).glob("*_zh.txt"))
    for zh in zh_files:
        en = zh.with_name(zh.stem.replace("_zh", "_en") + ".txt")
        if en.exists():
            build_dataset(en, zh)
        else:
            print(f"⚠ 缺少英文文件：{en}")

# ---------------- 运行 --------------------
if __name__ == "__main__":
    batch_process("txt_clean")      # 根据实际 txt 路径修改
