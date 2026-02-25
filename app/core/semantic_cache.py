"""
SemanticCache: Cache câu trả lời dựa trên độ tương đồng ngữ nghĩa (cosine similarity).
- Lưu trữ: MongoDB collection `query_cache`
- Embedding: local SentenceTransformer (paraphrase-multilingual-MiniLM-L12-v2)
- Lookup: cosine similarity trong Python (không cần Atlas Vector Search Index mới)
- Threshold: 0.92 (có thể điều chỉnh)
"""

import logging
import time
import numpy as np
from typing import Optional, Any, Dict
from pymongo import MongoClient

logger = logging.getLogger("uvicorn")

SIMILARITY_THRESHOLD = 0.92   # Ngưỡng tương đồng để coi là "cùng câu hỏi"
MAX_CACHE_ENTRIES   = 500     # Giới hạn số entry để không load quá nhiều
DEFAULT_TTL         = 3600    # 1 tiếng (giây)


class SemanticCache:
    """
    Cache ngữ nghĩa: thay vì khớp từng chữ, so sánh embedding cosine similarity.
    Ví dụ:
        "Lý Thái Tổ là ai?"  ≈  "Ai là Lý Thái Tổ?"  → HIT
        "Cho tôi biết về Lý Thái Tổ"                  → HIT (nếu > 0.92)
    """

    def __init__(self, db, embedder):
        """
        Args:
            db: pymongo Database object (v_db.db)
            embedder: SentenceTransformer instance
        """
        self.col = db["query_cache"]
        self.embedder = embedder
        self._ensure_indexes()

    def _ensure_indexes(self):
        try:
            self.col.create_index("expires_at", expireAfterSeconds=0)  # TTL index
            self.col.create_index("intent")
            logger.info("✅ [SemanticCache] Indexes OK.")
        except Exception as e:
            logger.warning(f"⚠️ [SemanticCache] Index warning: {e}")

    def _embed(self, text: str) -> np.ndarray:
        """Embed text thành vector numpy."""
        vec = self.embedder.encode(text, normalize_embeddings=True)
        return np.array(vec, dtype=np.float32)

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity — đã normalize_embeddings=True nên chỉ cần dot product."""
        return float(np.dot(a, b))

    # ─── PUBLIC API ───────────────────────────────────────────────────────────

    def get(self, query: str, intent_filter: str = "heritage") -> Optional[Dict]:
        """
        Tìm response tương đồng trong cache.
        Returns: dict response nếu tìm thấy, None nếu không.
        """
        try:
            query_vec = self._embed(query)

            # Load MAX_CACHE_ENTRIES entries gần nhất (chỉ intent cần thiết)
            entries = list(
                self.col.find(
                    {"intent": intent_filter},
                    {"query_embedding": 1, "response": 1, "_id": 0}
                ).sort("_id", -1).limit(MAX_CACHE_ENTRIES)
            )

            if not entries:
                return None

            best_score = 0.0
            best_entry = None

            for entry in entries:
                stored_vec = np.array(entry["query_embedding"], dtype=np.float32)
                score = self._cosine(query_vec, stored_vec)
                if score > best_score:
                    best_score = score
                    best_entry = entry

            if best_score >= SIMILARITY_THRESHOLD and best_entry:
                logger.info(f"   🎯 [SemanticCache] HIT (similarity={best_score:.3f})")
                return best_entry["response"]

            logger.info(f"   💨 [SemanticCache] MISS (best={best_score:.3f} < {SIMILARITY_THRESHOLD})")
            return None

        except Exception as e:
            logger.warning(f"⚠️ [SemanticCache] get() error: {e}")
            return None

    def set(self, query: str, response: Dict, intent: str = "heritage", ttl: int = DEFAULT_TTL):
        """
        Lưu response vào cache.
        Args:
            query: câu hỏi gốc (đã normalize)
            response: dict kết quả từ workflow
            intent: loại intent để filter khi lookup
            ttl: thời gian sống tính bằng giây
        """
        try:
            query_vec = self._embed(query)
            expires_at = time.time() + ttl

            self.col.insert_one({
                "query": query,
                "query_embedding": query_vec.tolist(),
                "response": response,
                "intent": intent,
                "expires_at": expires_at,
            })
            logger.info(f"   💾 [SemanticCache] Saved (TTL={ttl}s)")

        except Exception as e:
            logger.warning(f"⚠️ [SemanticCache] set() error: {e}")

    def delete_expired(self):
        """Xóa thủ công các entry hết hạn (MongoDB TTL index sẽ tự xóa, nhưng có thể gọi thủ công)."""
        try:
            result = self.col.delete_many({"expires_at": {"$lt": time.time()}})
            logger.info(f"🧹 [SemanticCache] Deleted {result.deleted_count} expired entries")
        except Exception as e:
            logger.warning(f"⚠️ [SemanticCache] delete_expired error: {e}")

    def count(self) -> int:
        return self.col.count_documents({})
