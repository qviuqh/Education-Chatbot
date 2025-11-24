from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class Reranker:
    def __init__(self, model_name: str, device=None):
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
    
        # Tự chọn device nếu không truyền vào
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model.to(self.device)
        self.model.eval()
    
    def rerank(
        self,
        query,
        candidates,
        topn=3,
        score_threshold=None,     # ngưỡng để lọc đoạn không liên quan
        return_scores=False       # nếu True: trả về (text, score)
    ):
        """
        Rerank các candidates theo mức độ liên quan với query.
        
        Nếu score_threshold != None:
            - Chỉ giữ lại các đoạn có score >= threshold
            - Nếu không có đoạn nào đạt ngưỡng -> trả về [] (no context)

        Bản chất score ở đây là sigmoid(logit) ∈ (0, 1),
        có thể xem như "xác suất liên quan".
        """
        if not candidates:
            return []
        
        pairs = [(query, c) for c in candidates]
        
        inputs = self.tok(
            [q for q, _ in pairs],
            [c for _, c in pairs],
            padding=True,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)
        
        with torch.no_grad():
            logits = self.model(**inputs).logits.view(-1)
        # Chuẩn hóa về [0, 1] cho dễ đặt threshold
        scores = torch.sigmoid(logits)    # shape: (num_candidates, )
        # Sort theo score giảm dần
        order = torch.argsort(scores, descending=True).tolist()
        
        results = []
        for idx in order:
            score = float(scores[idx].item())
            text = candidates[idx]
            # Nếu có đặt threshold thì lọc
            if score_threshold is not None and score < score_threshold:
                continue
            
            if return_scores:
                results.append((text, score))
            else:
                results.append(text)
            
            if len(results) >= topn:
                break
        # Nếu sau khi lọc không còn gì -> trả về list rỗng
        return results
