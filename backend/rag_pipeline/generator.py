from ..ai_deps import get_ollama_client
import sys

def generate_answer_stream(
    prompt: str, 
    model: str, 
    temperature: float = 0.2
):
    """
    Sinh câu trả lời từ Ollama và yield từng token (streaming).
    Hỗ trợ truyền temperature cho model.
    """
    try:
        # Lấy client đã được cấu hình URL chính xác (http://ollama:11434)
        client = get_ollama_client()
        
        stream_resp = client.chat(
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
        # Log ra console để dễ debug trong docker logs
        print(f"Error in generate_answer_stream: {e}", file=sys.stderr)
        yield f"Lỗi khi sinh phản hồi: {e}"

def generate_answer(
    prompt: str, 
    model: str, 
    ):
    """
    Sinh câu trả lời từ Ollama.
    Hỗ trợ truyền temperature cho model.
    Trả về câu trả lời đầy đủ.
    """
    try:
        # Lấy client đã được cấu hình URL chính xác
        client = get_ollama_client()
        
        resp = client.generate(model=model, prompt=prompt, stream=False)
        return resp.get("response", "")
    
    except Exception as e:
        print(f"Error in generate_answer: {e}", file=sys.stderr)
        return f"Lỗi khi sinh phản hồi: {e}"