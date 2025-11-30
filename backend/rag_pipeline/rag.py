"""
RAG Pipeline - Kết nối các components thành pipeline hoàn chỉnh
"""
from typing import Generator, List, Dict, Any, Optional
from ..config import settings
from ..ai_deps import get_embedder, get_reranker

# Import các components
from .embedder import Embedder
from .vector_store import VectorStore
from .retriever import Retriever
from .generator import generate_answer, generate_answer_stream
from .language_detector import LanguageDetector
from .prompt_builder import build_prompt
from .reranker import Reranker


class RAGRetriever:
    """
    Wrapper class cho Retriever để sử dụng trong pipeline
    """
    def __init__(self, index_path: str, meta_path: str, embedder: Embedder = None):
        """
        Initialize retriever với saved vector store
        
        Args:
            index_path: Đường dẫn file .index (FAISS)
            meta_path: Đường dẫn file .json (text chunks)
            embedder: Embedder instance (optional, sẽ tạo mới nếu None)
        """
        self.index_path = index_path
        self.meta_path = meta_path
        
        # Khởi tạo embedder nếu chưa có
        if embedder is None:
            self.embedder = get_embedder()
        else:
            self.embedder = embedder
        
        # Khởi tạo retriever với embedder và store
        self.retriever = Retriever(
            store_path=index_path,
            meta_path=meta_path,
            embedder=self.embedder
        )
        
        print(f"✅ Retriever initialized with {len(self.retriever.store.documents)} chunks")
    
    @staticmethod
    def _format_context(doc: Dict[str, Any]) -> str:
        metadata = doc.get("metadata", {})
        source_parts = []
        
        filename = metadata.get("filename")
        if filename:
            source_parts.append(f"Source: {filename}")
        elif metadata.get("source"):
            source_parts.append(f"Source: {metadata.get('source')}")
        
        page = metadata.get("page")
        if page is not None:
            source_parts.append(f"Page: {page}")
        
        chunk_id = metadata.get("chunk_unique_id") or metadata.get("chunk_id")
        if chunk_id:
            source_parts.append(f"Chunk: {chunk_id}")
        
        meta_line = " | ".join(source_parts) if source_parts else "Source: unknown"
        return f"[{meta_line}]\n{doc.get('text', '')}"
    
    def retrieve(
        self, 
        question: str, 
        k_semantic: int = None,
        k_keyword: int = None,
        use_validation: bool = True,
        allowed_document_ids: Optional[set[int]] = None
    ) -> Optional[List[str]]:
        """
        Retrieve relevant contexts cho câu hỏi
        
        Args:
            question: Câu hỏi của user
            k_semantic: Số lượng contexts từ semantic search
            k_keyword: Số lượng contexts từ keyword search
            use_validation: Có validate relevance không
            
        Returns:
            List[str]: Danh sách text contexts, hoặc None nếu không tìm thấy
        """
        if k_semantic is None:
            k_semantic = settings.TOP_K_RETRIEVE
        
        if k_keyword is None:
            k_keyword = settings.TOP_K_RETRIEVE
        
        try:
            if use_validation:
                # Dùng retrieve_with_validation - trả về None nếu không relevant
                contexts = self.retriever.retrieve_with_validation(
                    query=question,
                    k_semantic=k_semantic,
                    k_keyword=k_keyword,
                    semantic_threshold=settings.SIMILARITY_THRESHOLD,
                    bm25_threshold=settings.BM25_THRESHOLD,
                    min_results=1,
                    bm25_min_top1=1.0
                )
            else:
                # Retrieve bình thường
                contexts, is_relevant = self.retriever.retrieve(
                    query=question,
                    k_semantic=k_semantic,
                    k_keyword=k_keyword,
                    semantic_threshold=settings.SIMILARITY_THRESHOLD,
                    bm25_threshold=settings.BM25_THRESHOLD,
                    min_results=1,
                    bm25_min_top1=1.0
                )
                if not is_relevant:
                    contexts = None
            
            if contexts:
                if allowed_document_ids is not None:
                    contexts = [
                        doc
                        for doc in contexts
                        if doc.get("metadata", {}).get("document_id") in allowed_document_ids
                    ]
            
            if contexts:
                contexts = [self._format_context(doc) for doc in contexts]
            
            return contexts
            
        except Exception as e:
            print(f"❌ Error in retrieval: {e}")
            return None


