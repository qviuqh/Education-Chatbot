import os
import time
import streamlit as st
from rag_pipeline.data_loader import load_document, chunk_documents
from rag_pipeline.embedder import Embedder
from rag_pipeline.vector_store import VectorStore
from rag_pipeline.retriever import Retriever
from rag_pipeline.generator import generate_answer_stream
from rag_pipeline.prompt_builder import build_prompt
from rag_pipeline.reranker import Reranker

import tempfile
import json
import yaml


with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# --- Config ---
st.set_page_config(page_title="RAG Chat Local", layout="wide")
INDEX_PATH = config['data']['host']  # "./data/vectordb/index.faiss"
META_PATH = config['data']['chunks']  # "./data/vectordb/chunks.json"
model_name = config['models']['embedder']  #"intfloat/multilingual-e5-base"
llm_model = config['models']['generator']  #"qwen2:7b"

retriever_dict = {
    'semantic_threshold' : 0.3, 
    'bm25_threshold' : 1.0,
}

# --- Session ---
if "index_built" not in st.session_state:
    st.session_state.index_built = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Sidebar ---
st.sidebar.title("Cấu hình")
# model_name = st.sidebar.selectbox(
#     "Embedding model",
#     ["intfloat/multilingual-e5-base", "intfloat/multilingual-e5-small"],
#     index=0,
# )
# llm_model = st.sidebar.text_input("Local LLM (Ollama model)", value="qwen2:7b")
top_k = st.sidebar.slider("Top-k", 1, 5, 3, 1)

# --- Upload zone ---
st.title("StudyBot - Trợ lý học tập đa ngôn ngữ")
st.subheader("Tải tài liệu")
uploaded_files = st.file_uploader(
    "Tải lên nhiều file (.pdf, .txt)",
    type=["pdf", "txt"],
    accept_multiple_files=True,
)

if st.button("Xử lý & tạo chỉ mục"):
    if not uploaded_files:
        st.warning("Hãy tải lên ít nhất một tài liệu.")
    else:
        with st.spinner("Đang xử lý tài liệu..."):
            # Import hàm load mới
            tmp_dir = tempfile.mkdtemp()
            docs = [] # Khởi tạo danh sách docs

            for f in uploaded_files:
                temp_path = os.path.join(tmp_dir, f.name)
                with open(temp_path, "wb") as out:
                    out.write(f.read())

                # 1) Load từng file
                try:
                    docs.extend(load_document(temp_path))
                except Exception as e:
                    st.error(f"Lỗi khi tải file {f.name}: {e}")

            if not docs:
                st.warning("Không thể đọc bất kỳ tài liệu nào. Vui lòng kiểm tra lại định dạng file.")
                st.stop()

            # 2) Chunk (Hàm này giờ sẽ đọc config)
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
            st.success(f"Hoàn tất xử lý tài liệu!")

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
        # 1. KHỞI TẠO CÁC MODULES
        # (Bạn có thể cache các đối tượng này bằng @st.cache_resource để tăng tốc)
        retriever = Retriever(INDEX_PATH, META_PATH) # Đây là Hybrid Retriever mới
        reranker = Reranker() # Khởi tạo Reranker

        # 2. RETRIEVE (Hybrid)
        # Lấy số lượng lớn hơn (ví dụ k * 3) để Reranker có nhiều lựa chọn
        hybrid_k = top_k * 3 

        retriever_dict.update(**{'k_semantic': hybrid_k, 'k_keyword': hybrid_k})

        with st.spinner(f"Đang tìm kiếm các tài liệu liên quan..."):
            # Retriever mới sẽ tự động tìm semantic và keyword
            fused_contexts = retriever.retrieve_with_validation(query, **retriever_dict)

        if not fused_contexts:
            st.error("Không tìm thấy tài liệu nào.")
            st.stop() # Dừng xử lý nếu không có kết quả

        # 3. RERANK
        # Lọc lại k_final kết quả tốt nhất từ danh sách hợp nhất
        with st.spinner(f"Đã tìm thấy kết quả. Đang lọc và xếp hạng lại..."):
            print(f"Đã tìm thấy {len(fused_contexts)} kết quả. Đang lọc và xếp hạng lại...")
            # top_k là biến từ thanh slider
            reranked_contexts = reranker.rerank(query, fused_contexts, topn=top_k)

        # 4. BUILD PROMPT
        # Chỉ sử dụng các context tốt nhất sau khi đã rerank
        prompt = build_prompt(query, reranked_contexts)

        print("=== PROMPT ===")
        print(prompt)

        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.chat_history.append(("user", query))

        # 5. GENERATE (Streaming)
        with st.chat_message("assistant"):
            response = st.write_stream(generate_answer_stream(prompt, llm_model))

        st.session_state.chat_history.append(("assistant", response))

# query = st.chat_input("Nhập câu hỏi...")

# if query:
#     if not os.path.exists(INDEX_PATH):
#         st.warning("Bạn chưa tạo chỉ mục. Hãy tải tài liệu và bấm xử lý trước.")
#     else:
#         retriever = Retriever(INDEX_PATH, META_PATH)
#         reranker = Reranker()

#         retrieved_results = retriever.retrieve(query, k=top_k * 3) 
#         contexts_to_rerank = [t for _, t in retrieved_results]

#         reranked_contexts = reranker.rerank(query, contexts_to_rerank, topn=top_k)
#         prompt = build_prompt(query, reranked_contexts)

#         with st.chat_message("user"):
#             st.markdown(query)
#         st.session_state.chat_history.append(("user", query))

#         with st.chat_message("assistant"):
#             response = st.write_stream(generate_answer_stream(prompt, llm_model))
#         st.session_state.chat_history.append(("assistant", response))
