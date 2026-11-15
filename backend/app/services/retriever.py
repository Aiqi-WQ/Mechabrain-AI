"""教材切片检索。

两种后端：
- chroma：需要 `chromadb` 与可用的 embedding 服务（bge-m3），按章节元数据过滤；
- lexical：内置 BM25，零依赖，未装 chromadb 或未配置 embedding 时自动降级。

检索结果统一为 [{book, chapter, page, text, score}]。
"""
import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import httpx

from ..config import get_settings

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def resolve_data_path(raw: str) -> Path:
    """配置里的相对路径按 backend/ 解析，这样从仓库根目录、backend/ 或容器里启动都指向同一份数据。"""
    path = Path(raw)
    return path if path.is_absolute() else BACKEND_ROOT / path


CHAPTER_NO_RE = re.compile(r"第\s*[一二三四五六七八九十百0-9]+\s*[章节篇]")


def chapter_no(text: str) -> str:
    """从「第1章 平面机构的自由度」里抽出「第1章」，两边都归一化后再比较。"""
    match = CHAPTER_NO_RE.search(text or "")
    return re.sub(r"\s+", "", match.group(0)) if match else ""


def normalize_book(name: str) -> str:
    return re.sub(r"\s+", "", name or "")


def match_book(meta_book: str, wanted: str) -> bool:
    """书名允许精确相等，也允许一方包含另一方（示例教材_机械原理节选 含 机械原理）。"""
    a, b = normalize_book(meta_book), normalize_book(wanted)
    return a == b or a in b or b in a


def match_chapter(meta_chapter: str, wanted: str) -> bool:
    """章节按编号比对：'第1章' 与 '第1章 平面机构的自由度' 视为同一章。"""
    wanted_no = chapter_no(wanted) or re.sub(r"\s+", "", wanted or "")
    meta_no = chapter_no(meta_chapter)
    if wanted_no and meta_no:
        return wanted_no == meta_no
    a, b = re.sub(r"\s+", "", meta_chapter or ""), re.sub(r"\s+", "", wanted or "")
    return a == b or a.startswith(b)


def tokenize(text: str) -> list[str]:
    """中文按二元切分，英文与数字按词切分，够用且不依赖分词库。"""
    cleaned = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text or "")
    tokens: list[str] = []
    for part in cleaned.split():
        if re.search(r"[\u4e00-\u9fff]", part):
            if len(part) == 1:
                tokens.append(part)
            else:
                tokens.extend(part[i : i + 2] for i in range(len(part) - 1))
        else:
            tokens.append(part.lower())
    return tokens


class LexicalIndex:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.docs = [tokenize(c.get("text", "")) for c in chunks]
        self.tf = [Counter(d) for d in self.docs]
        self.df: Counter = Counter()
        for d in self.docs:
            self.df.update(set(d))
        self.n = len(self.docs) or 1
        self.avgdl = (sum(len(d) for d in self.docs) / self.n) if self.docs else 0.0

    def search(self, query: str, top_k: int = 5, book: str | None = None,
               chapter: str | None = None) -> list[dict]:
        q_tokens = tokenize(query)
        scored: list[tuple[float, int]] = []
        for idx, tf in enumerate(self.tf):
            meta = self.chunks[idx]
            if book and not match_book(meta.get("book", ""), book):
                continue
            if chapter and not match_chapter(meta.get("chapter", ""), chapter):
                continue
            dl = len(self.docs[idx]) or 1
            score = 0.0
            for token in q_tokens:
                freq = tf.get(token)
                if not freq:
                    continue
                df = self.df.get(token, 0)
                idf = math.log(1 + (self.n - df + 0.5) / (df + 0.5))
                score += idf * (freq * 2.2) / (freq + 1.2 * (0.25 + 0.75 * dl / (self.avgdl or 1)))
            if score > 0:
                scored.append((score, idx))
        scored.sort(reverse=True)
        return [dict(self.chunks[i], score=round(s, 3)) for s, i in scored[:top_k]]


