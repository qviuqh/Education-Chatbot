import os
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_document(file_path: str) -> List[Document]:
    """Tải một tài liệu duy nhất dựa trên đường dẫn."""
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        print(f"Định dạng file không được hỗ trợ: {file_path}")
        return []
    
    return loader.load()


def chunk_documents(docs: List[Document], chunk_size: int = 1000, overlap: int = 120) -> List[Document]:
    # sourcery skip: use-named-expression
    """Chia tài liệu thành các đoạn nhỏ kèm metadata hỗ trợ trích dẫn."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        add_start_index=True,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    
    chunks = splitter.split_documents(docs)
    enriched_chunks: List[Document] = []
    
    for idx, chunk in enumerate(chunks, start=1):
        metadata = chunk.metadata.copy() if chunk.metadata else {}
        metadata.update(
            {
                "chunk_id": idx,
                "page": metadata.get("page"),
                "source": metadata.get("source", "unknown"),
                "content_length": len(chunk.page_content),
                "start_index": metadata.get("start_index"),
            }
        )
        # Đảm bảo metadata lưu lại tên file rõ ràng để hiển thị citation
        source_path = metadata.get("source")
        if source_path:
            metadata["filename"] = os.path.basename(str(source_path))
        
        chunk.metadata = metadata
        enriched_chunks.append(chunk)
    
    return enriched_chunks