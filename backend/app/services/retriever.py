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
            if book and meta.get("book") != book:
                continue
            if chapter and meta.get("chapter") != chapter:
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
        self.client = chromadb.PersistentClient(path=settings.chroma_dir)
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
    path = Path(get_settings().index_file)
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


def retrieve(query: str, top_k: int | None = None, book: str | None = None,
             chapter: str | None = None) -> list[dict]:
    settings = get_settings()
    backend, index = get_index()
    if not index:
        return []
    return index.search(query, top_k or settings.retrieve_top_k, book, chapter)


def backend_name() -> str:
    backend, _ = get_index()
    return backend or "none"


def format_context(hits: list[dict], limit: int = 5) -> str:
    blocks: list[str] = []
    for i, hit in enumerate(hits[:limit], start=1):
        head = f"[{i}] {hit.get('book', '')} {hit.get('chapter', '')} {hit.get('page', '')}"
        blocks.append(f"{head}\n{hit.get('text', '').strip()}")
    return "\n\n".join(blocks)
