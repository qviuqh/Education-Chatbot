from rag_pipeline.embedder import Embedder
from rag_pipeline.vector_store import VectorStore
import numpy as np
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

class Retriever:
    def __init__(self, store_path=config['data']['host'], meta_path=config['data']['chunks']):
        self.embedder = Embedder()
        self.store = VectorStore(self.embedder.model.get_sentence_embedding_dimension(), store_path, meta_path)
        self.store.load()

    def retrieve(self, query, k=5):
        q_emb = self.embedder.encode([query], prefix="query")
        return self.store.search(np.array(q_emb).reshape(1, -1), k)