"""Vector store caching theo môn học.

Module này giữ một cache nhỏ cho các conversation thuộc môn học đang được chọn,
cho phép người dùng chat liên tục mà không phải load lại vector store sau mỗi câu hỏi.
"""

from typing import Dict, Optional
import os

from ..ai_deps import get_embedder
from ..rag_pipeline.rag import create_retriever, RAGRetriever


class VectorStoreCache:
    """Quản lý cache retriever theo môn học đang hoạt động."""

    def __init__(self) -> None:
        self._cache: Dict[int, RAGRetriever] = {}
        self._active_subject_id: Optional[int] = None

    def clear(self) -> None:
        """Xóa toàn bộ cache hiện tại."""
        self._cache.clear()
        self._active_subject_id = None

    def set_active_subject(
        self,
        subject_id: int,
        vector_meta,
    ) -> None:
        """Nạp sẵn vector store cho môn học đang được chọn."""
        if self._active_subject_id == subject_id:
            return

        self.clear()
        self._active_subject_id = subject_id

        if not vector_meta or vector_meta.status != "ready":
            return

        if not (os.path.exists(vector_meta.index_path) and os.path.exists(vector_meta.meta_path)):
            return

        try:
            embedder = get_embedder()
            retriever = create_retriever(
                index_path=vector_meta.index_path,
                meta_path=vector_meta.meta_path,
                embedder=embedder,
            )
            self._cache[subject_id] = retriever
        except Exception as exc:  # pragma: no cover - logging side-effect
            print(f"⚠️  Không thể nạp vector store cho subject {subject_id}: {exc}")

    def get_retriever(self, subject_id: int) -> Optional[RAGRetriever]:
        """Lấy retriever từ cache (nếu tồn tại)."""
        return self._cache.get(subject_id)

    def cache_retriever(
        self, subject_id: int, retriever: RAGRetriever
    ) -> None:
        """Lưu retriever vào cache nếu subject đang hoạt động."""
        if self._active_subject_id == subject_id:
            self._cache[subject_id] = retriever


vector_store_cache = VectorStoreCache()