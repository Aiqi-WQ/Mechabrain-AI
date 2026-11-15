"""教材入库：PDF/TXT → 章节切分 → 带页码的切片索引。

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

# 文件名里常见的教材前后缀，入库前剥掉，避免 book 存成 "示例教材_机械原理节选"
BOOK_PREFIXES = ("示例教材_", "示例教材-", "教材_", "教材-")
BOOK_SUFFIXES = ("节选", "片段", "摘录")


def normalize_book(stem: str) -> str:
    """把文件名还原成书名：示例教材_机械原理节选 → 机械原理。"""
    name = stem.strip()
    for prefix in BOOK_PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix) :]
            break
    for suffix in BOOK_SUFFIXES:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name.strip(" _-—·") or stem


def read_pages(path: Path) -> list[tuple[int, str]]:
    """返回 [(页码, 文本)]。TXT 没有页的概念，页码记 0。"""
    if path.suffix.lower() == ".txt":
        return [(0, path.read_text(encoding="utf-8", errors="ignore"))]
    try:
        import fitz  # PyMuPDF
    except ImportError:
        sys.exit("缺少 PyMuPDF：pip install -r requirements-ingest.txt（或直接放 .txt 教材）")
    doc = fitz.open(path)
    pages = [(i + 1, page.get_text()) for i, page in enumerate(doc)]
    doc.close()
    return pages


def split_chapters(pages: list[tuple[int, str]]) -> list[tuple[str, list[tuple[int, str]]]]:
    """按「第 X 章」标题切章，返回 [(章标题, [(页码, 段落文本)])]。没有标题时整体算一章。"""
    chapters: list[tuple[str, list[tuple[int, str]]]] = []
    current_title = "全文"
    current: list[tuple[int, str]] = []
    for page_no, text in pages:
        for line in text.splitlines():
            match = CHAPTER_RE.match(line)
            if match and len(line.strip()) <= 40:
                if current:
                    chapters.append((current_title, current))
                current_title = line.strip()
                current = []
            elif line.strip():
                current.append((page_no, line.strip()))
    if current:
        chapters.append((current_title, current))
    return [(title, body) for title, body in chapters if body]


def chunk_paragraphs(
    paragraphs: list[tuple[int, str]],
    min_len: int = CHUNK_MIN,
    max_len: int = CHUNK_MAX,
    overlap: int = OVERLAP,
) -> list[tuple[str, int]]:
    """按段落聚合成 500~800 字的切片，相邻切片重叠约 100 字，并记住切片起始页。"""
    chunks: list[tuple[str, int]] = []
    buffer = ""
    buffer_page = paragraphs[0][0] if paragraphs else 0
    for page_no, para in paragraphs:
        if not buffer:
            buffer_page = page_no
        if len(buffer) + len(para) <= max_len:
            buffer = f"{buffer}\n{para}".strip()
            continue
        if buffer:
            chunks.append((buffer, buffer_page))
            tail = buffer[-overlap:] if len(buffer) > overlap else buffer
            buffer = f"{tail}\n{para}".strip()
            buffer_page = page_no
        else:
            chunks.append((para[:max_len], page_no))
            buffer = para[max_len - overlap : max_len]
            buffer_page = page_no
        while len(buffer) >= max_len:
            chunks.append((buffer[:max_len], buffer_page))
            buffer = buffer[max_len - overlap :]
    if len(buffer) >= min_len:
        chunks.append((buffer, buffer_page))
    elif chunks and buffer:
        last_text, last_page = chunks[-1]
        chunks[-1] = (f"{last_text}\n{buffer}"[: max_len + overlap], last_page)
    elif buffer:
        chunks.append((buffer, buffer_page))
    return chunks


def build(book_filter: str | None = None) -> list[dict]:
    if not TEXTBOOK_DIR.exists():
        sys.exit(f"目录不存在：{TEXTBOOK_DIR}")
    files = sorted(p for p in TEXTBOOK_DIR.iterdir() if p.suffix.lower() in {".pdf", ".txt"})
    if not files:
        sys.exit(f"{TEXTBOOK_DIR} 下没有 .pdf / .txt 教材")

    records: list[dict] = []
    for path in files:
        book = normalize_book(path.stem)
        if book_filter and book_filter not in book:
            continue
        print(f"[ingest] 解析 {path.name} → 书名「{book}」")
        pages = read_pages(path)
        has_real_page = path.suffix.lower() == ".pdf"
        for chapter, body in split_chapters(pages):
            chapter_no = CHAPTER_RE.match(chapter)
            chapter_no_text = re.sub(r"\s+", "", chapter_no.group(1)) if chapter_no else ""
            for chunk, page in chunk_paragraphs(body):
                records.append({
                    "book": book,
                    "chapter": chapter,
                    "chapter_no": chapter_no_text,
                    "page": f"p.{page}" if has_real_page and page else "",
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
    parser.add_argument("--book", default=None, help="只处理书名包含该关键词的教材")
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
