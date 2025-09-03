import os, glob, uuid, time
import frontmatter
from markdown_it import MarkdownIt

from server.config_loader import load_rag_settings
from server.rag.search import embed_texts, get_pinecone

ROOT = os.path.dirname(os.path.dirname(__file__))
RAG_DIR = os.path.join(os.path.dirname(ROOT), "rag")

def iter_docs():
    for path in glob.glob(os.path.join(RAG_DIR, "docs", "**", "*.md"), recursive=True):
        yield path

def chunk_markdown(md_text: str, target_chars=900, overlap=120):
    # very simple chunker: split by headings first, then by length
    md = MarkdownIt()
    tokens = md.parse(md_text)
    pieces = []
    buf = []
    char_count = 0
    for tok in tokens:
        if tok.type in ("heading_open",):
            # flush previous
            if buf:
                text = "".join(buf).strip()
                pieces.extend(split_len(text, target_chars, overlap))
                buf = []
                char_count = 0
        if tok.type == "inline":
            buf.append(tok.content + "\n")
            char_count += len(tok.content)
    if buf:
        text = "".join(buf).strip()
        pieces.extend(split_len(text, target_chars, overlap))
    return [p for p in pieces if p.strip()]

def split_len(text: str, target: int, overlap: int):
    out = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + target, n)
        out.append(text[start:end])
        start = end - overlap if end - overlap > start else end
    return out

def ingest_all():
    cfg = load_rag_settings()
    pine = get_pinecone(cfg)
    index = pine.Index(cfg["pinecone"]["index"])

    target_chars = cfg["chunking_guidelines"]["target_chars"]
    overlap = cfg["chunking_guidelines"]["overlap_chars"]

    total_chunks = 0
    docs = 0

    for path in iter_docs():
        post = frontmatter.load(path)
        meta = post.metadata
        body = post.content
        doc_id = meta.get("doc_id") or os.path.splitext(os.path.basename(path))[0]
        title = meta.get("title","")
        version = meta.get("version","1.0")
        category = meta.get("category","")
        tags = meta.get("tags",[])

        chunks = chunk_markdown(body, target_chars=target_chars, overlap=overlap)
        ids = []
        vectors = []
        metadatas = []
        for i, ch in enumerate(chunks, start=1):
            snip_id = f"s{i}"
            ids.append(f"{doc_id}:{snip_id}")
            metadatas.append({
                "doc_id": doc_id, "title": title, "version": version,
                "category": category, "tags": ";".join(tags),
                "snippet_id": snip_id, "text": ch
            })
            vectors.append(ch)

        # embed and upsert
        embeds = embed_texts(vectors)
        to_upsert = [{"id": ids[i], "values": embeds[i], "metadata": metadatas[i]} for i in range(len(ids))]
        # Pinecone v4 upsert
        index.upsert(vectors=to_upsert, namespace=cfg["pinecone"].get("namespace","default"))

        total_chunks += len(chunks); docs += 1

    return {"docs": docs, "chunks": total_chunks}

if __name__ == "__main__":
    ok = ingest_all()
    print("Indexed:", ok)
