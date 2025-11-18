import numpy as np
import yaml
from rag_pipeline.embedder import Embedder
from rag_pipeline.vector_store import VectorStore
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

class Retriever:
    def __init__(self, store_path=config['data']['host'], meta_path=config['data']['chunks']):
        
        # 1. Load Semantic (FAISS) components
        self.embedder = Embedder()
        self.store = VectorStore(self.embedder.model.get_sentence_embedding_dimension(), store_path, meta_path)
        try:
            self.store.load()
            print(f"Đã tải {len(self.store.texts)} chunks cho FAISS.")
        except Exception as e:
            print(f"Lỗi khi tải VectorStore: {e}")
            raise
        
        # 2. Load Keyword (BM25) components
        if not self.store.texts:
            raise Exception("VectorStore không tải được văn bản (texts). Không thể khởi tạo BM25.")
        
        tokenized_corpus = [doc.split(" ") for doc in self.store.texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.bm25_texts = self.store.texts
        print("Đã khởi tạo BM25 index xong.")
    
    def retrieve(self, query, k_semantic=10, k_keyword=10, 
                 semantic_threshold=0.3, bm25_threshold=0.3, 
                 min_results=1):
        """
        Thực hiện tìm kiếm lai với ngưỡng lọc.
        
        Args:
            query: Câu truy vấn
            k_semantic: Số lượng kết quả semantic tối đa
            k_keyword: Số lượng kết quả keyword tối đa
            semantic_threshold: Ngưỡng cosine similarity (0-1). Mặc định 0.3
            bm25_threshold: Ngưỡng BM25 score động. Mặc định 0.3
            min_results: Số kết quả tối thiểu để coi là "tìm thấy tài liệu"
        
        Returns:
            tuple: (fused_docs, is_relevant)
                - fused_docs: Danh sách văn bản đã lọc
                - is_relevant: True nếu tìm thấy tài liệu liên quan, False nếu không
        """
        
        # --- 1. Semantic Search (FAISS) với ngưỡng ---
        q_emb = self.embedder.encode([query], prefix="query")
        semantic_results = self.store.search(np.array(q_emb).reshape(1, -1), k=k_semantic)
        
        semantic_docs = [(score, text) for score, text in semantic_results if score >= semantic_threshold]
        
        print(f"Semantic: {len(semantic_docs)}/{len(semantic_results)} kết quả vượt ngưỡng {semantic_threshold}")
        
        # --- 2. Keyword Search (BM25) với ngưỡng động ---
        tokenized_query = query.lower().split(" ")
        keyword_scores = self.bm25.get_scores(tokenized_query)

        top_k_indices = np.argsort(keyword_scores)[::-1]

        # Ngưỡng động dựa trên top1
        top1 = keyword_scores[top_k_indices[0]]
        dynamic_threshold = bm25_threshold * top1  # ví dụ: 0.3 * top1

        keyword_docs = []
        for i in top_k_indices:
            score = keyword_scores[i]
            if score >= dynamic_threshold and len(keyword_docs) < k_keyword:
                keyword_docs.append((score, self.bm25_texts[i]))
            else:
                break
        
        print(f"BM25: {len(keyword_docs)} kết quả vượt ngưỡng động ({dynamic_threshold:.2f})")
        
        # --- 3. Fuse Results (Hợp nhất) ---
        fused_docs = []
        seen_docs = set()
        
        # Ưu tiên kết quả semantic (thường chính xác hơn)
        for score, doc in semantic_docs:
            if doc not in seen_docs:
                fused_docs.append(doc)
                seen_docs.add(doc)
        
        for score, doc in keyword_docs:
            if doc not in seen_docs:
                fused_docs.append(doc)
                seen_docs.add(doc)
        
        # --- 4. Kiểm tra độ liên quan ---
        is_relevant = len(fused_docs) >= min_results
        
        if not is_relevant:
            print(f"⚠️ CẢNH BÁO: Không tìm thấy tài liệu liên quan (chỉ có {len(fused_docs)} kết quả)")
        else:
            print(f"✓ Tìm thấy {len(fused_docs)} tài liệu liên quan")
        
        return fused_docs, is_relevant
    
    def retrieve_with_validation(self, query, **kwargs):
        """
        Wrapper method trả về None nếu không có tài liệu liên quan.
        """
        fused_docs, is_relevant = self.retrieve(query, **kwargs)

        return fused_docs if is_relevant else None