def create_retriever(index_path: str, meta_path: str, embedder: Embedder = None) -> RAGRetriever:
    """
    Factory function để tạo Retriever
    
    Args:
        index_path: Đường dẫn file .index
        meta_path: Đường dẫn file .json
        embedder: Embedder instance (optional)
        
    Returns:
        RAGRetriever instance
    """
    return RAGRetriever(index_path, meta_path, embedder)


def answer_question_with_store(
    question: str,
    retriever: RAGRetriever,
    streaming: bool = False,
    use_reranker: bool = False,
    reranker_top_k: int = 3,
    detect_language: bool = True,
    model: str = None,
    temperature: float = None,
    allowed_document_ids: Optional[set[int]] = None
) -> str | Generator[str, None, None]:
    """
    RAG Pipeline hoàn chỉnh: Retrieve + Generate
    
    Args:
        question: Câu hỏi của user
        retriever: RAGRetriever instance
        streaming: True nếu muốn stream response
        use_reranker: Có dùng reranker không
        reranker_top_k: Số contexts sau rerank
        detect_language: Có tự động detect ngôn ngữ không
        model: LLM model name (override config)
        temperature: Temperature cho generation (override config)
        
    Returns:
        str nếu streaming=False
        Generator[str] nếu streaming=True
    """
    print(f"\n{'='*60}")
    print(f"📝 Question: {question}")
    print(f"{'='*60}\n")
    
    # Step 1: Retrieve contexts
    print("🔍 Step 1: Retrieving contexts...")
    contexts = retriever.retrieve(
        question=question,
        k_semantic=settings.TOP_K_RETRIEVE,
        k_keyword=settings.TOP_K_RETRIEVE,
        use_validation=True,
        allowed_document_ids=allowed_document_ids
    )
    
    # Kiểm tra contexts
    if not contexts or len(contexts) == 0:
        print("⚠️  No relevant contexts found")
        no_context_answer = (
            "Xin lỗi, tôi không tìm thấy thông tin liên quan trong tài liệu "
            "để trả lời câu hỏi này. Vui lòng thử hỏi theo cách khác hoặc "
            "kiểm tra lại tài liệu đã upload."
        )
        
        if streaming:
            def no_context_generator():
                for char in no_context_answer:
                    yield char
            return no_context_generator()
        else:
            return no_context_answer
    
    print(f"✅ Found {len(contexts)} contexts")
    
    # Step 2: Rerank contexts (optional)
    if use_reranker and len(contexts) > reranker_top_k:
        print(f"\n🎯 Step 2: Reranking contexts (top {reranker_top_k})...")
        try:
            reranker = get_reranker()
            contexts = reranker.rerank(
                query=question,
                candidates=contexts,
                topn=reranker_top_k,
                score_threshold=0.3,
                return_scores=False
            )
            print(f"✅ Reranked to {len(contexts)} contexts")
        except Exception as e:
            print(f"⚠️  Reranking failed: {e}. Using original contexts.")
    else:
        print(f"\n⏭️  Step 2: Skipping reranker")
    
    # Step 3: Detect language
    language = "Vietnamese"  # Default
    if detect_language:
        print(f"\n🌍 Step 3: Detecting language...")
        try:
            detector = LanguageDetector()
            language = detector.detect(question)
            print(f"✅ Detected language: {language}")
        except Exception as e:
            print(f"⚠️  Language detection failed: {e}. Using default: Vietnamese")
    else:
        print(f"\n⏭️  Step 3: Using default language: Vietnamese")
    
    # Step 4: Build prompt
    print(f"\n📋 Step 4: Building prompt...")
    prompt = build_prompt(
        question=question,
        contexts=contexts,
        language=language
    )
    print(f"✅ Prompt built ({len(prompt)} chars)")
    
    # Step 5: Generate answer
    target_model = model or settings.LLM_MODEL
    
    print(f"\n🤖 Step 5: Generating answer...")
    print(f"   Model: {target_model}")
    print(f"   Streaming: {streaming}")
    
    try:
        if streaming:
            print("✅ Streaming response started\n")
            # Luôn truyền target_model vào hàm
            return generate_answer_stream(
                prompt, 
                model=target_model, 
                temperature=temperature or settings.GENERATOR_TEMPERATURE
            )
        else:
            # Luôn truyền target_model vào hàm
            answer = generate_answer(
                prompt, 
                model=target_model
            )
            print(f"✅ Answer generated ({len(answer)} chars)\n")
            return answer
            
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        error_message = (
            "Xin lỗi, đã có lỗi xảy ra khi tạo câu trả lời. "
            "Vui lòng thử lại sau."
        )
        
        if streaming:
            def error_generator():
                yield error_message
            return error_generator()
        else:
            return error_message


