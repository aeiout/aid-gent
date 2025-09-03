import os
import numpy as np
from typing import List, Dict, Any

from server.config_loader import load_rag_settings
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from pinecone import Pinecone

_client = None
_pc = None

def get_openai() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client

def get_pinecone(cfg=None) -> Pinecone:
    global _pc
    if _pc is None:
        _pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    return _pc

def embed_texts(texts: List[str]) -> List[List[float]]:
    cfg = load_rag_settings()
    client = get_openai()
    model = cfg["embeddings"]["model"]
    resp = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in resp.data]

def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]

class RagSearcher:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.pc = get_pinecone(cfg)
        self.index = self.pc.Index(cfg["pinecone"]["index"])
        self.namespace = cfg["pinecone"].get("namespace","default")

    def ingest_all(self) -> Dict[str, int]:
        from server.rag.ingest import ingest_all
        return ingest_all()

    def search(self, query: str, top_k=5, min_score=0.3, mmr=True) -> List[Dict[str, Any]]:
        qvec = embed_query(query)
        res = self.index.query(
            namespace=self.namespace,
            vector=qvec,
            top_k=top_k*3 if mmr else top_k,
            include_metadata=True
        )
        matches = []
        for m in res["matches"]:
            score = m.get("score", 0.0) or 0.0
            md = m["metadata"]
            if score >= min_score:
                matches.append({
                    "doc_id": md["doc_id"],
                    "title": md.get("title",""),
                    "version": md.get("version","1.0"),
                    "snippet_id": md["snippet_id"],
                    "text": md["text"],
                    "score": score
                })

        if not matches:
            return []

        if mmr:
            # simple MMR over the candidate texts
            return self._mmr_rank(qvec, matches, top_k)
        else:
            return sorted(matches, key=lambda x: x["score"], reverse=True)[:top_k]

    def _mmr_rank(self, qvec, matches, k):
        # build matrix
        vecs = np.array(embed_texts([m["text"] for m in matches]))
        q = np.array(qvec)
        # cosine sim
        sim_to_query = (vecs @ q) / (np.linalg.norm(vecs, axis=1) * np.linalg.norm(q) + 1e-9)
        selected = []
        lamb = 0.7
        candidates = list(range(len(matches)))
        while len(selected) < min(k, len(matches)) and candidates:
            if not selected:
                idx = int(np.argmax(sim_to_query[candidates]))
                best = candidates[idx]
                selected.append(best)
                candidates.remove(best)
                continue
            # diversity penalty
            max_sim_to_selected = []
            for ci in candidates:
                sim_sel = []
                for si in selected:
                    denom = (np.linalg.norm(vecs[ci]) * np.linalg.norm(vecs[si]) + 1e-9)
                    sim = (vecs[ci] @ vecs[si]) / denom
                    sim_sel.append(sim)
                max_sim_to_selected.append(max(sim_sel) if sim_sel else 0.0)
            scores = lamb * sim_to_query[candidates] - (1 - lamb) * np.array(max_sim_to_selected)
            pick_local = int(np.argmax(scores))
            pick = candidates[pick_local]
            selected.append(pick)
            candidates.remove(pick)
        return [matches[i] for i in selected]
