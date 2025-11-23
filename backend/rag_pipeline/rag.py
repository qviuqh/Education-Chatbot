"""
RAG Pipeline - Kết nối các components thành pipeline hoàn chỉnh
"""
from typing import Generator, List, Dict, Any
from config import settings

# Import các components (cần implement)
# from .embedder import Embedder
# from .vector_store import VectorStore
# from .retriever import Retriever
# from .generator import Generator
# from .language_detector import LanguageDetector
# from .prompt_builder import PromptBuilder
# from .reranker import Reranker


class Retriever:
    """
    Retriever sử dụng Vector Store để tìm kiếm context
    """
    def __init__(self, index_path: str, meta_path: str):
        """
        Initialize retriever với saved vector store
        
        Args:
            index_path: Đường dẫn file .index (FAISS)
            meta_path: Đường dẫn file .json (text chunks)
        """
        self.index_path = index_path
        self.meta_path = meta_path
        
        # TODO: Load embedder
        # self.embedder = Embedder(model_name=settings.EMBEDDING_MODEL)
        
        # TODO: Load vector store
        # self.vector_store = VectorStore.load(index_path, meta_path)
        pass
    
    def retrieve(self, question: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant contexts cho câu hỏi
        
        Args:
            question: Câu hỏi của user
            top_k: Số lượng contexts cần lấy
            
        Returns:
            List[Dict]: Danh sách contexts với score
                [{"text": "...", "score": 0.85}, ...]
        """
        if top_k is None:
            top_k = settings.TOP_K_RETRIEVE
        
        # TODO: Implement retrieval
        # 1. Embed câu hỏi
        # query_embedding = self.embedder.encode([question], prefix="query")[0]
        
        # 2. Search trong vector store
        # results = self.vector_store.search(query_embedding, top_k=top_k)
        
        # 3. Filter theo threshold
        # contexts = [
        #     {"text": r["text"], "score": r["score"]}
        #     for r in results
        #     if r["score"] >= settings.SIMILARITY_THRESHOLD
        # ]
        
        # PLACEHOLDER
        contexts = [
            {"text": "This is a placeholder context.", "score": 0.9}
        ]
        
        return contexts


def create_retriever(index_path: str, meta_path: str) -> Retriever:
    """
    Factory function để tạo Retriever
    """
    return Retriever(index_path, meta_path)


def answer_question_with_store(
    question: str,
    retriever: Retriever,
    streaming: bool = False
) -> str | Generator[str, None, None]:
    """
    RAG Pipeline hoàn chỉnh: Retrieve + Generate
    
    Args:
        question: Câu hỏi của user
        retriever: Retriever instance
        streaming: True nếu muốn stream response
        
    Returns:
        str nếu streaming=False
        Generator[str] nếu streaming=True
    """
    # Step 1: Retrieve contexts
    contexts = retriever.retrieve(question)
    
    if not contexts:
        no_context_answer = "Xin lỗi, tôi không tìm thấy thông tin liên quan trong tài liệu để trả lời câu hỏi này."
        
        if streaming:
            def no_context_generator():
                yield no_context_answer
            return no_context_generator()
        else:
            return no_context_answer
    
    # Step 2: Detect language (optional)
    # TODO: Implement language detection
    # language_detector = LanguageDetector()
    # language = language_detector.detect(question)
    language = "vi"  # Default Vietnamese
    
    # Step 3: Build prompt
    # TODO: Implement prompt builder
    # prompt_builder = PromptBuilder()
    # prompt = prompt_builder.build(
    #     question=question,
    #     contexts=contexts,
    #     language=language
    # )
    
    # PLACEHOLDER prompt
    context_text = "\n\n".join([c["text"] for c in contexts])
    prompt = f"""Dựa trên thông tin sau:

{context_text}

Câu hỏi: {question}

Hãy trả lời câu hỏi dựa trên thông tin được cung cấp. Nếu không tìm thấy thông tin liên quan, hãy nói "Tôi không tìm thấy thông tin để trả lời câu hỏi này trong tài liệu."
"""
    
    # Step 4: Generate answer
    # TODO: Implement generator
    # generator = Generator(model_name=settings.LLM_MODEL)
    
    if streaming:
        # TODO: Implement streaming generation
        # return generator.generate_stream(prompt)
        
        # PLACEHOLDER streaming
        def placeholder_stream():
            answer = "Đây là câu trả lời mẫu. Bạn cần implement Generator để có câu trả lời thực."
            for char in answer:
                yield char
        
        return placeholder_stream()
    else:
        # TODO: Implement normal generation
        # answer = generator.generate(prompt)
        
        # PLACEHOLDER
        answer = "Đây là câu trả lời mẫu. Bạn cần implement Generator để có câu trả lời thực."
        
        return answer


def answer_question_with_reranking(
    question: str,
    retriever: Retriever,
    streaming: bool = False,
    use_reranker: bool = True
) -> str | Generator[str, None, None]:
    """
    Advanced RAG với reranking
    
    Similar to answer_question_with_store nhưng có thêm bước rerank
    """
    # Step 1: Retrieve nhiều contexts hơn
    contexts = retriever.retrieve(question, top_k=settings.TOP_K_RETRIEVE * 2)
    
    if not contexts:
        return answer_question_with_store(question, retriever, streaming)
    
    # Step 2: Rerank contexts (optional)
    if use_reranker and len(contexts) > settings.TOP_K_RETRIEVE:
        # TODO: Implement reranker
        # reranker = Reranker()
        # contexts = reranker.rerank(question, contexts, top_k=settings.TOP_K_RETRIEVE)
        
        # PLACEHOLDER: Chỉ lấy top k
        contexts = contexts[:settings.TOP_K_RETRIEVE]
    
    # Step 3-4: Giống answer_question_with_store
    # ... (rest similar to above)
    
    return answer_question_with_store(question, retriever, streaming)


# Utility functions
def format_contexts(contexts: List[Dict[str, Any]]) -> str:
    """
    Format contexts thành string để đưa vào prompt
    """
    formatted = []
    for i, ctx in enumerate(contexts, 1):
        formatted.append(f"[Đoạn {i}]:\n{ctx['text']}\n")
    
    return "\n".join(formatted)


def get_source_info(contexts: List[Dict[str, Any]]) -> List[str]:
    """
    Lấy thông tin nguồn từ contexts (nếu có)
    """
    sources = []
    for ctx in contexts:
        if "source" in ctx:
            sources.append(ctx["source"])
    
    return list(set(sources))  # Remove duplicates
