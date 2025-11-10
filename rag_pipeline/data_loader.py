from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)



def load_documents(folder_path=config['data']['raw']):
    docs = []
    for file in os.listdir(folder_path):
        path = os.path.join(folder_path, file)
        if file.endswith(".pdf"):
            loader = PyPDFLoader(path)
        elif file.endswith(".txt"):
            loader = TextLoader(path, encoding="utf-8")
        else:
            continue
        docs.extend(loader.load())
    return docs

def chunk_documents(docs, chunk_size=800, overlap=120):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    return splitter.split_documents(docs)