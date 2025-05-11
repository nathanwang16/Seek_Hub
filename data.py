import yaml
import json
import re
import os
import time
from pathlib import Path
from collections import Counter
from sentence_transformers import SentenceTransformer
from bertalign.aligner import Bertalign as Aligner
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from tqdm.auto import tqdm
import nltk
import logging

try:
    from opencc import OpenCC
except ImportError:
    OpenCC = None

# Configure NLTK to use local data directory
NLTK_DATA_DIR = Path("./nltk_data").absolute()
nltk.data.path.insert(0, str(NLTK_DATA_DIR))

# Configure logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Constants
STAGE_INIT = "INITIALIZATION"
STAGE_EPUB_TO_TXT = "EPUB TO TEXT CONVERSION"
STAGE_TOKENIZE = "SENTENCE TOKENIZATION"
STAGE_ALIGN = "SENTENCE ALIGNMENT"
STAGE_DATASET = "DATASET GENERATION"
STAGE_COMPLETE = "PROCESS COMPLETE"

# Use the correct constant for ebooklib document items
datatype = ebooklib.ITEM_DOCUMENT

# ---------------- YAML CONFIG ----------------
def load_config(yaml_path="parameter.yml"):
    logging.info(f"[{STAGE_INIT}] Loading configuration from {yaml_path}")
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    logging.info(f"[{STAGE_INIT}] Configuration loaded successfully")
    return config

# ---------------- RESOURCE MANAGEMENT ----------------
def ensure_resources_available():
    """Download required NLTK resources if not already available."""
    logging.info(f"[{STAGE_INIT}] Checking required resources...")
    
    # Create NLTK data directory if it doesn't exist
    NLTK_DATA_DIR.mkdir(exist_ok=True, parents=True)
    
    # Check for punkt tokenizer data
    try:
        nltk.data.find('tokenizers/punkt')
        logging.info(f"[{STAGE_INIT}] NLTK punkt tokenizer already available")
    except LookupError:
        logging.info(f"[{STAGE_INIT}] Downloading NLTK punkt tokenizer...")
        nltk.download('punkt', download_dir=str(NLTK_DATA_DIR), quiet=False)