def embed_texts(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    if not settings.embedding_base_url:
        raise RuntimeError("未配置 EMBEDDING_BASE_URL，无法做向量检索")
    url = settings.embedding_base_url.rstrip("/") + "/embeddings"
    headers = {"Authorization": f"Bearer {settings.embedding_api_key}"} if settings.embedding_api_key else {}
    resp = httpx.post(
        url,
        json={"model": settings.embedding_model, "input": texts},
        headers=headers,
        timeout=60.0,
    )
    resp.raise_for_status()
    return [item["embedding"] for item in resp.json()["data"]]


class ChromaIndex:
    def __init__(self) -> None:
        import chromadb  # 延迟导入，未安装时由上层降级

        settings = get_settings()
        self.client = chromadb.PersistentClient(path=str(resolve_data_path(settings.chroma_dir)))
        self.collection = self.client.get_or_create_collection("textbook_chunks")

    def search(self, query: str, top_k: int = 5, book: str | None = None,
               chapter: str | None = None) -> list[dict]:
        vector = embed_texts([query])[0]
        where: dict = {}
        if book and chapter:
            where = {"$and": [{"book": book}, {"chapter": chapter}]}
        elif book:
            where = {"book": book}
        elif chapter:
            where = {"chapter": chapter}
        result = self.collection.query(
            query_embeddings=[vector],
            n_results=top_k,
            where=where or None,
        )
        out: list[dict] = []
        for doc, meta, dist in zip(
            result.get("documents", [[]])[0],
            result.get("metadatas", [[]])[0],
            result.get("distances", [[]])[0],
        ):
            out.append({
                "text": doc,
                "book": meta.get("book", ""),
                "chapter": meta.get("chapter", ""),
                "page": meta.get("page", ""),
                "score": round(float(dist), 3),
            })
        return out


def load_chunks() -> list[dict]:
    path = resolve_data_path(get_settings().index_file)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []


@lru_cache
def get_index():
    """返回 (backend_name, index_object)。索引文件缺失时返回 (None, None)。"""
    settings = get_settings()
    chunks = load_chunks()
    if not chunks:
        return None, None
    if settings.chroma_enabled:
        try:
            return "chroma", ChromaIndex()
        except Exception:  # noqa: BLE001 - 未安装或未配置时降级
            pass
    return "lexical", LexicalIndex(chunks)


def catalog() -> list[dict]:
    """返回实际入库的教材目录：[{book, chapters:[{no, title, pages, chunks}]}]。

    前端据此渲染章节树，保证「界面上能点的」与「后端能检索到的」完全一致。
    """
    books: dict[str, dict] = {}
    for chunk in load_chunks():
        book = chunk.get("book", "") or "未命名教材"
        chapter_title = chunk.get("chapter", "") or "全文"
        entry = books.setdefault(book, {"book": book, "chapters": {}})
        item = entry["chapters"].setdefault(
            chapter_title,
            {
                "no": chunk.get("chapter_no") or chapter_no(chapter_title),
                "title": chapter_title,
                "page_from": None,
                "page_to": None,
                "chunks": 0,
            },
        )
        item["chunks"] += 1
        page = chunk.get("page") or ""
        if page.startswith("p.") and page[2:].isdigit():
            number = int(page[2:])
            item["page_from"] = number if item["page_from"] is None else min(item["page_from"], number)
            item["page_to"] = number if item["page_to"] is None else max(item["page_to"], number)

    out: list[dict] = []
    for entry in books.values():
        chapters = []
        for item in entry["chapters"].values():
            pages = ""
            if item["page_from"] and item["page_to"]:
                pages = f"p.{item['page_from']}–{item['page_to']}" if item["page_from"] != item["page_to"] \
                    else f"p.{item['page_from']}"
            chapters.append({
                "no": item["no"],
                "title": item["title"],
                "pages": pages,
                "chunks": item["chunks"],
            })
        out.append({"book": entry["book"], "chapters": chapters})
    return out


def resolve_scope(book: str | None, chapter: str | None) -> tuple[str | None, str | None]:
    """把前端传来的 {book, chapter} 解析成索引里真实的书名与章标题，供 Chroma 元数据过滤。"""
    if not book and not chapter:
        return None, None
    resolved_book, resolved_chapter = book, chapter
    for entry in catalog():
        if book and match_book(entry["book"], book):
            resolved_book = entry["book"]
            for item in entry["chapters"]:
                if chapter and match_chapter(item["title"], chapter):
                    resolved_chapter = item["title"]
                    break
            if book:
                break
    return resolved_book, resolved_chapter


def dedupe_cites(hits: list[dict]) -> list[dict]:
    """同一章节的多个切片只留一条引用，避免 UI 里出现重复标签。"""
    seen: set[tuple[str, str, str]] = set()
    out: list[dict] = []
    for hit in hits:
        key = (hit.get("book", ""), hit.get("chapter", ""), hit.get("page", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append({"book": hit.get("book", ""), "chapter": hit.get("chapter", ""), "page": hit.get("page", "")})
    return out


def retrieve(query: str, top_k: int | None = None, book: str | None = None,
             chapter: str | None = None) -> list[dict]:
    settings = get_settings()
    backend, index = get_index()
    if not index:
        return []
    scope_book, scope_chapter = resolve_scope(book, chapter)
    return index.search(query, top_k or settings.retrieve_top_k, scope_book, scope_chapter)


def backend_name() -> str:
    backend, _ = get_index()
    return backend or "none"


def format_context(hits: list[dict], limit: int = 5) -> str:
    blocks: list[str] = []
    for i, hit in enumerate(hits[:limit], start=1):
        head = f"[{i}] {hit.get('book', '')} {hit.get('chapter', '')} {hit.get('page', '')}"
        blocks.append(f"{head}\n{hit.get('text', '').strip()}")
    return "\n\n".join(blocks)
