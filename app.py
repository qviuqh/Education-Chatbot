import os
import time
import streamlit as st
from rag_pipeline.data_loader import load_documents, chunk_documents
from rag_pipeline.embedder import Embedder
from rag_pipeline.vector_store import VectorStore
from rag_pipeline.retriever import Retriever
from rag_pipeline.generator import generate_answer
from rag_pipeline.prompt_builder import build_prompt
from ollama import chat

import tempfile
import json
import yaml


with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# --- Config ---
st.set_page_config(page_title="RAG Chat Local", layout="wide")
INDEX_PATH = config['data']['host']  # "./data/vectordb/index.faiss"
META_PATH = config['data']['chunks']  # "./data/vectordb/chunks.json"

# --- Session ---
if "index_built" not in st.session_state:
    st.session_state.index_built = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Sidebar ---
st.sidebar.title("Cấu hình")
model_name = st.sidebar.selectbox(
    "Embedding model",
    ["intfloat/multilingual-e5-base", "intfloat/multilingual-e5-small"],
    index=0,
)
llm_model = st.sidebar.text_input("Local LLM (Ollama model)", value="qwen2:7b")
top_k = st.sidebar.slider("Top-k", 1, 15, 5, 1)

# --- Upload zone ---
st.title("RAG Chat App (Local, Multilingual)")
st.subheader("Tải tài liệu")
uploaded_files = st.file_uploader(
    "Tải lên nhiều file (.pdf, .txt, .md, .docx)",
    type=["pdf", "txt", "md", "docx"],
    accept_multiple_files=True,
)

if st.button("Xử lý & tạo chỉ mục"):
    if not uploaded_files:
        st.warning("Hãy tải lên ít nhất một tài liệu.")
    else:
        with st.spinner("Đang xử lý tài liệu..."):
            tmp_dir = tempfile.mkdtemp()
            paths = []
            for f in uploaded_files:
                temp_path = os.path.join(tmp_dir, f.name)
                with open(temp_path, "wb") as out:
                    out.write(f.read())
                paths.append(temp_path)

            # 1) Load
            docs = []
            for p in paths:
                docs.extend(load_documents(os.path.dirname(p)))

            # 2) Chunk
            chunks = chunk_documents(docs)
            texts = [c.page_content for c in chunks]

            # 3) Embedding
            embedder = Embedder(model_name)
            embs = embedder.encode(texts)

            # 4) Build FAISS
            store = VectorStore(embedder.model.get_sentence_embedding_dimension(), INDEX_PATH, META_PATH)
            store.add(embs, texts)
            store.save()

            st.session_state.index_built = True
            st.success(f"✅ Đã lập chỉ mục {len(texts)} đoạn văn.")

# --- Chat Interface ---
st.markdown("---")
st.subheader("Chat truy vấn")

for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)

query = st.chat_input("Nhập câu hỏi...")

if query:
    if not os.path.exists(INDEX_PATH):
        st.warning("Bạn chưa tạo chỉ mục. Hãy tải tài liệu và bấm xử lý trước.")
    else:
        retriever = Retriever(INDEX_PATH, META_PATH)
        results = retriever.retrieve(query, k=top_k)
        contexts = [t for _, t in results]
        prompt = build_prompt(query, contexts)

        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.chat_history.append(("user", query))

        with st.chat_message("assistant"):
            placeholder = st.empty()
            streamed_text = ""
            for chunk in chat(
                model=llm_model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=True
            ):
                token = chunk['message']['content']
                streamed_text += token
                placeholder.markdown(f"🤖 {streamed_text}▌")
                time.sleep(0.01)
            placeholder.markdown(f"🤖 {streamed_text}")
            answer = streamed_text

        # with st.chat_message("assistant"):
        #     st.markdown("_Đang tạo câu trả lời..._")
        #     answer = generate_answer(prompt, model=llm_model)
        #     st.markdown(answer)
        st.session_state.chat_history.append(("assistant", answer))
