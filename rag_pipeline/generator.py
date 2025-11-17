from ollama import chat, generate
import sys
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

def generate_answer_stream(prompt: str, model: str = config['models']['generator'], temperature: float = config['params']['temperature']):
    """
    Sinh câu trả lời từ Ollama và yield từng token (streaming).
    """
    try:
        stream_resp = chat(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            stream=True
        )
        for chunk in stream_resp:
            token = chunk['message']['content']
            yield token
            
    except Exception as e:
        yield f"Lỗi khi sinh phản hồi: {e}"