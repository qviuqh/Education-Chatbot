"""Vector store caching theo môn học.

Module này giữ một cache nhỏ cho các conversation thuộc môn học đang được chọn, 
cho phép người dùng chat liên tục mà không phải load lại vector store sau mỗi câu hỏi.
"""

from typing import Dict, Optional, Iterable
import os

from ..ai_deps import get_embedder
from ..rag_pipeline.rag import create_retriever, RAGRetriever
from ..models import Conversation


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
        conversations: Iterable[Conversation],
    ) -> None:
        """
        Nạp sẵn vector store cho tất cả conversation của môn học được chọn.
        
        Cache sẽ được làm mới mỗi khi môn học thay đổi để tránh giữ toàn bộ
        vector store của các môn khác trong RAM.
        """
        if self._active_subject_id == subject_id:
            return
        
        self.clear()
        self._active_subject_id = subject_id
        
        embedder = get_embedder()
        
        for conversation in conversations:
            meta = conversation.vector_store_meta
            
            if not meta or meta.status != "ready":
                continue
            
            if not (os.path.exists(meta.index_path) and os.path.exists(meta.meta_path)):
                continue
            
            try:
                retriever = create_retriever(
                    index_path=meta.index_path,
                    meta_path=meta.meta_path,
                    embedder=embedder,
                )
                self._cache[conversation.id] = retriever
            except Exception as exc:  # pragma: no cover - logging side-effect
                print(
                    f"⚠️  Không thể nạp vector store cho conversation {conversation.id}: {exc}"
                )
    
    def get_retriever(self, conversation_id: int) -> Optional[RAGRetriever]:
        """Lấy retriever từ cache (nếu tồn tại)."""
        return self._cache.get(conversation_id)
    
    def cache_retriever(
        self, subject_id: int, conversation_id: int, retriever: RAGRetriever
    ) -> None:
        """Lưu retriever vào cache nếu conversation thuộc môn học đang hoạt động."""
        if self._active_subject_id == subject_id:
            self._cache[conversation_id] = retriever


vector_store_cache = VectorStoreCache()