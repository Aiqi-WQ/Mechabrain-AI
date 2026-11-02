"""教材入库：PDF/TXT → 章节切分 → 切片索引。

用法：
    python scripts/ingest.py                    # 处理 data/textbooks/ 下全部文件
    python scripts/ingest.py --book 机械原理     # 只处理指定教材
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXTBOOK_DIR = ROOT / "data" / "textbooks"
OUTPUT = ROOT / "data" / "index.json"

CHAPTER_RE = re.compile(r"^\s*(第\s*[一二三四五六七八九十百0-9]+\s*[章节篇])\s*(.*)$")
CHUNK_MIN = 500
CHUNK_MAX = 800
OVERLAP = 100


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    try:
        import fitz  # PyMuPDF
    except ImportError:
        sys.exit("缺少 PyMuPDF：pip install -r requirements-ingest.txt（或直接放 .txt 教材）")
    doc = fitz.open(path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages)


def split_chapters(text: str) -> list[tuple[str, str]]:
    """按「第 X 章」标题切章，返回 [(章标题, 正文)]。没有标题时整体算一章。"""
    lines = text.splitlines()
    chapters: list[tuple[str, list[str]]] = []
    current_title = "全文"
    current: list[str] = []
    for line in lines:
        match = CHAPTER_RE.match(line)
        if match and len(line.strip()) <= 40:
            if current:
                chapters.append((current_title, current))
            current_title = line.strip()
            current = []
        else:
            current.append(line)
    if current:
        chapters.append((current_title, current))
    return [(title, "\n".join(body).strip()) for title, body in chapters if len(body) > 0]


def chunk_text(text: str, min_len: int = CHUNK_MIN, max_len: int = CHUNK_MAX,
               overlap: int = OVERLAP) -> list[str]:
    """按段落聚合成 500~800 字的切片，相邻切片重叠约 100 字。"""
    paragraphs = [p.strip() for p in re.split(r"\n{1,}", text) if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for para in paragraphs:
        if len(buffer) + len(para) <= max_len:
            buffer = f"{buffer}\n{para}".strip()
            continue
        if buffer:
            chunks.append(buffer)
            tail = buffer[-overlap:] if len(buffer) > overlap else buffer
            buffer = f"{tail}\n{para}".strip()
        else:
            chunks.append(para[:max_len])
            buffer = para[max_len - overlap : max_len]
        while len(buffer) >= max_len:
            chunks.append(buffer[:max_len])
            buffer = buffer[max_len - overlap :]
    if len(buffer) >= min_len:
        chunks.append(buffer)
    elif chunks and buffer:
        chunks[-1] = f"{chunks[-1]}\n{buffer}"[: max_len + overlap]
    elif buffer:
        chunks.append(buffer)
    return chunks


def build(book_filter: str | None = None) -> list[dict]:
    if not TEXTBOOK_DIR.exists():
        sys.exit(f"目录不存在：{TEXTBOOK_DIR}")
    files = sorted(p for p in TEXTBOOK_DIR.iterdir() if p.suffix.lower() in {".pdf", ".txt"})
    if not files:
        sys.exit(f"{TEXTBOOK_DIR} 下没有 .pdf / .txt 教材")

    records: list[dict] = []
    for path in files:
        book = path.stem
        if book_filter and book_filter not in book:
            continue
        print(f"[ingest] 解析 {path.name} …")
        text = read_text(path)
        for chapter, body in split_chapters(text):
            for chunk in chunk_text(body):
                records.append({
                    "book": book,
                    "chapter": chapter,
                    "page": "",
                    "text": chunk,
                })
    return records


def write_chroma(records: list[dict]) -> None:
    sys.path.insert(0, str(ROOT))
    from app.services.retriever import embed_texts  # 复用同一套 embedding 配置

    import chromadb

    client = chromadb.PersistentClient(path=str(ROOT / "data" / "chroma"))
    collection = client.get_or_create_collection("textbook_chunks")
    texts = [r["text"] for r in records]
    for i in range(0, len(texts), 32):
        batch = texts[i : i + 32]
        collection.add(
            ids=[f"c{i + j}" for j in range(len(batch))],
            documents=batch,
            embeddings=embed_texts(batch),
            metadatas=[{"book": records[i + j]["book"], "chapter": records[i + j]["chapter"],
                        "page": records[i + j]["page"]} for j in range(len(batch))],
        )
    print(f"[ingest] 写入 Chroma 完成：{len(texts)} 条")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", default=None, help="只处理文件名包含该关键词的教材")
    parser.add_argument("--chroma", action="store_true", help="同时写入 Chroma（需安装 chromadb 并配置 embedding）")
    args = parser.parse_args()

    records = build(args.book)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    print(f"[ingest] 写出 {OUTPUT.relative_to(ROOT)}：{len(records)} 条切片")

    if args.chroma:
        write_chroma(records)


if __name__ == "__main__":
    main()
