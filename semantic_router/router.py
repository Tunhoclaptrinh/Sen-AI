# semantic_router/router.py
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

        self._route_embs = {}  # route_name -> np.ndarray (n_samples, dim) normalized

        for r in self.routes:
            samples = [str(s).strip() for s in (r.samples or []) if str(s).strip()]
            if not samples:
                self._route_embs[r.name] = None
                continue

            embs = np.array(self.embedding.encode(samples), dtype=np.float32)
            norms = np.linalg.norm(embs, axis=1, keepdims=True)
            embs = embs / np.clip(norms, 1e-12, None)
            self._route_embs[r.name] = embs

    def guide(self, query: str) -> Tuple[float, str, Optional[Dict[str, Any]]]:
        q_emb = self.embedding.encode([query])
        if not q_emb:
            return 0.0, "uncertain", None

        q = np.array(q_emb[0], dtype=np.float32)
        q = q / max(np.linalg.norm(q), 1e-12)

        scores = []
        for r in self.routes:
            embs = self._route_embs.get(r.name)
            if embs is None:
                continue
            sim = float(np.max(np.dot(embs, q)))  # max similarity
            scores.append((sim, r))

        if not scores:
            return 0.0, "uncertain", None

        scores.sort(key=lambda x: x[0], reverse=True)
        best_score, best_route = scores[0]
        second_score = scores[1][0] if len(scores) > 1 else None

        if best_score < self.threshold:
            return float(best_score), "uncertain", None

        if second_score is not None and (best_score - second_score) < self.margin:
            # vẫn trả route top1 nhưng biết là "gần"
            pass

        return float(best_score), best_route.name, (best_route.filter_dict or None)














# import numpy as np

# class SemanticRouter():
#     def __init__(self, embedding, routes):
#         """
#         :param embedding: Một đối tượng embedding có phương thức encode() để chuyển đổi các văn bản thành embeddings.
#         :param routes: Danh sách các đối tượng route với các thuộc tính như name và samples.
#         """
#         self.routes = routes
#         self.embedding = embedding
#         self.routesEmbedding = {}

#         # Tính toán embedding cho mỗi route
#         for route in self.routes:
#             # Ensure that `route.samples` is a list of strings
#             if not isinstance(route.samples, list):
#                 raise ValueError(f"Route {route.name} samples must be a list of strings.")
            
#             # Convert all items in `route.samples` to strings
#             route.samples = [str(sample) for sample in route.samples]

#             # Encode the samples into embeddings
#             self.routesEmbedding[route.name] = self.embedding.encode(route.samples)

#     def get_routes(self):
#         """
#         Trả về danh sách các routes.
#         """
#         return self.routes

#     def guide(self, query):
#         """
#         Nhận truy vấn và trả về route có điểm tương đồng cao nhất với truy vấn.
        
#         :param query: Câu truy vấn để tìm kiếm trên các routes.
#         :return: Route có điểm tương đồng cao nhất với truy vấn.
#         """
#         queryEmbedding = self.embedding.encode([query])  # Biến truy vấn thành embedding
#         queryEmbedding = queryEmbedding / np.linalg.norm(queryEmbedding)  # Chuẩn hóa truy vấn

#         scores = []

#         # Tính toán cosine similarity giữa embedding của truy vấn và embedding của các route
#         for route in self.routes:
#             routesEmbedding = self.routesEmbedding[route.name]  # Lấy embedding của route
#             routesEmbedding = routesEmbedding / np.linalg.norm(routesEmbedding, axis=1, keepdims=True)  # Chuẩn hóa các sample embeddings

#             # Tính điểm tương đồng giữa các embedding của route và truy vấn
#             score = np.mean(np.dot(routesEmbedding, queryEmbedding.T).flatten())
#             scores.append((score, route.name))

#         # Sắp xếp các scores theo thứ tự giảm dần và trả về route có điểm tương đồng cao nhất
#         scores.sort(reverse=True, key=lambda x: x[0])

#         # Nếu độ tương đồng thấp, không trả lời câu hỏi
#         if scores[0][0] < 0.35:  # Ngưỡng tương đồng (có thể điều chỉnh ngưỡng 0.5)
#             return 0, "uncertain"  # Trả về "uncertain" khi không có độ tương đồng cao

#         # Trả về route có điểm tương đồng cao nhất nếu câu hỏi liên quan đến múa rối nước
#         return scores[0]  # Trả về tuple (score, best_route)
