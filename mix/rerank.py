import numpy as np
from FlagEmbedding import FlagReranker

class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        # FlagReranker tự động nhận diện CPU/GPU
        # use_fp16=True giúp chạy nhanh hơn trên các máy đời mới
        self.model = FlagReranker(model_name, use_fp16=True)

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def rerank(self, query: str, passages: list[str], threshold: float = 0.4):
        if not passages:
            return [], []

        pairs = [[query, p] for p in passages]
        
        # FlagReranker trả về điểm thô (logits)
        raw_scores = self.model.compute_score(pairs)
        
        # Nếu chỉ có 1 cặp, raw_scores là một số, nếu nhiều cặp là một list
        if isinstance(raw_scores, (int, float)):
            raw_scores = [raw_scores]
        
        # Ép về 0-1
        probs = [self.sigmoid(s) for s in raw_scores]

        # Sắp xếp
        ranked = sorted(zip(probs, passages), key=lambda x: x[0], reverse=True)
        filtered = [(float(s), p) for s, p in ranked if s >= threshold]

        if not filtered:
            return [], []

        s_list, p_list = zip(*filtered)
        return list(s_list), list(p_list)
    
# from typing import List, Tuple
# import numpy as np
# import torch # Thêm torch để kiểm tra GPU
# from sentence_transformers import CrossEncoder

# class Reranker:
#     """
#     Rerank bằng CrossEncoder với hỗ trợ Sigmoid để đưa điểm về khoảng 0-1.
#     """

#     def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
#         # Tự động dùng GPU nếu máy bạn có, giúp chạy nhanh hơn rất nhiều
#         device = "cuda" if torch.cuda.is_available() else "cpu"
#         self.model = CrossEncoder(model_name, device=device)

#     def sigmoid(self, x):
#         return 1 / (1 + np.exp(-x))

#     def rerank(self, query: str, passages: List[str], threshold: float = 0.4) -> Tuple[List[float], List[str]]:
#         if not passages:
#             return [], []

#         # Chuẩn bị cặp câu hỏi - đoạn văn
#         pairs = [[query, p] for p in passages]
        
#         # predict() trả về Raw Scores (logits)
#         raw_scores = self.model.predict(pairs)
        
#         # Ép điểm về khoảng 0-1 để dễ đặt threshold
#         sigmoid_scores = self.sigmoid(np.array(raw_scores))

#         # Sắp xếp và lọc theo ngưỡng
#         ranked = sorted(zip(sigmoid_scores, passages), key=lambda x: x[0], reverse=True)
#         filtered = [(float(s), p) for s, p in ranked if s >= threshold]

#         if not filtered:
#             return [], []

#         s_list, p_list = zip(*filtered)
#         return list(s_list), list(p_list)