from sentence_transformers import SentenceTransformer
import torch

class Embedder:
    def __init__(self, model_name:str="intfloat/multilingual-e5-base", device:str=None):
        # Nếu không truyền device, tự động chọn cuda nếu có, ngược lại cpu
        if not device:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
        print(f"📡 Embedder loading on: {device}")
        self.model = SentenceTransformer(model_name, device=device)
    
    def encode(self, texts, prefix="passage"):
        return self.model.encode([f"{prefix}: {t}" for t in texts], normalize_embeddings=True)