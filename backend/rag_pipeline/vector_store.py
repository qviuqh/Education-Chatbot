import json
from typing import List, Dict, Any, Tuple

import faiss
import numpy as np


class VectorStore:
    def __init__(self, dim: int, path: str, meta_path: str):
        self.path = path
        self.meta_path = meta_path
        self.index = faiss.IndexFlatIP(dim)
        self.documents: List[Dict[str, Any]] = []

    def add(self, embeddings, documents: List[Dict[str, Any]]):
        self.index.add(np.array(embeddings))
        self.documents.extend(documents)

    def save(self):
        faiss.write_index(self.index, self.path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)

    def load(self):
        self.index = faiss.read_index(self.path)
        with open(self.meta_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

    def search(self, query_emb, k: int = 5) -> List[Tuple[float, Dict[str, Any]]]:
        scores, idxs = self.index.search(query_emb, k)
        return [
            (scores[0][i], self.documents[idxs[0][i]])
            for i in range(len(idxs[0]))
        ]