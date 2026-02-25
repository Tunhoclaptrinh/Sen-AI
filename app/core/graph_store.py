# app/core/graph_store.py
"""
Graph Store: Quản lý Knowledge Graph (Entity - Relation - Entity)
Lưu trữ trong MongoDB collection "knowledge_graph".

Document format:
{
    "subject": "Hoàng Thành Thăng Long",
    "relation": "XÂY_BỞI",
    "object": "Lý Thái Tổ",
    "site_key": "hoang_thanh",
    "confidence": 0.95,
    "source": "hoang_thanh_lich_su.md"
}
"""

import logging
from typing import List, Dict, Optional, Set
from pymongo import MongoClient, UpdateOne
import os

logger = logging.getLogger("uvicorn")

GRAPH_COLLECTION = "knowledge_graph"


class GraphStore:
    """
    Lưu và query Knowledge Graph trong MongoDB.
    Không cần Neo4j — dùng chính MongoDB đang có sẵn.
    """

    def __init__(self, db):
        """
        Args:
            db: MongoDB database object (từ VectorDatabase.db)
        """
        self.db = db
        self.col = db[GRAPH_COLLECTION] if db is not None else None
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Tạo indexes để query nhanh."""
        if self.col is None:
            return
        try:
            self.col.create_index("subject")
            self.col.create_index("object")
            self.col.create_index("site_key")
            self.col.create_index([("subject", 1), ("relation", 1), ("object", 1)], unique=True)
            logger.info("✅ [GraphStore] Indexes created/verified.")
        except Exception as e:
            logger.warning(f"⚠️ [GraphStore] Index creation warning: {e}")

    def insert_triples(self, triples: List[Dict], site_key: str, source: str = "") -> int:
        """
        Insert nhiều triples vào MongoDB.
        Dùng upsert để tránh trùng lặp.

        Args:
            triples: [{"s": "...", "r": "...", "o": "...", "confidence": 0.9}]
            site_key: Key của di tích (vd: "hoang_thanh")
            source: Tên file nguồn

        Returns:
            Số triple được insert/update
        """
        if self.col is None or not triples:
            return 0

        ops = []
        for t in triples:
            subject = str(t.get("s", "")).strip()
            relation = str(t.get("r", "")).strip()
            obj = str(t.get("o", "")).strip()
            confidence = float(t.get("confidence", 0.9))

            if not subject or not relation or not obj:
                continue
            # Bỏ qua triple quá ngắn (noise)
            if len(subject) < 2 or len(obj) < 2:
                continue

            ops.append(
                UpdateOne(
                    # Filter: tìm triple giống hệt
                    {"subject": subject, "relation": relation, "object": obj},
                    # Update: upsert với thông tin đầy đủ
                    {
                        "$set": {
                            "subject": subject,
                            "relation": relation,
                            "object": obj,
                            "site_key": site_key,
                            "confidence": confidence,
                            "source": source,
                        }
                    },
                    upsert=True
                )
            )

        if not ops:
            return 0

        try:
            result = self.col.bulk_write(ops, ordered=False)
            count = result.upserted_count + result.modified_count
            logger.info(f"   📊 [GraphStore] {count} triples upserted (total ops: {len(ops)})")
            return count
        except Exception as e:
            logger.error(f"❌ [GraphStore] Insert error: {e}")
            return 0

    def get_neighbors(self, entity: str, depth: int = 2, max_nodes: int = 20) -> List[Dict]:
        """
        Lấy tất cả quan hệ xoay quanh một entity (BFS).

        Args:
            entity: Tên entity cần tìm (vd: "Hoàng Thành Thăng Long")
            depth: Số bước traverse (1 = trực tiếp, 2 = qua 1 bước)
            max_nodes: Giới hạn số node tối đa

        Returns:
            List các triple liên quan: [{"subject", "relation", "object"}]
        """
        if self.col is None:
            return []

        visited: Set[str] = set()
        result_triples: List[Dict] = []
        queue = [entity]
        visited.add(entity.lower())

        for _ in range(depth):
            if not queue or len(result_triples) >= max_nodes:
                break

            next_queue = []
            for current_entity in queue:
                # Tìm triples mà entity là subject HOẶC object
                cursor = self.col.find(
                    {
                        "$or": [
                            {"subject": {"$regex": current_entity, "$options": "i"}},
                            {"object": {"$regex": current_entity, "$options": "i"}},
                        ]
                    },
                    {"_id": 0, "subject": 1, "relation": 1, "object": 1, "confidence": 1}
                ).limit(max_nodes)

                for doc in cursor:
                    result_triples.append(doc)

                    # Thêm nodes mới vào queue cho vòng sau
                    for neighbor in [doc["subject"], doc["object"]]:
                        if neighbor.lower() not in visited:
                            visited.add(neighbor.lower())
                            next_queue.append(neighbor)

            queue = next_queue

        return result_triples

    def get_by_site(self, site_key: str, limit: int = 100) -> List[Dict]:
        """Lấy tất cả triples của một di tích."""
        if self.col is None:
            return []
        cursor = self.col.find(
            {"site_key": site_key},
            {"_id": 0, "subject": 1, "relation": 1, "object": 1}
        ).limit(limit)
        return list(cursor)

    def count(self, site_key: Optional[str] = None) -> int:
        """Đếm số triples."""
        if self.col is None:
            return 0
        query = {"site_key": site_key} if site_key else {}
        return self.col.count_documents(query)

    def delete_by_source(self, source: str) -> int:
        """Xóa triples của một file cụ thể (khi re-ingest)."""
        if self.col is None:
            return 0
        result = self.col.delete_many({"source": source})
        return result.deleted_count

    def format_triples_as_context(self, triples: List[Dict]) -> str:
        """
        Format triples thành text có thể đưa vào LLM prompt.

        Ví dụ output:
          - Hoàng Thành Thăng Long [XÂY_BỞI] Lý Thái Tổ
          - Lý Thái Tổ [THUỘC_TRIỀU_ĐẠI] Nhà Lý
          - Nhà Lý [CHIẾN_THẮNG] Quân Tống
        """
        if not triples:
            return ""

        lines = []
        seen = set()
        for t in triples:
            line = f"  - {t['subject']} [{t['relation']}] {t['object']}"
            if line not in seen:
                seen.add(line)
                lines.append(line)

        return "\n".join(lines)
