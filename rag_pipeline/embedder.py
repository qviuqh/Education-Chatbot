from sentence_transformers import SentenceTransformer

class Embedder:
    def __init__(self, model_name="intfloat/multilingual-e5-base"):
        self.model = SentenceTransformer(model_name)
    
    def encode(self, texts, prefix="passage"):
        return self.model.encode([f"{prefix}: {t}" for t in texts], normalize_embeddings=True)