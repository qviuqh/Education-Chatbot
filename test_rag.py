"""
Test script cho RAG Pipeline
Chạy: python test_rag_pipeline.py
"""

import os
import yaml
from rag_pipeline.data_loader import load_documents, chunk_documents
from rag_pipeline.embedder import Embedder
from rag_pipeline.vector_store import VectorStore
from rag_pipeline.retriever import Retriever
from rag_pipeline.generator import generate_answer
from rag_pipeline.prompt_builder import build_prompt


def print_section(title):
    """In tiêu đề section"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_config():
    """Test 1: Kiểm tra config"""
    print_section("TEST 1: Kiểm tra Config")
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        print("✅ Config loaded successfully")
        print(f"   - Index path: {config['data']['host']}")
        print(f"   - Meta path: {config['data']['chunks']}")
        return config
    except Exception as e:
        print(f"❌ Lỗi khi load config: {e}")
        return None


def test_load_documents(doc_dir):
    """Test 2: Load documents"""
    print_section("TEST 2: Load Documents")
    try:
        docs = load_documents(doc_dir)
        print(f"✅ Loaded {len(docs)} documents")
        if docs:
            print(f"   - Document đầu tiên: {docs[0].metadata}")
            print(f"   - Preview: {docs[0].page_content[:200]}...")
        return docs
    except Exception as e:
        print(f"❌ Lỗi khi load documents: {e}")
        return None


def test_chunk_documents(docs):
    """Test 3: Chunk documents"""
    print_section("TEST 3: Chunk Documents")
    try:
        chunks = chunk_documents(docs)
        texts = [c.page_content for c in chunks]
        print(f"✅ Created {len(chunks)} chunks")
        if chunks:
            print(f"   - Chunk đầu tiên length: {len(texts[0])} chars")
            print(f"   - Preview: {texts[0][:150]}...")
        return texts, chunks
    except Exception as e:
        print(f"❌ Lỗi khi chunk documents: {e}")
        return None, None


def test_embedder(model_name, texts):
    """Test 4: Create embeddings"""
    print_section("TEST 4: Create Embeddings")
    try:
        embedder = Embedder(model_name)
        print(f"   - Model: {model_name}")
        print(f"   - Embedding dimension: {embedder.model.get_sentence_embedding_dimension()}")
        
        # Test với một vài texts
        test_texts = texts[:min(3, len(texts))]
        embs = embedder.encode(test_texts)
        print(f"✅ Created embeddings for {len(test_texts)} texts")
        print(f"   - Embedding shape: {embs.shape}")
        return embedder, embs
    except Exception as e:
        print(f"❌ Lỗi khi create embeddings: {e}")
        return None, None


def test_vector_store(embedder, texts, index_path, meta_path):
    """Test 5: Build vector store"""
    print_section("TEST 5: Build Vector Store")
    try:
        dim = embedder.model.get_sentence_embedding_dimension()
        store = VectorStore(dim, index_path, meta_path)
        
        # Encode all texts
        embs = embedder.encode(texts)
        store.add(embs, texts)
        store.save()
        
        print(f"✅ Vector store created successfully")
        print(f"   - Index saved to: {index_path}")
        print(f"   - Meta saved to: {meta_path}")
        print(f"   - Total vectors: {len(texts)}")
        return store
    except Exception as e:
        print(f"❌ Lỗi khi build vector store: {e}")
        return None


def test_retriever(query, index_path, meta_path, top_k=5):
    """Test 6: Test retrieval"""
    print_section("TEST 6: Test Retrieval")
    try:
        retriever = Retriever(index_path, meta_path)
        results = retriever.retrieve(query, k=top_k)
        
        print(f"✅ Retrieved {len(results)} results for query: '{query}'")
        for i, (score, text) in enumerate(results, 1):
            print(f"\n   Result {i} (score: {score:.4f}):")
            print(f"   {text[:200]}...")
        
        return results
    except Exception as e:
        print(f"❌ Lỗi khi retrieve: {e}")
        return None


def test_prompt_builder(query, contexts):
    """Test 7: Build prompt"""
    print_section("TEST 7: Build Prompt")
    try:
        prompt = build_prompt(query, contexts)
        print(f"✅ Prompt built successfully")
        print(f"   - Prompt length: {len(prompt)} chars")
        print(f"\n   Preview:")
        print(f"   {prompt[:300]}...")
        return prompt
    except Exception as e:
        print(f"❌ Lỗi khi build prompt: {e}")
        return None


def test_generator(prompt, model="qwen2:7b"):
    """Test 8: Generate answer"""
    print_section("TEST 8: Generate Answer")
    try:
        print(f"   - Using model: {model}")
        print(f"   - Đang generate (có thể mất vài giây)...")
        answer = generate_answer(prompt, model=model)
        print(f"✅ Answer generated successfully")
        print(f"\n   Answer:")
        print(f"   {answer}")
        return answer
    except Exception as e:
        print(f"❌ Lỗi khi generate answer: {e}")
        return None


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("  RAG PIPELINE TEST SUITE")
    print("="*60)
    
    # Configuration
    DOC_DIR = "./data/documents"  # Thay đổi path này
    MODEL_NAME = "intfloat/multilingual-e5-base"
    LLM_MODEL = "qwen2:7b"
    TEST_QUERY = "Nội dung chính của tài liệu là gì?"  # Thay đổi câu hỏi
    TOP_K = 3
    
    # Test 1: Config
    config = test_config()
    if not config:
        return
    
    INDEX_PATH = config['data']['host']
    META_PATH = config['data']['chunks']
    
    # Test 2: Load documents
    print(f"\n📁 Document directory: {DOC_DIR}")
    if not os.path.exists(DOC_DIR):
        print(f"⚠️  Directory không tồn tại: {DOC_DIR}")
        print(f"   Hãy tạo folder và thêm file test vào đó")
        return
    
    docs = test_load_documents(DOC_DIR)
    if not docs:
        return
    
    # Test 3: Chunk
    texts, chunks = test_chunk_documents(docs)
    if not texts:
        return
    
    # Test 4: Embeddings
    embedder, sample_embs = test_embedder(MODEL_NAME, texts)
    if not embedder:
        return
    
    # Test 5: Vector Store
    store = test_vector_store(embedder, texts, INDEX_PATH, META_PATH)
    if not store:
        return
    
    # Test 6: Retrieval
    results = test_retriever(TEST_QUERY, INDEX_PATH, META_PATH, TOP_K)
    if not results:
        return
    
    contexts = [text for _, text in results]
    
    # Test 7: Prompt
    prompt = test_prompt_builder(TEST_QUERY, contexts)
    if not prompt:
        return
    
    # Test 8: Generation
    answer = test_generator(prompt, LLM_MODEL)
    
    # Summary
    print_section("SUMMARY")
    print("✅ All tests completed!")
    print(f"   - Documents loaded: {len(docs)}")
    print(f"   - Chunks created: {len(texts)}")
    print(f"   - Index built: {INDEX_PATH}")
    print(f"   - Query tested: {TEST_QUERY}")
    print(f"   - Answer generated: {'Yes' if answer else 'No'}")


if __name__ == "__main__":
    main()
