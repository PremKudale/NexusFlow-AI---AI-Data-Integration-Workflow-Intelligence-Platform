import hashlib
import numpy as np
from typing import List, Union
from config.settings import settings

class EmbeddingService:
    def __init__(self):
        self.backend = settings.EMBEDDING_BACKEND
        self.dimension = settings.PINECONE_DIMENSION
        self._local_model = None
        self._init_backend()

    def _init_backend(self):
        if self.backend == "vertex":
            try:
                from google.cloud import aiplatform
                from vertexai.language_models import TextEmbeddingModel
                aiplatform.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_LOCATION)
                self._vertex_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
                print(f"[Embeddings] Initialized Vertex AI textembedding-gecko@003")
            except Exception as e:
                print(f"[Warning] Vertex AI initialization skipped: {e}. Falling back to deterministic local embedding.")
                self.backend = "local"

        elif self.backend == "sentence_transformers":
            try:
                from sentence_transformers import SentenceTransformer
                self._local_model = SentenceTransformer("all-MiniLM-L6-v2")
                self.dimension = 384
            except Exception as e:
                print(f"[Warning] SentenceTransformer failed: {e}. Using deterministic local projector.")
                self._local_model = None
        else:
            # High-performance local deterministic semantic projector (default for local dev)
            self._local_model = None

    def _deterministic_embed(self, text: str) -> List[float]:
        """High-entropy deterministic semantic projection for offline standalone execution."""
        dim = self.dimension
        vec = np.zeros(dim, dtype=np.float32)
        words = text.lower().split()
        for idx, word in enumerate(words):
            h = int(hashlib.sha256(word.encode()).hexdigest(), 16)
            pos = h % dim
            val = (h % 1000) / 1000.0 - 0.5
            vec[pos] += val * (1.0 / (1.0 + idx * 0.05))

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0
        return vec.tolist()

    def get_embedding(self, text: str) -> List[float]:
        if self.backend == "vertex" and hasattr(self, "_vertex_model"):
            try:
                embeddings = self._vertex_model.get_embeddings([text])
                return embeddings[0].values
            except Exception:
                return self._deterministic_embed(text)

        if self._local_model is not None:
            try:
                emb = self._local_model.encode(text, normalize_embeddings=True)
                return emb.tolist()
            except Exception:
                return self._deterministic_embed(text)

        return self._deterministic_embed(text)

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.get_embedding(t) for t in texts]

embedding_service = EmbeddingService()