def answer_question_simple(
    question: str,
    retriever: RAGRetriever,
    streaming: bool = False
) -> str | Generator[str, None, None]:
    """
    Simplified RAG pipeline - không dùng reranker, language detection đơn giản
    
    Args:
        question: Câu hỏi của user
        retriever: RAGRetriever instance
        streaming: True nếu muốn stream response
        
    Returns:
        str nếu streaming=False
        Generator[str] nếu streaming=True
    """
    return answer_question_with_store(
        question=question,
        retriever=retriever,
        streaming=streaming,
        use_reranker=False,
        detect_language=True
    )


def answer_question_advanced(
    question: str,
    retriever: RAGRetriever,
    streaming: bool = False,
    reranker_top_k: int = 3
) -> str | Generator[str, None, None]:
    """
    Advanced RAG pipeline - có reranker và language detection
    
    Args:
        question: Câu hỏi của user
        retriever: RAGRetriever instance
        streaming: True nếu muốn stream response
        reranker_top_k: Số contexts sau rerank
        
    Returns:
        str nếu streaming=False
        Generator[str] nếu streaming=True
    """
    return answer_question_with_store(
        question=question,
        retriever=retriever,
        streaming=streaming,
        use_reranker=True,
        reranker_top_k=reranker_top_k,
        detect_language=True
    )


# Utility functions
def format_contexts_for_display(contexts: List[str], max_length: int = 200) -> List[str]:
    """
    Format contexts để hiển thị (truncate nếu quá dài)
    
    Args:
        contexts: Danh sách contexts
        max_length: Độ dài tối đa mỗi context
        
    Returns:
        List contexts đã format
    """
    formatted = []
    for i, ctx in enumerate(contexts, 1):
        if len(ctx) > max_length:
            ctx_display = ctx[:max_length] + "..."
        else:
            ctx_display = ctx
        formatted.append(f"[Context {i}]: {ctx_display}")
    
    return formatted


def get_context_sources(contexts: List[str]) -> Dict[str, Any]:
    """
    Trích xuất thông tin nguồn từ contexts (nếu có)
    
    Args:
        contexts: Danh sách contexts
        
    Returns:
        Dict chứa thông tin sources
    """
    return {
        "total_contexts": len(contexts),
        "total_chars": sum(len(c) for c in contexts),
        "avg_length": sum(len(c) for c in contexts) / len(contexts) if contexts else 0
    }


def validate_retriever_setup(index_path: str, meta_path: str) -> bool:
    """
    Kiểm tra xem retriever có thể được khởi tạo không
    
    Args:
        index_path: Đường dẫn file .index
        meta_path: Đường dẫn file .json
        
    Returns:
        True nếu hợp lệ, False nếu không
    """
    import os
    
    if not os.path.exists(index_path):
        print(f"❌ Index file not found: {index_path}")
        return False
    
    if not os.path.exists(meta_path):
        print(f"❌ Meta file not found: {meta_path}")
        return False
    
    try:
        # Thử load để kiểm tra
        retriever = create_retriever(index_path, meta_path)
        print("✅ Retriever validation successful")
        return True
    except Exception as e:
        print(f"❌ Retriever validation failed: {e}")
        return False