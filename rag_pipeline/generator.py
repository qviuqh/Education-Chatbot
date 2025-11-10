from ollama import chat, generate
import sys
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

def generate_answer(prompt: str, model: str = config['models']['generator'], temperature: float = config['params']['temperature'], stream: bool = False):
    """
    Sinh câu trả lời từ model Ollama (Qwen, Llama, v.v.)
    Hỗ trợ chế độ streaming từng token.
    """
    try:
        if stream:
            stream_resp = chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=True
            )
            full_text = ""
            for chunk in stream_resp:
                token = chunk['message']['content']
                full_text += token
                # Ghi ra stdout hoặc yield để Streamlit hiển thị dần
                sys.stdout.write(token)
                sys.stdout.flush()
            return full_text.strip()
        else:
            response = generate(
                model=model,
                prompt=prompt,
                options={"temperature": temperature}
            )
            return response["response"].strip()
    except Exception as e:
        return f"Lỗi khi sinh phản hồi: {e}"

    # Cách khác: sử dụng chat với streaming (nếu cần)
    # response = chat(
    #     model=model,
    #     messages=[{'role': 'user', 'content': prompt, 'stream': True}],
    # )
    # return response['message']['content'].strip()
    
# Ví dụ sử dụng
# prompt = "Viết một đoạn văn ngắn về trí tuệ nhân tạo."
# answer = generate_answer(prompt)
# print(answer)
