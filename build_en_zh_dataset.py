#!/usr/bin/env python
"""
build_en_zh_dataset.py

Usage:
  python build_en_zh_dataset.py  \
      --en book_en.txt \
      --zh book_zh.txt \
      --out ./en_zh_book_ds \
      --max-chunk 2048
"""

import argparse, re, random, itertools, os, json
from pathlib import Path
from typing import List, Tuple
import logging
import yaml


# ── 1. 3rd-party deps ────────────────────────────────────────────────────────
import torch
import random, numpy as np, torch
from sentence_transformers import SentenceTransformer, util  # GPU if available
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer

# ── 2. simple helpers ────────────────────────────────────────────────────────
EN_SENT_RE = re.compile(r'(?<=[\.\?\!])\s+')                 # rudimentary EN
ZH_SENT_RE = re.compile(r'(?<=[。？！])')                    # rudimentary ZH

STOP_WORDS = set("""a an the and or but if while with without of on in at to
this that these those is are was were be been being have has had do does did
can could should would may might must""".split())

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        
def split_sentences(text: str, lang: str) -> List[str]:
    if lang == "en":
        return [s.strip() for s in EN_SENT_RE.split(text) if s.strip()]
    elif lang == "zh":
        return [s.strip() for s in ZH_SENT_RE.split(text) if s.strip()]
    else:
        raise ValueError(lang)

def noisify_en(sentence: str, drop_rate=(0.03, 0.05)) -> str:
    low, high = drop_rate
    words = sentence.split()
    keep = [w for w in words
            if not (w.lower() in STOP_WORDS and random.random() < random.uniform(low, high))]
    return " ".join(keep)

def chunk_paragraphs(sents: List[str], max_tokens: int, tok) -> List[str]:
    """Greedy pack sentences until ~max_tokens."""
    chunks, buff = [], []
    for s in sents:
        buff.append(s)
        if len(tok(" ".join(buff)).input_ids) >= max_tokens:
            chunks.append(" ".join(buff))
            buff = []
    if buff:
        chunks.append(" ".join(buff))
    return chunks

# ── 3. alignment with SBERT / BERT-aligner ───────────────────────────────────
def align(en_sents: List[str], zh_sents: List[str],
          model: SentenceTransformer, device: str) -> List[Tuple[str, str]]:
    """Greedy 1-1 sentence alignment using cosine similarity."""
    model = model.to(device)
    en_emb = model.encode(en_sents, convert_to_tensor=True, device=device, show_progress_bar=False)
    zh_emb = model.encode(zh_sents, convert_to_tensor=True, device=device, show_progress_bar=False)

    sim = util.cos_sim(en_emb, zh_emb)          # shape (N_en, N_zh)
    pairs = []
    used_zh = set()
    for i in range(sim.size(0)):
        j = torch.argmax(sim[i]).item()
        if j not in used_zh:                    # keep unique match
            pairs.append((en_sents[i], zh_sents[j]))
            used_zh.add(j)
    return pairs

# ── 4. main pipeline ────────────────────────────────────────────────────────
def main(config):
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"🔹 Using device: {device}")

    # 4.1 read raw books
    en_raw = Path(config["en"]).read_text(encoding="utf-8")
    zh_raw = Path(config["zh"]).read_text(encoding="utf-8")

    en_sents = split_sentences(en_raw, "en")
    zh_sents = split_sentences(zh_raw, "zh")
    print(f"🔹 Split into {len(en_sents)} EN & {len(zh_sents)} ZH sentences")

    # 4.2 embed & align
    sbert = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    sent_pairs = align(en_sents, zh_sents, sbert, device)
    print(f"🔹 Aligned {len(sent_pairs)} sentence pairs")

    # 4.3 tokenizer for token length & chunking
    tok = AutoTokenizer.from_pretrained("deepseek-ai/deepseek-llm-7b-base")  # any fast tokenizer OK

    # 4.4 build records ─ sentence level
    records = []
    for en_sent, zh_sent in sent_pairs:
        tags   = f"<en> {en_sent} </en><zh> {zh_sent} </zh>"
        toklen = len(tok(tags).input_ids)
        records.append(
            {"en": en_sent,
             "zh": zh_sent,
             "text": tags,
             "tok_len": toklen,
             "noisy_en": noisify_en(en_sent)}
        )

    # 4.5 add doc-/paragraph-level chunks for long-context curriculum
    para_en  = chunk_paragraphs(en_sents, config["max_chunk"], tok)
    para_zh  = chunk_paragraphs(zh_sents, config["max_chunk"], tok)
    long_pairs = list(zip(para_en, para_zh))
    print(f"🔹 Added {len(long_pairs)} paragraph-level pairs (~≤{config['max_chunk']} tokens)")

    for en_para, zh_para in long_pairs:
        tags   = f"<en> {en_para} </en><zh> {zh_para} </zh>"
        toklen = len(tok(tags).input_ids)
        records.append(
            {"en": en_para,
             "zh": zh_para,
             "text": tags,
             "tok_len": toklen,
             "noisy_en": noisify_en(en_para)}
        )

    # 4.6 build Dataset & train/valid split
    random.shuffle(records)
    split = int(0.9 * len(records))
    ds = Dataset.from_list(records)
    dsdict = DatasetDict({
        "train": ds.select(range(split)),
        "valid": ds.select(range(split, len(ds)))
    })

    # 4.7 save
    out = Path(config["out"])
    out.mkdir(parents=True, exist_ok=True)
    dsdict.save_to_disk(str(out))
    print(f"✅ Saved Hugging Face dataset to: {out.resolve()}")

if __name__ == "__main__":
    with open("dataset_parameter.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    set_seed(12345)
    main(config)