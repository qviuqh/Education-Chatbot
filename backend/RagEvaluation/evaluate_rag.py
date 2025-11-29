import json
import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# --- Cấu hình đường dẫn import ---
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

# --- Import Libraries ---
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

# Import Wrappers cho Local Models
try:
    from ragas.llms import llm_factory
    from ragas.embeddings import HuggingfaceEmbeddings
    USE_NEW_RAGAS = True
except ImportError:
    USE_NEW_RAGAS = False

# Import RAG Components từ Backend
from backend.rag_pipeline.rag import RAGRetriever, answer_question_with_store
from backend.ai_deps import get_embedder
from backend.config import settings


class RagasEvaluator:
    """
    Class để đánh giá RAG pipeline sử dụng Local LLM (Ollama)
    """
    
    def __init__(
        self, 
        index_path: str,
        meta_path: str,
        test_data_path: str = "test_data.json",
        llm_model: str = None,
        embedding_model: str = None
    ):
        """
        Args:
            index_path: Đường dẫn file .index
            meta_path: Đường dẫn file .json
            test_data_path: Đường dẫn file test data
            llm_model: Tên model LLM (mặc định từ settings)
            embedding_model: Tên model embedding (mặc định từ settings)
        """
        # 1. Khởi tạo Pipeline
        print("🚀 Đang khởi tạo RAG components thực tế...")
        self.system_embedder = get_embedder()
        
        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            raise FileNotFoundError(
                f"Không tìm thấy file index hoặc meta tại:\n"
                f"  Index: {index_path}\n"
                f"  Meta:  {meta_path}"
            )
            
        self.retriever = RAGRetriever(index_path, meta_path, self.system_embedder)
        
        # 2. Load Test Data
        print(f"📂 Đang tải dữ liệu test từ {test_data_path}...")
        try:
            with open(test_data_path, 'r', encoding='utf-8') as f:
                self.test_data = json.load(f)
            print(f"✅ Đã tải {len(self.test_data['questions'])} câu hỏi test")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Không tìm thấy file {test_data_path}\n"
                f"Vui lòng tạo file test data trước khi chạy."
            )

        # 3. Cấu hình Judge Models
        self.llm_model = llm_model or settings.LLM_MODEL
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL
        
        print(f"⚖️  Cấu hình Ragas Judge:")
        print(f"   LLM Model: {self.llm_model}")
        print(f"   Embedding: {self.embedding_model}")
        print(f"   Ragas API: {'New (llm_factory)' if USE_NEW_RAGAS else 'Legacy (Wrapper)'}")
        
        # Setup Judge LLM và Embeddings
        self._setup_judge_models()

    def _setup_judge_models(self):
        """Setup LLM và Embedding models cho Ragas"""
        global USE_NEW_RAGAS
        
        if USE_NEW_RAGAS:
            print("⚠️  Ragas mới chưa hỗ trợ tốt Ollama, đang fallback về wrapper...")
            USE_NEW_RAGAS = False
        
        # Import wrapper
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from langchain_ollama import ChatOllama
        from langchain_huggingface import HuggingFaceEmbeddings
        
        # Config
        self.judge_llm = LangchainLLMWrapper(
            ChatOllama(
                model=self.llm_model,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0,
                timeout=7200,  # 2h
                num_ctx=4096,
            )
        )
        
        self.judge_embeddings = LangchainEmbeddingsWrapper(
            HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        )

    def generate_rag_responses(self, use_reranker: bool = False) -> List[Dict]:
        """
        Chạy RAG pipeline để sinh câu trả lời
        """
        print("\n" + "="*60)
        print("🔄 Đang chạy RAG Pipeline để sinh câu trả lời...")
        print(f"   Use Reranker: {use_reranker}")
        print("="*60 + "\n")
        
        results = []
        
        for i, question in enumerate(self.test_data['questions'], 1):
            print(f"[{i}/{len(self.test_data['questions'])}] Hỏi: {question}")
            
            try:
                # 1. Retrieve contexts
                retrieved_contexts_raw = self.retriever.retrieve(
                    question=question,
                    k_semantic=settings.TOP_K_RETRIEVE,
                    k_keyword=settings.TOP_K_RETRIEVE,
                    use_validation=False
                )
                
                # Xử lý contexts
                if not retrieved_contexts_raw:
                    contexts_list = ["Không tìm thấy thông tin liên quan trong tài liệu."]
                    print("   ⚠️  Không tìm thấy context")
                else:
                    contexts_list = []
                    for ctx in retrieved_contexts_raw:
                        if '\n' in ctx:
                            text = ctx.split('\n', 1)[1]
                        else:
                            text = ctx
                        contexts_list.append(text.strip())
                    
                    print(f"   ✓ Contexts: {len(contexts_list)}")

                # 2. Generate Answer
                answer = answer_question_with_store(
                    question=question,
                    retriever=self.retriever,
                    streaming=False,
                    use_reranker=use_reranker,
                    detect_language=True
                )
                
                print(f"   ✓ Answer: {answer[:80]}...")
                
                results.append({
                    "question": question,
                    "contexts": contexts_list,
                    "answer": answer,
                    "ground_truth": self.test_data["ground_truths"][i-1][0]
                })
                
            except Exception as e:
                print(f"   ❌ Lỗi khi xử lý câu hỏi: {e}")
                results.append({
                    "question": question,
                    "contexts": ["Error during retrieval"],
                    "answer": f"Lỗi: {str(e)}",
                    "ground_truth": self.test_data["ground_truths"][i-1][0]
                })
        
        return results

    def save_detailed_results(self, results, rag_results, output_dir: str = "evaluation_results"):
        """
        Lưu kết quả đánh giá chi tiết vào các file CSV
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 1. FILE SCORES: Điểm từng câu hỏi
            if hasattr(results, 'to_pandas'):
                df_scores = results.to_pandas()
            else:
                df_scores = pd.DataFrame([results])
            
            # Lấy các cột metric
            metric_cols = [col for col in df_scores.columns 
                          if col not in ['question', 'answer', 'contexts', 'ground_truth']]
            
            # Tạo DataFrame điểm
            scores_data = []
            for idx, row in df_scores.iterrows():
                score_row = {
                    'question_id': idx + 1,
                    'question': row.get('question', rag_results[idx]['question']),
                }
                
                for metric in metric_cols:
                    if metric in row:
                        score_row[metric] = row[metric]
                
                scores_data.append(score_row)
            
            df_final_scores = pd.DataFrame(scores_data)
            scores_file = f"{output_dir}/scores_{timestamp}.csv"
            df_final_scores.to_csv(scores_file, index=False, encoding='utf-8-sig')
            print(f"\n📊 Đã lưu điểm chi tiết vào: {scores_file}")
            
            # 2. FILE SUMMARY: Thống kê tổng hợp
            summary_data = []
            for metric in metric_cols:
                if metric in df_scores.columns:
                    values = df_scores[metric].dropna()
                    if len(values) > 0:
                        summary_data.append({
                            'metric': metric,
                            'mean': values.mean(),
                            'std': values.std(),
                            'min': values.min(),
                            'max': values.max(),
                            'count': len(values),
                            'nan_count': df_scores[metric].isna().sum()
                        })
            
            df_summary = pd.DataFrame(summary_data)
            summary_file = f"{output_dir}/summary_{timestamp}.csv"
            df_summary.to_csv(summary_file, index=False, encoding='utf-8-sig')
            print(f"📈 Đã lưu thống kê tổng hợp vào: {summary_file}")
            
            # 3. FILE DETAILS: Câu hỏi, câu trả lời, contexts đầy đủ
            details_data = []
            for idx, result in enumerate(rag_results):
                detail_row = {
                    'question_id': idx + 1,
                    'question': result['question'],
                    'answer': result['answer'],
                    'ground_truth': result['ground_truth'],
                    'num_contexts': len(result['contexts']),
                    'contexts': ' ||| '.join(result['contexts'])
                }
                
                for metric in metric_cols:
                    if metric in df_scores.columns:
                        detail_row[f'score_{metric}'] = df_scores.iloc[idx][metric]
                
                details_data.append(detail_row)
            
            df_details = pd.DataFrame(details_data)
            details_file = f"{output_dir}/details_{timestamp}.csv"
            df_details.to_csv(details_file, index=False, encoding='utf-8-sig')
            print(f"📝 Đã lưu chi tiết đầy đủ vào: {details_file}")
            
            # 4. FILE CONFIG: Cấu hình evaluation
            config_data = {
                'timestamp': [timestamp],
                'llm_model': [self.llm_model],
                'embedding_model': [self.embedding_model],
                'num_questions': [len(rag_results)],
                'metrics_used': [', '.join(metric_cols)],
                'index_path': [getattr(self.retriever, 'index_path', 'N/A')],
            }
            df_config = pd.DataFrame(config_data)
            config_file = f"{output_dir}/config_{timestamp}.csv"
            df_config.to_csv(config_file, index=False, encoding='utf-8-sig')
            print(f"⚙️  Đã lưu cấu hình vào: {config_file}")
            
            # 5. In tóm tắt ra terminal
            print("\n" + "="*70)
            print("📊 TÓM TẮT KẾT QUẢ ĐÁNH GIÁ")
            print("="*70)
            print(f"\n🕒 Thời gian: {timestamp}")
            print(f"📁 Thư mục kết quả: {output_dir}/")
            print(f"❓ Số câu hỏi: {len(rag_results)}")
            print(f"📏 Metrics: {', '.join(metric_cols)}")
            
            print("\n📈 ĐIỂM TRUNG BÌNH:")
            for _, row in df_summary.iterrows():
                metric = row['metric']
                mean = row['mean']
                
                if pd.isna(mean):
                    verdict = "⚠️  Không có dữ liệu (NaN)"
                elif mean >= 0.8:
                    verdict = "✅ EXCELLENT"
                elif mean >= 0.6:
                    verdict = "⚠️  GOOD"
                elif mean >= 0.4:
                    verdict = "⚠️  FAIR"
                else:
                    verdict = "❌ POOR"
                
                print(f"\n   {metric}:")
                print(f"      Mean:  {mean:.4f} ({verdict})")
                print(f"      Std:   {row['std']:.4f}")
                print(f"      Range: [{row['min']:.4f}, {row['max']:.4f}]")
                if row['nan_count'] > 0:
                    print(f"      ⚠️  NaN: {row['nan_count']}/{row['count'] + row['nan_count']} câu")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Lỗi khi lưu kết quả: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_evaluation(
        self, 
        use_all_metrics: bool = False,
        use_reranker: bool = False,
        batch_size: int = 2
    ):
        """
        Thực hiện đánh giá
        """
        # 1. Thu thập dữ liệu
        rag_results = self.generate_rag_responses(use_reranker=use_reranker)
        
        # 2. Chuyển sang Dataset
        data_dict = {
            "question": [r["question"] for r in rag_results],
            "answer": [r["answer"] for r in rag_results],
            "contexts": [r["contexts"] for r in rag_results],
            "ground_truth": [r["ground_truth"] for r in rag_results]
        }
        dataset = Dataset.from_dict(data_dict)
        
        # 3. Chọn metrics
        if use_all_metrics:
            print("\n⚠️  Sử dụng tất cả metrics - MẤT RẤT NHIỀU THỜI GIAN với local LLM!")
            metrics = [
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ]
        else:
            print("\n✅ Chỉ dùng answer_relevancy (nhanh nhất, không cần LLM nhiều)")
            metrics = [answer_relevancy]
        
        print("\n" + "="*60)
        print("🧪 Đang chấm điểm bằng Ragas...")
        print(f"   Metrics: {[m.name for m in metrics]}")
        print(f"   Dataset size: {len(dataset)}")
        print("="*60 + "\n")
        
        try:
            # Tăng timeout
            os.environ['RAGAS_TIMEOUT'] = '7200'
            
            results = evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=self.judge_llm,
                embeddings=self.judge_embeddings,
                batch_size=batch_size,
            )
            
            # Lưu kết quả chi tiết
            self.save_detailed_results(results, rag_results)
            
            return results
            
        except Exception as e:
            print(f"\n❌ Lỗi khi đánh giá: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """Main function để chạy evaluation"""
    print("\n" + "="*70)
    print("🎯 RAG PIPELINE EVALUATION WITH RAGAS (LOCAL LLM)")
    print("="*70 + "\n")
    
    # Cấu hình
    INDEX_FILE = "backend/data/vectordb/index.faiss" 
    META_FILE = "backend/data/vectordb/chunks.json"
    TEST_DATA_FILE = "test_data.json"
    OUTPUT_DIR = "evaluation_results"
    
    # Kiểm tra file index
    if not os.path.exists(INDEX_FILE):
        print(f"⚠️  Không tìm thấy {INDEX_FILE}")
        print("Thử dùng đường dẫn mặc định...")
        INDEX_FILE = "data/vectordb/index.faiss" 
        META_FILE = "data/vectordb/chunks.json"
        
        if not os.path.exists(INDEX_FILE):
            print("❌ Không tìm thấy file vector store nào!")
            return
    
    print(f"✅ Target Vector Store: {INDEX_FILE}")
    
    # Kiểm tra test data
    if not os.path.exists(TEST_DATA_FILE):
        print(f"❌ Không tìm thấy {TEST_DATA_FILE}")
        return

    try:
        evaluator = RagasEvaluator(
            index_path=INDEX_FILE,
            meta_path=META_FILE,
            test_data_path=TEST_DATA_FILE
        )
        
        print("\n💡 LƯU Ý:")
        print(f"   - Kết quả sẽ được lưu vào thư mục '{OUTPUT_DIR}/'")
        print("   - 4 file CSV: scores, summary, details, config")
        print("   - Chỉ dùng answer_relevancy để tránh timeout\n")
        
        # Chạy evaluation
        results = evaluator.run_evaluation(
            use_all_metrics=True,  # True để test đầy đủ (rất chậm)
            use_reranker=False,
            batch_size=1
        )
        
        if results:
            print("\n" + "="*70)
            print("✅ HOÀN TẤT EVALUATION!")
            print(f"📂 Kiểm tra thư mục '{OUTPUT_DIR}/' để xem kết quả chi tiết")
            print("="*70)
        else:
            print("\n❌ Evaluation thất bại")

    except FileNotFoundError as e:
        print(f"\n❌ Lỗi file: {e}")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()