from ollama import chat, generate
import sys
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

def generate_answer_stream(
    prompt: str, 
    model: str = config['models']['generator'], 
    temperature: float = config['params']['temperature']
):
    """
    Sinh câu trả lời từ Ollama và yield từng token (streaming).
    Hỗ trợ truyền temperature cho model.
    """
    try:
        stream_resp = chat(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            stream=True,
            options={
                "temperature": temperature
            }
        )
        for chunk in stream_resp:
            yield chunk['message']['content']
    
    except Exception as e:
        yield f"Lỗi khi sinh phản hồi: {e}"

def generate_answer(
    prompt: str, 
    model: str = config['models']['generator'], 
    ):
    """
    Sinh câu trả lời từ Ollama.
    Hỗ trợ truyền temperature cho model.
    Trả về câu trả lời đầy đủ.
    """
    try:
        resp = generate(model=model, prompt=prompt, stream=False)
        return resp.get("response", "")
    
    except Exception as e:
        return f"Lỗi khi sinh phản hồi: {e}"