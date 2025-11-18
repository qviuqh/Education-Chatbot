from rag_pipeline.generator import generate_answer
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

class LanguageDetector:
    def __init__(self, llm_model=config['models']['generator']):
        """
        Khởi tạo bộ phát hiện ngôn ngữ sử dụng LLM.
        
        Args:
            llm_model: Tên model LLM sử dụng
        """
        self.llm_model = llm_model
    
    def detect(self, text):
        """
        Phát hiện ngôn ngữ của văn bản đầu vào.
        
        Args:
            text: Văn bản cần phát hiện ngôn ngữ
        
        Returns:
            Mã ngôn ngữ phát hiện được (ví dụ: 'en', 'vi', ...)
        """
        prompt = f"Identify the language of the question in the paragraph: \"{text}\". Answer to the point, do not answer in a rambling way. (Eg. English, Vietnamese, or Chinese)"
        response = generate_answer(prompt, model=self.llm_model)
        print(f"Detected language response: {response}")
        return response