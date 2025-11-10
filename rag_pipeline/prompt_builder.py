def build_prompt(question, contexts):
    ctx_block = "\n\n---\n".join(contexts)
    return f"""You are a multilingual assistant. 
Answer clearly in the same language as the question.
If the answer is not found, say "Không tìm thấy thông tin" (Not found).

[CONTEXT]
{ctx_block}

[QUESTION]
{question}

[ANSWER]
"""
