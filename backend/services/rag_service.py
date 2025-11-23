from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Generator, Optional

import models
from config import settings

# Import RAG components (bạn cần implement các file này)
# from rag_pipeline.data_loader import load_document, chunk_documents
# from rag_pipeline.embedder import Embedder
# from rag_pipeline.vector_store import VectorStore
# from rag_pipeline.pipeline import create_retriever, answer_question_with_store


def build_vector_store_for_conversation(
    db: Session,
    conversation_id: int
) -> None:
    """
    Xây dựng vector store cho conversation
    
    Steps:
    1. Load tất cả documents của conversation
    2. Chunk documents thành các đoạn nhỏ
    3. Embed các chunks
    4. Lưu vào FAISS index
    5. Cập nhật VectorStoreMeta
    """
    # Lấy conversation và metadata
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    vector_meta = conversation.vector_store_meta
    
    if not vector_meta:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vector store metadata not found"
        )
    
    try:
        # Cập nhật status
        vector_meta.status = "building"
        db.commit()
        
        # TODO: Implement RAG pipeline
        # Step 1: Load và chunk documents
        all_texts = []
        
        for conv_doc in conversation.documents:
            document = conv_doc.document
            
            # Load document
            # docs = load_document(document.filepath)
            # chunks = chunk_documents(docs, chunk_size=500, chunk_overlap=50)
            # all_texts.extend([chunk.page_content for chunk in chunks])
            
            # PLACEHOLDER: Bạn cần implement hàm load_document và chunk_documents
            pass
        
        # Step 2: Embed texts
        # embedder = Embedder(model_name=settings.EMBEDDING_MODEL)
        # embeddings = embedder.encode(all_texts, prefix="passage")
        
        # PLACEHOLDER: Bạn cần implement Embedder
        embeddings = None  # Replace this
        
        # Step 3: Create và save vector store
        # vector_store = VectorStore(
        #     dimension=settings.EMBEDDING_DIMENSION,
        #     index_path=vector_meta.index_path,
        #     meta_path=vector_meta.meta_path
        # )
        # vector_store.add(embeddings, all_texts)
        # vector_store.save()
        
        # PLACEHOLDER: Bạn cần implement VectorStore
        
        # Update metadata
        vector_meta.doc_count = len(all_texts) if all_texts else 0
        vector_meta.dimension = settings.EMBEDDING_DIMENSION
        vector_meta.status = "ready"
        vector_meta.error_message = None
        
        db.commit()
        
    except Exception as e:
        # Cập nhật lỗi
        vector_meta.status = "error"
        vector_meta.error_message = str(e)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build vector store: {str(e)}"
        )


def answer_question_for_conversation(
    db: Session,
    conversation_id: int,
    question: str,
    streaming: bool = False
) -> str | Generator[str, None, None]:
    """
    Trả lời câu hỏi cho conversation
    
    Returns:
        str nếu streaming=False
        Generator[str] nếu streaming=True
    """
    # Lấy conversation
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    vector_meta = conversation.vector_store_meta
    
    if not vector_meta or vector_meta.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vector store not ready. Please build it first."
        )
    
    try:
        # TODO: Implement RAG pipeline
        # retriever = create_retriever(
        #     index_path=vector_meta.index_path,
        #     meta_path=vector_meta.meta_path
        # )
        
        # answer = answer_question_with_store(
        #     question=question,
        #     retriever=retriever,
        #     streaming=streaming
        # )
        
        # PLACEHOLDER: Bạn cần implement pipeline
        answer = "This is a placeholder answer. Implement RAG pipeline to get real answers."
        
        return answer
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )


def get_vector_store_status(
    db: Session,
    conversation_id: int
) -> models.VectorStoreMeta:
    """
    Lấy trạng thái vector store
    """
    vector_meta = db.query(models.VectorStoreMeta).filter(
        models.VectorStoreMeta.conversation_id == conversation_id
    ).first()
    
    if not vector_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vector store not found"
        )
    
    return vector_meta
