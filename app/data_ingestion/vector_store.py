import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import settings
from app.data_ingestion.doc_extractors import SemanticDocumentChunk
from app.data_ingestion.embeddings import embedding_service

VECTOR_STORE_DIR = Path("data/vector_store")
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE = VECTOR_STORE_DIR / "vector_index.json"

class VectorSearchResult:
    def __init__(self, chunk_id: str, score: float, content: str, title: str, source_type: str, metadata: dict):
        self.chunk_id = chunk_id
        self.score = score
        self.content = content
        self.title = title
        self.source_type = source_type
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "score": round(self.score, 4),
            "content": self.content,
            "title": self.title,
            "source_type": self.source_type,
            "metadata": self.metadata
        }

class UnifiedVectorStore:
    def __init__(self):
        self.backend = settings.VECTOR_STORE_BACKEND
        self.records: Dict[str, Dict[str, Any]] = {}
        self._pinecone_index = None
        self._init_backend()
        self._load_local_index()

    def _init_backend(self):
        if self.backend == "pinecone" and settings.PINECONE_API_KEY:
            try:
                from pinecone import Pinecone, ServerlessSpec
                pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                index_name = settings.PINECONE_INDEX_NAME
                existing = [i.name for i in pc.list_indexes()]
                if index_name not in existing:
                    pc.create_index(
                        name=index_name,
                        dimension=embedding_service.dimension,
                        metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region=settings.PINECONE_ENVIRONMENT)
                    )
                self._pinecone_index = pc.Index(index_name)
                print(f"[VectorStore] Connected to Pinecone index: {index_name}")
            except Exception as e:
                print(f"[VectorStore] Pinecone connection fallback: {e}")
                self.backend = "memory"

    def _load_local_index(self):
        if INDEX_FILE.exists():
            try:
                with open(INDEX_FILE, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
            except Exception as e:
                print(f"[VectorStore] Error loading local index: {e}")
                self.records = {}

    def _save_local_index(self):
        try:
            with open(INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(self.records, f, indent=2)
        except Exception as e:
            print(f"[VectorStore] Error saving local index: {e}")

    def upsert_chunks(self, chunks: List[SemanticDocumentChunk]) -> int:
        count = 0
        texts = [c.content for c in chunks]
        embeddings = embedding_service.get_embeddings_batch(texts)

        pinecone_vectors = []
        for chunk, emb in zip(chunks, embeddings):
            record = {
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "title": chunk.title,
                "source_type": chunk.source_type,
                "source_name": chunk.source_name,
                "content": chunk.content,
                "embedding": emb,
                "metadata": chunk.metadata
            }
            self.records[chunk.chunk_id] = record
            count += 1

            if self._pinecone_index is not None:
                pinecone_vectors.append({
                    "id": chunk.chunk_id,
                    "values": emb,
                    "metadata": {
                        "title": chunk.title,
                        "source_type": chunk.source_type,
                        "source_name": chunk.source_name,
                        "content": chunk.content[:1000],  # Pinecone metadata size limit
                        **chunk.metadata
                    }
                })

        if self._pinecone_index and pinecone_vectors:
            try:
                self._pinecone_index.upsert(vectors=pinecone_vectors)
            except Exception as e:
                print(f"[VectorStore] Pinecone upsert warning: {e}")

        self._save_local_index()
        return count

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[VectorSearchResult]:
        query_emb = np.array(embedding_service.get_embedding(query), dtype=np.float32)

        # Pinecone search if available
        if self._pinecone_index is not None:
            try:
                filter_dict = {}
                if source_type:
                    filter_dict["source_type"] = {"$eq": source_type}
                if tenant_id:
                    filter_dict["tenant_id"] = {"$eq": tenant_id}

                res = self._pinecone_index.query(
                    vector=query_emb.tolist(),
                    top_k=top_k,
                    include_metadata=True,
                    filter=filter_dict if filter_dict else None
                )
                results = []
                for match in res.matches:
                    meta = match.metadata or {}
                    results.append(VectorSearchResult(
                        chunk_id=match.id,
                        score=match.score,
                        content=meta.get("content", ""),
                        title=meta.get("title", ""),
                        source_type=meta.get("source_type", "unknown"),
                        metadata=meta
                    ))
                return results
            except Exception as e:
                print(f"[VectorStore] Pinecone query fallback: {e}")

        # Local cosine similarity search
        if not self.records:
            return []

        scored_items = []
        for chunk_id, record in self.records.items():
            # Apply metadata filters
            if source_type and record.get("source_type") != source_type:
                continue
            if tenant_id and record.get("metadata", {}).get("tenant_id") != tenant_id:
                continue

            doc_emb = np.array(record["embedding"], dtype=np.float32)
            denom = (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb))
            cosine_sim = float(np.dot(query_emb, doc_emb) / (denom + 1e-9))

            # Keyword lexical overlap boost for high precision hybrid search
            query_words = set(query.lower().split())
            content_words = set(record["content"].lower().split())
            overlap = len(query_words.intersection(content_words)) / max(len(query_words), 1)
            hybrid_score = 0.7 * cosine_sim + 0.3 * overlap

            scored_items.append((hybrid_score, record))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored_items[:top_k]

        return [
            VectorSearchResult(
                chunk_id=rec["chunk_id"],
                score=score,
                content=rec["content"],
                title=rec["title"],
                source_type=rec["source_type"],
                metadata=rec["metadata"]
            )
            for score, rec in top_matches
        ]

    def get_stats(self) -> Dict[str, Any]:
        types = {}
        for r in self.records.values():
            st = r.get("source_type", "other")
            types[st] = types.get(st, 0) + 1
        return {
            "total_vectors": len(self.records),
            "backend": self.backend,
            "breakdown_by_source": types,
            "dimension": embedding_service.dimension
        }

vector_store = UnifiedVectorStore()

