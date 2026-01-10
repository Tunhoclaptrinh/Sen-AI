from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from .route import Route

class SemanticRouter:
    """
    Router dựa trên cosine similarity giữa query embedding và sample embeddings của từng route.
    - Precompute embeddings cho samples để chạy nhanh.
    - Dùng max similarity để bắt keyword mạnh.
    """

    def __init__(
        self,
        embedding,
        routes: List[Route],
        threshold: float = 0.6,
        margin: float = 0.08
    ):
        self.embedding = embedding
        self.routes = routes
        self.threshold = threshold
        self.margin = margin
        self._route_embs = {}

        for r in self.routes:
            samples = [str(s).strip() for s in (r.samples or []) if str(s).strip()]
            if not samples:
                self._route_embs[r.name] = None
                continue

            # Chuyển đổi samples thành embeddings một lần duy nhất khi khởi tạo
            embs = np.array(self.embedding.encode(samples), dtype=np.float32)
            norms = np.linalg.norm(embs, axis=1, keepdims=True)
            embs = embs / np.clip(norms, 1e-12, None)
            self._route_embs[r.name] = embs

    def guide(self, query: str) -> Tuple[float, str, Optional[Dict[str, Any]]]:
        q_emb = self.embedding.encode([query])
        
        # FIX TẠI ĐÂY: Kiểm tra mảng NumPy một cách an toàn
        if q_emb is None or len(q_emb) == 0:
            return 0.0, "uncertain", None

        # Đảm bảo q là mảng 1D chuẩn
        q = np.array(q_emb[0], dtype=np.float32)
        q_norm = np.linalg.norm(q)
        q = q / max(q_norm, 1e-12)

        scores = []
        for r in self.routes:
            embs = self._route_embs.get(r.name)
            if embs is None:
                continue
            
            # Tính toán độ tương đồng (Cosine Similarity)
            # Dùng np.max để lấy sample giống nhất trong route đó
            sims = np.dot(embs, q)
            best_sim = float(np.max(sims))
            scores.append((best_sim, r))

        if not scores:
            return 0.0, "uncertain", None

        # Sắp xếp để lấy Route có điểm cao nhất
        scores.sort(key=lambda x: x[0], reverse=True)
        best_score, best_route = scores[0]
        
        # Kiểm tra ngưỡng (Threshold)
        if best_score < self.threshold:
            return float(best_score), "uncertain", None

        return float(best_score), best_route.name, (best_route.filter_dict or None)



#---- bản cho app_fastapi
# # semantic_router/router.py
# from typing import List, Tuple, Optional, Dict, Any
# import numpy as np

# from .route import Route


# class SemanticRouter:
#     """
#     Router dựa trên cosine similarity giữa query embedding và sample embeddings của từng route.
#     - Precompute embeddings cho samples để chạy nhanh.
#     - Dùng max similarity để bắt keyword mạnh.
#     """

#     def __init__(
#         self,
#         embedding,
#         routes: List[Route],
#         threshold: float = 0.6,
#         margin: float = 0.08
#     ):
#         self.embedding = embedding
#         self.routes = routes
#         self.threshold = threshold
#         self.margin = margin

#         self._route_embs = {}  # route_name -> np.ndarray (n_samples, dim) normalized

#         for r in self.routes:
#             samples = [str(s).strip() for s in (r.samples or []) if str(s).strip()]
#             if not samples:
#                 self._route_embs[r.name] = None
#                 continue

#             embs = np.array(self.embedding.encode(samples), dtype=np.float32)
#             norms = np.linalg.norm(embs, axis=1, keepdims=True)
#             embs = embs / np.clip(norms, 1e-12, None)
#             self._route_embs[r.name] = embs

#     def guide(self, query: str) -> Tuple[float, str, Optional[Dict[str, Any]]]:
#         q_emb = self.embedding.encode([query])
#         if not q_emb:
#             return 0.0, "uncertain", None

#         q = np.array(q_emb[0], dtype=np.float32)
#         q = q / max(np.linalg.norm(q), 1e-12)

#         scores = []
#         for r in self.routes:
#             embs = self._route_embs.get(r.name)
#             if embs is None:
#                 continue
#             sim = float(np.max(np.dot(embs, q)))  # max similarity
#             scores.append((sim, r))

#         if not scores:
#             return 0.0, "uncertain", None

#         scores.sort(key=lambda x: x[0], reverse=True)
#         best_score, best_route = scores[0]
#         second_score = scores[1][0] if len(scores) > 1 else None

#         if best_score < self.threshold:
#             return float(best_score), "uncertain", None

#         if second_score is not None and (best_score - second_score) < self.margin:
#             # vẫn trả route top1 nhưng biết là "gần"
#             pass

#         return float(best_score), best_route.name, (best_route.filter_dict or None)













