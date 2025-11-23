from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)


def load_document(file_path):
    """Tải một tài liệu duy nhất dựa trên đường dẫn."""
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        print(f"Định dạng file không được hỗ trợ: {file_path}")
        return []
    
    return loader.load()

def chunk_documents(docs, chunk_size=800, overlap=120):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    return splitter.split_documents(docs)