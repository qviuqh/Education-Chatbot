import numpy as np
from rank_bm25 import BM25Okapi

from .embedder import Embedder
from .vector_store import VectorStore


class Retriever:
    def __init__(self, store_path: str, meta_path: str, embedder=None, store=None):
        # 1. Load Semantic (FAISS) components (có thể dùng cache)
        self.embedder = embedder if embedder is not None else Embedder()
        self.store = (
            store
            if store is not None
            else VectorStore(
                self.embedder.model.get_sentence_embedding_dimension(),
                store_path,
                meta_path,
            )
        )
        if store is None:
            try:
                self.store.load()
                print(f"Đã tải {len(self.store.documents)} chunks cho FAISS.")
            except Exception as e:
                print(f"Lỗi khi tải VectorStore: {e}")
                raise

        # 2. Load Keyword (BM25) components
        if not self.store.documents:
            raise Exception("VectorStore không tải được văn bản (texts). Không thể khởi tạo BM25.")

        # --- FIX: Tự động chuẩn hóa dữ liệu nếu chunks.json chứa list[str] thay vì list[dict] ---
        if self.store.documents and isinstance(self.store.documents[0], str):
            print("⚠️  Cảnh báo: Dữ liệu chunks.json dạng chuỗi cũ. Đang tự động chuẩn hóa...")
            normalized_docs = []
            for i, text in enumerate(self.store.documents):
                normalized_docs.append({
                    "text": text,
                    "metadata": {
                        "chunk_id": i,
                        "source": "unknown",
                        "filename": "unknown"
                    }
                })
            # Cập nhật lại documents trong store để dùng cho các bước sau
            self.store.documents = normalized_docs
        # ----------------------------------------------------------------------------------------

        tokenized_corpus = [doc["text"].split(" ") for doc in self.store.documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.bm25_documents = self.store.documents
        print("Đã khởi tạo BM25 index xong.")

    def retrieve(
        self,
        query,
        k_semantic=10,
        k_keyword=10,
        semantic_threshold=0.3,
        bm25_threshold=0.3,
        min_results=1,
        bm25_min_top1=1.0   # <<< NGƯỠNG TOP1 TỐI THIỂU CHO BM25
    ):
        """
        Thực hiện tìm kiếm lai với ngưỡng lọc.

        Args:
            query: Câu truy vấn
            k_semantic: Số lượng kết quả semantic tối đa
            k_keyword: Số lượng kết quả keyword tối đa
            semantic_threshold: Ngưỡng cosine similarity (0-1). Mặc định 0.3
            bm25_threshold: Hệ số để tạo ngưỡng động cho BM25 (vd 0.3 * top1)
            bm25_min_top1: Ngưỡng tuyệt đối tối thiểu cho điểm BM25 top1.
                           Nếu top1 < bm25_min_top1 => coi như BM25 không tìm được gì.
            min_results: Số kết quả tối thiểu để coi là "tìm thấy tài liệu"

        Returns:
            tuple: (fused_docs, is_relevant)
                - fused_docs: Danh sách văn bản đã lọc (bao gồm metadata)
                - is_relevant: True nếu tìm thấy tài liệu liên quan, False nếu không
        """
        # --- 1. Semantic Search (FAISS) với ngưỡng ---
        q_emb = self.embedder.encode([query], prefix="query")
        semantic_results = self.store.search(np.array(q_emb).reshape(1, -1), k=k_semantic)
        
        semantic_docs = [
            (score, doc) for score, doc in semantic_results if score >= semantic_threshold
        ]
        
        print(f"Semantic: {len(semantic_docs)}/{len(semantic_results)} kết quả vượt ngưỡng {semantic_threshold}")
        # --- 2. Keyword Search (BM25) với ngưỡng động + ngưỡng tuyệt đối ---
        tokenized_query = query.lower().split(" ")
        keyword_scores = self.bm25.get_scores(tokenized_query)

        # Sắp xếp index theo score giảm dần
        top_k_indices = np.argsort(keyword_scores)[::-1]

        # Điểm cao nhất (top1)
        top1 = keyword_scores[top_k_indices[0]]

        keyword_docs = []

        # Nếu top1 quá thấp -> coi như không có tài liệu liên quan
        if top1 <= 0 or top1 < bm25_min_top1:
            print(f"BM25: top1={top1:.4f} < bm25_min_top1={bm25_min_top1:.4f} -> KHÔNG lấy kết quả BM25.")
        else:
            # Ngưỡng động dựa trên top1
            dynamic_threshold = bm25_threshold * top1  # ví dụ: 0.3 * top1
            print(f"BM25: top1={top1:.4f}, ngưỡng động={dynamic_threshold:.4f}")

            for i in top_k_indices:
                score = keyword_scores[i]
                # Dừng nếu score đã dưới ngưỡng hoặc đủ k_keyword
                if score < dynamic_threshold or len(keyword_docs) >= k_keyword:
                    break
                keyword_docs.append((score, self.bm25_documents[i]))

            print(f"BM25: {len(keyword_docs)} kết quả vượt ngưỡng động ({dynamic_threshold:.4f})")

        # --- 3. Fuse Results (Hợp nhất) ---
        fused_docs = []
        seen_docs = set()

        # Ưu tiên kết quả semantic (thường chính xác hơn)
        for score, doc in semantic_docs:
            doc_id = doc["metadata"].get("chunk_unique_id") or doc["metadata"].get("chunk_id")
            if doc_id not in seen_docs:
                fused_docs.append(doc)
                seen_docs.add(doc_id)

        for score, doc in keyword_docs:
            doc_id = doc["metadata"].get("chunk_unique_id") or doc["metadata"].get("chunk_id")
            if doc_id not in seen_docs:
                fused_docs.append(doc)
                seen_docs.add(doc_id)

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