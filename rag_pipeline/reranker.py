from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

class Reranker:
    def __init__(self, model_name=config['models']['reranker']):
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

    def rerank(self, query, candidates, topn=3):
        pairs = [(query, c) for c in candidates]
        inputs = self.tok([q for q,_ in pairs], [c for _,c in pairs], padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            scores = self.model(**inputs).logits.view(-1)
        order = torch.argsort(scores, descending=True).tolist()
        return [candidates[i] for i in order[:topn]]
