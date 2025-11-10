import faiss
import json
import numpy as np
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)


class VectorStore:
    def __init__(self, dim, path=config['data']['host'], meta_path=config['data']['chunks']):
        self.path = path
        self.meta_path = meta_path
        self.index = faiss.IndexFlatIP(dim)
        self.texts = []

    def add(self, embeddings, texts):
        self.index.add(np.array(embeddings))
        self.texts.extend(texts)
    
    def save(self):
        faiss.write_index(self.index, self.path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.texts, f, ensure_ascii=False, indent=2)
    
    def load(self):
        self.index = faiss.read_index(self.path)
        with open(self.meta_path, "r", encoding="utf-8") as f:
            self.texts = json.load(f)
    
    def search(self, query_emb, k=5):
        scores, idxs = self.index.search(query_emb, k)
        return [(scores[0][i], self.texts[idxs[0][i]]) for i in range(len(idxs[0]))]
