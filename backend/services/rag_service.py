"""
RAG Service - Orchestration RAG: build index, answer question
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Generator, Optional, Iterable
import os

from .. import models
from ..config import settings

# Import RAG components
from ..rag_pipeline.data_loader import load_document, chunk_documents
from ..rag_pipeline.embedder import Embedder
from ..rag_pipeline.vector_store import VectorStore
from ..ai_deps import get_embedder
from ..rag_pipeline.rag import (
    create_retriever, 
    answer_question_with_store,
    validate_retriever_setup
)
from .vector_store_cache import vector_store_cache
from .vector_paths import get_vector_paths


def _ensure_subject_vector_meta(db: Session, subject: models.Subject) -> models.VectorStoreMeta:
    """Lấy hoặc tạo metadata cho vector store của một môn học."""

    if subject.vector_store_meta:
        return subject.vector_store_meta

    index_path, meta_path = get_vector_paths(subject.user_id, subject.id)
    vector_meta = models.VectorStoreMeta(
        subject_id=subject.id,
        index_path=index_path,
        meta_path=meta_path,
        dimension=settings.EMBEDDING_DIMENSION,
        status="empty",
    )

    db.add(vector_meta)
    db.commit()
    db.refresh(vector_meta)

    return vector_meta


def get_subject_vector_meta(db: Session, subject_id: int) -> models.VectorStoreMeta:
    """Lấy metadata vector store cho subject theo ID."""

    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    return _ensure_subject_vector_meta(db, subject)

def build_vector_store_for_subject(
    db: Session,
    subject_id: int,
    document_filter: Optional[Iterable[int]] = None
) -> None:  # sourcery skip: extract-method
    """
    Xây dựng vector store cho Môn học
    
    Steps:
    1. Load tất cả documents của môn học (có thể filter theo danh sách cho phép)
    2. Chunk documents
    3. Embed chunks
    4. Lưu vào FAISS index
    5. Cập nhật VectorStoreMeta
    """
    print(f"\n{'='*60}")
    print(f"🚀 Building vector store for subject {subject_id}")
    print(f"{'='*60}\n")
    
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    vector_meta = _ensure_subject_vector_meta(db, subject)
    
    try:
        # Cập nhật status
        vector_meta.status = "building"
        db.commit()
        print("📝 Status: building")
        
        # Step 1: Load và chunk documents
        print("\n📚 Step 1: Loading and chunking documents...")
        all_chunks = []
        doc_count = 0
        
        documents = subject.documents
        if document_filter:
            allowed_ids = set(document_filter)
            documents = [doc for doc in documents if doc.id in allowed_ids]
        
        for document in documents:
            # Kiểm tra file tồn tại
            if not os.path.exists(document.filepath):
                print(f"⚠️  File not found: {document.filepath}")
                continue
            
            print(f"  📄 Loading: {document.filename}")
            
            try:
                # Load document
                docs = load_document(document.filepath)
                print(f"     ✅ Loaded {len(docs)} pages")
                
                # Chunk documents
                chunks = chunk_documents(
                    docs, 
                    chunk_size=800,  # Có thể config
                    overlap=120
                )
                print(f"     ✅ Created {len(chunks)} chunks")
                
                # Extract text từ chunks
                for chunk in chunks:
                    metadata = chunk.metadata.copy() if chunk.metadata else {}
                    unique_chunk_id = f"{document.id}-{metadata.get('chunk_id', len(all_chunks)+1)}"
                    metadata.update(
                        {
                            "chunk_unique_id": unique_chunk_id,
                            "document_id": document.id,
                            "subject_id": document.subject_id,
                            "source": str(document.filepath),
                            "filename": document.filename,
                        }
                    )
                    chunk.metadata = metadata
                    
                    all_chunks.append(
                        {
                            "text": chunk.page_content,
                            "metadata": metadata,
                        }
                    )
                    
                doc_count += 1
                
            except Exception as e:
                print(f"     ❌ Error loading document: {e}")
                continue
        
        if not all_chunks:
            raise Exception("No texts extracted from documents")
        
        print(f"\n✅ Total: {len(all_chunks)} chunks from {doc_count} documents")
        
        # Step 2: Embed texts
        print(f"\n🔢 Step 2: Embedding texts...")
        embedder = get_embedder()
        print(f"  Model: {settings.EMBEDDING_MODEL}")
        
        texts_for_embedding = [chunk["text"] for chunk in all_chunks]
        embeddings = embedder.encode(texts_for_embedding, prefix="passage")
        print(f"  ✅ Created embeddings: shape {embeddings.shape}")
        
        # Step 3: Create và save vector store
        print(f"\n💾 Step 3: Creating vector store...")
        vector_store = VectorStore(
            dim=embedder.model.get_sentence_embedding_dimension(),
            path=vector_meta.index_path,
            meta_path=vector_meta.meta_path
        )
        
        print(f"  Index path: {vector_meta.index_path}")
        print(f"  Meta path: {vector_meta.meta_path}")
        
        vector_store.add(embeddings, all_chunks)
        vector_store.save()
        print("  ✅ Vector store saved")
        
        # Step 4: Update metadata
        vector_meta.doc_count = len(all_chunks)
        vector_meta.dimension = embedder.model.get_sentence_embedding_dimension()
        vector_meta.status = "ready"
        vector_meta.error_message = None
        
        db.commit()
        
        print(f"\n{'='*60}")
        print("✅ Vector store built successfully!")
        print(f"   - Chunks: {len(all_chunks)}")
        print(f"   - Dimension: {embedder.model.get_sentence_embedding_dimension()}")
        print("   - Status: ready")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"{'='*60}")
        print(f"❌ Error building vector store: {e}")
        print(f"{'='*60}\n")
        
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
    streaming: bool = False,
    use_reranker: bool = False
) -> str | Generator[str, None, None]:
    """
    Trả lời câu hỏi cho conversation
    
    Args:
        db: Database session
        conversation_id: ID của conversation
        question: Câu hỏi của user
        streaming: True để stream response
        use_reranker: True để dùng reranker
        
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
    
    vector_meta = _ensure_subject_vector_meta(db, conversation.subject)
    
    # Kiểm tra vector store
    if vector_meta.status == "empty":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vector store is empty. Please build it first."
        )
    
    if vector_meta.status == "building":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vector store is being built. Please wait."
        )
    
    if vector_meta.status == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vector store build failed: {vector_meta.error_message}"
        )
    
    if vector_meta.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vector store is not ready. Current status: {vector_meta.status}"
        )
    
    # Kiểm tra files tồn tại
    if not os.path.exists(vector_meta.index_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vector store index file not found"
        )
    
    if not os.path.exists(vector_meta.meta_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vector store meta file not found"
        )
    
    try:
        # Lấy retriever từ cache theo môn học
        retriever = vector_store_cache.get_retriever(conversation.subject_id)
        
        if retriever is None:
            retriever = create_retriever(
                index_path=vector_meta.index_path,
                meta_path=vector_meta.meta_path
            )
            
            vector_store_cache.cache_retriever(
                subject_id=conversation.subject_id,
                retriever=retriever,
            )
        
        allowed_doc_ids = {
            conv_doc.document_id for conv_doc in conversation.documents
        }
        
        # Gọi RAG pipeline
        answer = answer_question_with_store(
            question=question,
            retriever=retriever,
            streaming=streaming,
            use_reranker=use_reranker,
            reranker_top_k=3,
            detect_language=True,
            allowed_document_ids=allowed_doc_ids or None
        )
        
        return answer
        
    except Exception as e:
        print(f"❌ Error answering question: {e}")
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
    
    Args:
        db: Database session
        conversation_id: ID của conversation
        
    Returns:
        VectorStoreMeta instance
    """
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    vector_meta = _ensure_subject_vector_meta(db, conversation.subject)
    
    return vector_meta


def rebuild_vector_store_for_conversation(
    db: Session,
    conversation_id: int
) -> None:
    """
    Rebuild vector store cho conversation (xóa cũ và tạo mới)
    
    Args:
        db: Database session
        conversation_id: ID của conversation
    """
    print(f"\n🔄 Rebuilding vector store for conversation {conversation_id}")
    
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    vector_meta = _ensure_subject_vector_meta(db, conversation.subject)
    
    # Xóa files cũ nếu có
    try:
        if os.path.exists(vector_meta.index_path):
            os.remove(vector_meta.index_path)
            print("  ✅ Deleted old index file")
        
        if os.path.exists(vector_meta.meta_path):
            os.remove(vector_meta.meta_path)
            print("  ✅ Deleted old meta file")
    except Exception as e:
        print(f"  ⚠️  Error deleting old files: {e}")
    
    # Reset status
    vector_meta.status = "empty"
    vector_meta.doc_count = 0
    vector_meta.error_message = None
    db.commit()
    
    # Build lại
    build_vector_store_for_subject(db, conversation.subject_id)


def validate_conversation_vector_store(
    db: Session,
    conversation_id: int
) -> dict:
    """
    Validate vector store của conversation
    
    Args:
        db: Database session
        conversation_id: ID của conversation
        
    Returns:
        Dict chứa thông tin validation
    """
    vector_meta = get_vector_store_status(db, conversation_id)
    
    validation = {
        "conversation_id": conversation_id,
        "subject_id": vector_meta.subject_id,
        "status": vector_meta.status,
        "doc_count": vector_meta.doc_count,
        "dimension": vector_meta.dimension,
        "files_exist": {
            "index": os.path.exists(vector_meta.index_path),
            "meta": os.path.exists(vector_meta.meta_path)
        },
        "is_ready": False,
        "errors": []
    }
    
    # Kiểm tra status
    if vector_meta.status != "ready":
        validation["errors"].append(f"Status is {vector_meta.status}, not ready")
    
    # Kiểm tra files
    if not validation["files_exist"]["index"]:
        validation["errors"].append("Index file not found")
    
    if not validation["files_exist"]["meta"]:
        validation["errors"].append("Meta file not found")
    
    # Kiểm tra doc count
    if vector_meta.doc_count == 0:
        validation["errors"].append("No documents indexed")
    
    # Tổng kết
    validation["is_ready"] = (
        vector_meta.status == "ready" and
        validation["files_exist"]["index"] and
        validation["files_exist"]["meta"] and
        vector_meta.doc_count > 0
    )
    
    return validation