from typing import Any, Dict, List, Optional

from config import CHROMA_DIR, EMBEDDING_PROVIDER, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, SENTENCE_TRANSFORMER_MODEL


class VectorMemoryIndex:
    def __init__(self) -> None:
        self.enabled = False
        self._collection = None
        self._openai_client = None
        self._sentence_model = None
        self._init_index()

    def _init_index(self) -> None:
        try:
            import chromadb  # type: ignore

            client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            self._collection = client.get_or_create_collection(name="aria_memories")
            self.enabled = True
        except Exception:
            self.enabled = False

    def _embed(self, text: str) -> Optional[List[float]]:
        if EMBEDDING_PROVIDER == "openai" and OPENAI_API_KEY:
            try:
                if self._openai_client is None:
                    from openai import OpenAI  # type: ignore

                    self._openai_client = OpenAI(api_key=OPENAI_API_KEY)
                result = self._openai_client.embeddings.create(
                    model=OPENAI_EMBEDDING_MODEL,
                    input=text,
                )
                return result.data[0].embedding
            except Exception:
                return None

        try:
            if self._sentence_model is None:
                from sentence_transformers import SentenceTransformer  # type: ignore

                self._sentence_model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
            vector = self._sentence_model.encode(text).tolist()
            return vector
        except Exception:
            return None

    def add_memory(self, memory_id: int, content: str, metadata: Dict[str, Any]) -> None:
        if not self.enabled or self._collection is None:
            return
        embedding = self._embed(content)
        if embedding is None:
            return
        try:
            self._collection.upsert(
                ids=[str(memory_id)],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata],
            )
        except Exception:
            return

    def search(self, query: str, limit: int = 5, memory_type: str = "all") -> List[int]:
        if not self.enabled or self._collection is None:
            return []
        embedding = self._embed(query)
        if embedding is None:
            return []
        where = None if memory_type == "all" else {"memory_type": memory_type}
        try:
            result = self._collection.query(
                query_embeddings=[embedding],
                n_results=max(1, limit),
                where=where,
            )
            ids = result.get("ids", [[]])[0]
            return [int(i) for i in ids if str(i).isdigit()]
        except Exception:
            return []