# ---------------- EPUB ➜ TXT ----------------
def epub_to_txt(epub_path: str, txt_path: str, postprocess_func):
    logging.info(f"[{STAGE_EPUB_TO_TXT}] Processing EPUB file: {epub_path}")
    start_time = time.time()
    
    if not Path(epub_path).exists():
        logging.error(f"[{STAGE_EPUB_TO_TXT}] EPUB file not found: {epub_path}")
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
    
    try:
        book = epub.read_epub(epub_path)
        chunks = []
        items_count = 0
        for item in book.get_items_of_type(datatype):
            items_count += 1
            try:
                # Use html.parser as it's more reliable than lxml and always available
                soup = BeautifulSoup(item.get_content(), "html.parser")
                chunks.append(soup.get_text(separator="\n"))
            except Exception as e:
                logging.warning(f"[{STAGE_EPUB_TO_TXT}] Error processing item {items_count}: {str(e)}")
        
        logging.info(f"[{STAGE_EPUB_TO_TXT}] Processed {items_count} document items from EPUB")
        raw_text = "\n\n".join(chunks)
        cleaned = postprocess_func(raw_text)
        
        Path(txt_path).write_text(cleaned, encoding="utf-8")
        logging.info(f"[{STAGE_EPUB_TO_TXT}] Saved cleaned text ({len(cleaned)} chars) => {txt_path}")
        logging.info(f"[{STAGE_EPUB_TO_TXT}] Conversion completed in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        logging.error(f"[{STAGE_EPUB_TO_TXT}] Failed to process {epub_path}: {str(e)}")
        raise

# ---------------- 文本清洗 ------------------
_SENT_END = r"[.!?。！？]"
_HEADER_THRESHOLD = 0.6

def postprocess(raw: str) -> str:
    logging.info(f"[{STAGE_EPUB_TO_TXT}] Post-processing text ({len(raw)} chars)")
    txt = (
        raw.replace("\r\n", "\n")
           .replace("\r", "\n")
           .lstrip("\ufeff")
    )
    txt = re.sub(r"[\x00-\x09\x0B-\x1F\x7F]", "", txt)
    lines = txt.split("\n")
    logging.info(f"[{STAGE_EPUB_TO_TXT}] Split into {len(lines)} lines")
    
    pat_page = re.compile(r"^\s*(?:Page\s*)?\d{1,4}\s*(?:页|Page)?\s*$")
    trimmed = [ln.strip() for ln in lines if ln.strip()]
    common  = {ln for ln, c in Counter(trimmed).items()
                     if c > len(lines) * _HEADER_THRESHOLD and len(ln) < 80}
    logging.info(f"[{STAGE_EPUB_TO_TXT}] Identified {len(common)} common header/footer lines to remove")
    
    def is_noise(line: str) -> bool:
        return pat_page.match(line) or line.strip() in common
    
    content_lines = [ln for ln in lines if not is_noise(ln)]
    logging.info(f"[{STAGE_EPUB_TO_TXT}] Retained {len(content_lines)} content lines after noise removal")
    
    merged, buf = [], ""
    for ln in content_lines:
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
    logging.info(f"[{STAGE_EPUB_TO_TXT}] Final text: {len(merged)} paragraphs, {len(text_block)} chars")
    return text_block.strip()

# ---------------- 分句函数 -----------------
def split_en(text, min_len=2):
    logging.info(f"[{STAGE_TOKENIZE}] Tokenizing English text ({len(text)} chars)")
    sents = nltk.sent_tokenize(text)
    filtered = [s.strip() for s in sents if len(s.strip()) >= min_len]
    logging.info(f"[{STAGE_TOKENIZE}] Found {len(sents)} English sentences, {len(filtered)} after filtering")
    return filtered

def split_zh(text, min_len=2):
    logging.info(f"[{STAGE_TOKENIZE}] Tokenizing Chinese text ({len(text)} chars)")
    sents = [s for s in re.split(r'(?<=[。！？])\s*', text) if s.strip()]
    filtered = [s.strip() for s in sents if len(s.strip()) >= min_len]
    logging.info(f"[{STAGE_TOKENIZE}] Found {len(sents)} Chinese sentences, {len(filtered)} after filtering")
    return filtered

# ---------------- 句级对齐 -----------------
def align_sentences(en_sents, zh_sents):
    logging.info(f"[{STAGE_ALIGN}] Starting sentence alignment ({len(en_sents)} EN, {len(zh_sents)} ZH)")
    start_time = time.time()
    
    try:
        aligner = Aligner(
            src="\n".join(en_sents),
            tgt="\n".join(zh_sents),
            is_split=True
        )
        
        aligner.align_sents()
        
        # Extract indices from alignment result with safety checks
        valid_pairs = []
        for item in aligner.result:
            if not item[0] or not item[1]:  # Skip if either source or target is empty
                continue
                
            # Get first indices from each alignment
            en_idx, zh_idx = item[0][0], item[1][0]
            
            # Verify indices are within bounds
            if 0 <= en_idx < len(en_sents) and 0 <= zh_idx < len(zh_sents):
                valid_pairs.append((en_idx, zh_idx))
            else:
                logging.warning(f"[{STAGE_ALIGN}] Skipping out-of-bounds indices: EN={en_idx}, ZH={zh_idx}")
        
        logging.info(f"[{STAGE_ALIGN}] Alignment completed in {time.time() - start_time:.2f} seconds")
        logging.info(f"[{STAGE_ALIGN}] Found {len(valid_pairs)} valid sentence pairs")
        return valid_pairs
    
    except Exception as e:
        logging.error(f"[{STAGE_ALIGN}] Alignment failed: {str(e)}")
        raise

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
def build_dataset(en_txt_path, zh_txt_path, out_file, chunk_size, min_sent_len=2, use_opencc=False):
    logging.info(f"[{STAGE_DATASET}] Building dataset from aligned sentences")
    start_time = time.time()
    
    if use_opencc and OpenCC is None:
        logging.warning(f"[{STAGE_DATASET}] OpenCC not installed, skipping traditional-to-simplified conversion.")
        use_opencc = False
    
    cc = OpenCC("t2s") if use_opencc and OpenCC else None
    
    # Load sentence transformer model
    logging.info(f"[{STAGE_DATASET}] Loading sentence embedding model")
    embed_model = SentenceTransformer("sentence-transformers/LaBSE")
    
    # Read text files
    en_txt = Path(en_txt_path).read_text(encoding="utf-8")
    zh_txt = Path(zh_txt_path).read_text(encoding="utf-8")
    
    if cc:
        logging.info(f"[{STAGE_DATASET}] Converting traditional to simplified Chinese")
        zh_txt = cc.convert(zh_txt)
    
    # Split into sentences
    en_sents = split_en(en_txt, min_len=min_sent_len)
    zh_sents = split_zh(zh_txt, min_len=min_sent_len)
    
    # Align sentences
    pairs = align_sentences(en_sents, zh_sents)
    
    if len(pairs) < min(len(en_sents), len(zh_sents)) * 0.5:
        logging.warning(f"[{STAGE_DATASET}] Alignment pairs ({len(pairs)}) are less than half of the shorter language's sentence count. Check data quality.")
    
    # Build dataset chunks
    chunk_count = 0
    buf_en, buf_zh, buf_len = [], [], 0
    
    with open(out_file, "w", encoding="utf-8") as fout, tqdm(total=len(pairs), desc=Path(out_file).stem) as bar:
        for en_idx, zh_idx in pairs:
            try:
                es, zs = en_sents[en_idx], zh_sents[zh_idx]
                
                if len(es.strip()) < min_sent_len or len(zs.strip()) < min_sent_len:
                    bar.update(1)
                    continue
                    
                buf_en.append(es)
                buf_zh.append(zs)
                buf_len += len(zs)
                bar.update(1)
                
                if buf_len >= chunk_size:
                    write_chunk(buf_en, buf_zh, fout)
                    chunk_count += 1
                    buf_en, buf_zh, buf_len = [], [], 0
            except IndexError as e:
                logging.error(f"[{STAGE_DATASET}] Index error at pair ({en_idx}, {zh_idx}): {str(e)}")
                bar.update(1)
                continue
        
        # Write the last chunk if it's substantial
        if buf_en and buf_len > chunk_size * 0.3:
            write_chunk(buf_en, buf_zh, fout)
            chunk_count += 1
    
    duration = time.time() - start_time
    logging.info(f"[{STAGE_DATASET}] Generated {chunk_count} chunks in {duration:.2f} seconds")
    logging.info(f"[{STAGE_DATASET}] Finished writing Alpaca dataset to {out_file}")

# ---------------- MAIN --------------------
if __name__ == "__main__":
    logging.info(f"[{STAGE_INIT}] Starting script execution")
    
    # Download resources if needed
    ensure_resources_available()
    
    # Load configuration
    config = load_config("parameter.yml")
    en_epub = config["input_english_epub"]
    zh_epub = config["input_chinese_epub"]
    out_dir = Path(config["output_dir"])
    chunk_size = int(config.get("chunk_size", 8000))
    min_sent_len = int(config.get("min_sentence_length", 2))
    use_opencc = bool(config.get("use_opencc", False))
    
    # Create output directory
    out_dir.mkdir(exist_ok=True)
    
    # Define output paths
    en_txt_path = out_dir / (Path(en_epub).stem + "_en.txt")
    zh_txt_path = out_dir / (Path(zh_epub).stem + "_zh.txt")
    
    # Only convert EPUBs if text files don't exist or are outdated
    en_needs_conversion = (not en_txt_path.exists() or 
                          Path(en_epub).stat().st_mtime > en_txt_path.stat().st_mtime)
    zh_needs_conversion = (not zh_txt_path.exists() or 
                          Path(zh_epub).stat().st_mtime > zh_txt_path.stat().st_mtime)
    
    if en_needs_conversion:
        logging.info(f"[{STAGE_EPUB_TO_TXT}] English EPUB needs conversion")
        epub_to_txt(en_epub, en_txt_path, postprocess)
    else:
        logging.info(f"[{STAGE_EPUB_TO_TXT}] Using existing English text file: {en_txt_path}")
    
    if zh_needs_conversion:
        logging.info(f"[{STAGE_EPUB_TO_TXT}] Chinese EPUB needs conversion")
        epub_to_txt(zh_epub, zh_txt_path, postprocess)
    else:
        logging.info(f"[{STAGE_EPUB_TO_TXT}] Using existing Chinese text file: {zh_txt_path}")
    
    # Output file uses both stems for clarity
    out_file = out_dir / (f"{Path(en_epub).stem}_{Path(zh_epub).stem}_alpaca.jsonl")
    
    # Build the dataset
    build_dataset(en_txt_path, zh_txt_path, out_file, chunk_size, 
                 min_sent_len=min_sent_len, use_opencc=use_opencc)
    
    logging.info(f"[{STAGE_COMPLETE}] Process completed successfully")
