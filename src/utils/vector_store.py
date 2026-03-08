"""
Vector Store using a simple in-memory approach with JSON persistence.
This avoids ChromaDB's Pydantic v1 compatibility issues with Python 3.14.
"""
import json
import os
import hashlib
from typing import List, Dict, Any, Optional

class VectorStore:
    def __init__(self, db_path: str = ".refinery/vector_db"):
        self.db_path = db_path
        self.documents: Dict[str, Dict[str, Any]] = {}
        os.makedirs(db_path, exist_ok=True)
        self._load_index()

    def _load_index(self):
        """Load existing index from disk."""
        index_file = os.path.join(self.db_path, "index.json")
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
            except:
                self.documents = {}

    def _save_index(self):
        """Persist index to disk."""
        index_file = os.path.join(self.db_path, "index.json")
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False)

    def _generate_id(self, text: str) -> str:
        """Generate a simple hash-based ID for content."""
        return hashlib.md5(text.encode()).hexdigest()[:16]

    def _simple_embed(self, text: str) -> List[float]:
        """
        Simple embedding simulation using hash-based vectors.
        In production, replace with actual embedding model (sentence-transformers).
        """
        # Create a pseudo-embedding based on character frequencies
        vec = [0.0] * 128
        text_lower = text.lower()
        for i, char in enumerate(text_lower):
            vec[i % 128] += ord(char) / 255.0
        
        # Normalize
        magnitude = sum(x**2 for x in vec) ** 0.5
        if magnitude > 0:
            vec = [x/magnitude for x in vec]
        return vec

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(x*y for x, y in zip(a, b))
        return dot_product

    def ingest_ldus(self, ldus: List, doc_id: str):
        """Stores LDUs with full metadata for ProvenanceChain."""
        if doc_id not in self.documents:
            self.documents[doc_id] = {"chunks": []}

        for ldu in ldus:
            chunk_id = self._generate_id(ldu.content)
            embedding = self._simple_embed(ldu.content)
            
            chunk_data = {
                "id": chunk_id,
                "content": ldu.content,
                "chunk_type": ldu.chunk_type,
                "embedding": embedding,
                "page": ldu.bounding_box.page if ldu.bounding_box else 1,
                "x0": ldu.bounding_box.x0 if ldu.bounding_box else 0,
                "y0": ldu.bounding_box.y0 if ldu.bounding_box else 0,
                "x1": ldu.bounding_box.x1 if ldu.bounding_box else 100,
                "y1": ldu.bounding_box.y1 if ldu.bounding_box else 100,
                "token_count": ldu.token_count,
                "content_hash": ldu.content_hash
            }
            self.documents[doc_id]["chunks"].append(chunk_data)

        self._save_index()

    def search(self, query: str, n_results: int = 3, doc_id: str = None) -> Dict[str, Any]:
        """
        Returns context + metadata for the QueryAgent.
        Uses simple vector similarity matching.
        """
        query_embedding = self._simple_embed(query)
        
        all_chunks = []
        if doc_id and doc_id in self.documents:
            all_chunks = self.documents[doc_id].get("chunks", [])
        else:
            # Search across all documents
            for doc_id_key, doc_data in self.documents.items():
                all_chunks.extend(doc_data.get("chunks", []))

        if not all_chunks:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        # Compute similarities
        results = []
        for chunk in all_chunks:
            similarity = self._cosine_similarity(query_embedding, chunk.get("embedding", [0]*128))
            results.append((similarity, chunk))

        # Sort by similarity and take top N
        results.sort(key=lambda x: x[0], reverse=True)
        top_results = results[:n_results]

        return {
            "ids": [[r[1]["id"] for r in top_results]],
            "documents": [[r[1]["content"] for r in top_results]],
            "metadatas": [[{
                "page": r[1]["page"],
                "x0": r[1]["x0"],
                "y0": r[1]["y0"],
                "x1": r[1]["x1"],
                "y1": r[1]["y1"],
                "chunk_type": r[1]["chunk_type"],
                "doc_id": doc_id
            } for r in top_results]],
            "distances": [[1 - r[0] for r in top_results]]  # Convert similarity to distance
        }

    def clear(self, doc_id: str = None):
        """Clear documents from the store."""
        if doc_id:
            self.documents.pop(doc_id, None)
        else:
            self.documents = {}
        self._save_index()
