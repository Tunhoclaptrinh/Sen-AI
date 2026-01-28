# vector_db.py
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


class VectorDatabase:
    """
    Vector DB cho MongoDB Atlas Vector Search.
    - Không embed trong class này (embed ở embeddings.py).
    - Lưu chunk dạng:
      {
        "content": "...",
        "embedding": [...],
        "culture_type": "mua_roi_nuoc",     # ROOT FIELD để filter chắc chắn match
        "metadata": { "h1": "...", "h2": "...", ... }
      }
    """

    def __init__(self, db_name: str = "vector_db"):
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError("Thiếu MONGODB_URI trong .env")

        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    @staticmethod
    def _ensure_1d_float_list(vec: Any) -> List[float]:
        # vec có thể là numpy array / list / [[...]]
        if vec is None:
            return []
        if isinstance(vec, list) and vec and isinstance(vec[0], list):
            vec = vec[0]
        return [float(x) for x in vec]

    def insert_many(self, collection_name: str, docs: List[Dict[str, Any]]) -> int:
        if not docs:
            return 0

        col = self.db[collection_name]
        cleaned = []
        for d in docs:
            content = (d.get("content") or "").strip()
            if not content:
                continue

            emb = self._ensure_1d_float_list(d.get("embedding"))
            if not emb:
                # Bắt buộc embedding phải được tạo trước khi insert
                continue
            
            # Prepare doc to insert, keeping root fields dynamically
            doc_to_insert = {
                "content": content,
                "embedding": emb,
                "metadata": d.get("metadata") or {} 
            }
            
            # Copy type fields if present (support user's dynamic structure)
            for k in ["culture_type", "heritage_type", "history_type"]:
                if k in d:
                     doc_to_insert[k] = d[k]

            cleaned.append(doc_to_insert)

        if not cleaned:
            return 0

        res = col.insert_many(cleaned, ordered=False)
        return len(res.inserted_ids)

    def count_documents(self, collection_name: str, filter_query: Optional[Dict[str, Any]] = None) -> int:
        return self.db[collection_name].count_documents(filter_query or {})

    def delete_many(self, collection_name: str, filter_query: Dict[str, Any]) -> int:
        """
        Delete documents matching the filter query.
        """
        if not filter_query:
            return 0
        res = self.db[collection_name].delete_many(filter_query)
        return res.deleted_count

    def query(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        num_candidates: int = 200,
        index_name: str = "vector_index",
        path: str = "embedding",
        filter_dict: Optional[Dict[str, Any]] = None,
        project_fields: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        query_vector: list[float] 1 chiều (1536)
        filter_dict: ví dụ {"culture_type": "mua_roi_nuoc"}
        """
        col = self.db[collection_name]
        q = self._ensure_1d_float_list(query_vector)

        vector_stage: Dict[str, Any] = {
            "index": index_name,
            "queryVector": q,
            "path": path,
            "numCandidates": num_candidates,
            "limit": limit
        }

        if filter_dict:
            # Filter theo ROOT field (culture_type) => chắc chắn match vì ta lưu root
            vector_stage["filter"] = filter_dict

        pipeline: List[Dict[str, Any]] = [{"$vectorSearch": vector_stage}]

        # project
        if project_fields:
            pipeline.append({
                "$project": {
                    **project_fields,
                    "score": {"$meta": "vectorSearchScore"},
                    "_id": 0
                }
            })
        else:
            pipeline.append({
                "$project": {
                    "_id": 0,
                    "content": 1,
                    "culture_type": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            })

        return list(col.aggregate(pipeline))

    def find_regex(self, collection_name: str, regex_pattern: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fallback search using Regex Scan (Slow but guarantees match for keywords).
        """
        col = self.db[collection_name]
        cursor = col.find(
            {"content": {"$regex": regex_pattern, "$options": "i"}}, # Case-insensitive
            {"_id": 0, "content": 1, "metadata": 1}
        ).limit(limit)
        return list(cursor)

    def create_vector_index(self, collection_name: str, path: str = "embedding"):
        """
        [ATLAS ONLY] Create Vector Search Index if possible, or Log instructions.
        """
        # Define the index definition for this specific collection type
        filter_field = "culture_type"
        if collection_name == "heritage": filter_field = "heritage_type"
        elif collection_name == "history": filter_field = "history_type"
        
        index_def = {
            "fields": [
                {
                    "numDimensions": 384,
                    "path": path,
                    "similarity": "cosine",
                    "type": "vector"
                },
                {
                    "path": "metadata.level",
                    "type": "filter"
                },
                {
                    "path": filter_field,
                    "type": "filter"
                }
            ]
        }
        
        import logging
        logger = logging.getLogger("uvicorn")
        logger.info(f"⚠️ [VectorDB] Please Ensure Atlas Search Index exists on '{collection_name}':")
        logger.info(f"   JSON Config: {index_def}")
        
        # Try to create if supported by driver/cluster (M10+)
        try:
            self.db[collection_name].create_search_index(
                model=index_def,
                name="vector_index"
            )
            logger.info("✅ Requested index creation (Atlas may take time to build).")
        except Exception as e:
            logger.warning(f"ℹ️ Auto-index creation skipped: {e}")