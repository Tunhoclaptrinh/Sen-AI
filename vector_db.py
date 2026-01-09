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

            culture_type = (d.get("culture_type") or "").strip()
            if not culture_type:
                # Bắt buộc có culture_type để filter
                continue

            cleaned.append({
                "content": content,
                "embedding": emb,
                "culture_type": culture_type,      # ROOT
                "metadata": d.get("metadata") or {} # headers / page / source...
            })

        if not cleaned:
            return 0

        res = col.insert_many(cleaned, ordered=False)
        return len(res.inserted_ids)

    def count_documents(self, collection_name: str, filter_query: Optional[Dict[str, Any]] = None) -> int:
        return self.db[collection_name].count_documents(filter_query or {})

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





# import os
# import numpy as np
# from pymongo import MongoClient
# from sentence_transformers import SentenceTransformer
# from dotenv import load_dotenv
# from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# load_dotenv()

# class VectorDatabase:
#     def __init__(self, db_type: str, embedding_model_name: str = "all-MiniLM-L6-v2"):
#         self.db_type = db_type

#         if self.db_type != "mongodb":
#             raise ValueError(f"Unsupported db_type: {db_type}")

#         uri = os.getenv("MONGODB_URI")
#         if not uri:
#             raise RuntimeError("Thiếu MONGODB_URI trong .env")

#         self.client = MongoClient(uri)
#         self.db = self.client["vector_db"]

#         # SentenceTransformer embeddings
#         self.embedding_model = SentenceTransformer(embedding_model_name)

#     # ---------- helpers ----------
#     def _to_1d_float_list(self, vec):
#         if isinstance(vec, np.ndarray):
#             vec = vec.tolist()

#         # nếu vec bị [[...]] thì lấy vec[0]
#         if isinstance(vec, list) and vec and isinstance(vec[0], list):
#             vec = vec[0]

#         return [float(x) for x in vec]

#     def _embed_text(self, text: str) -> list:
#         # luôn embed theo list[str] -> lấy [0] để ra 1 vector 1 chiều
#         vec = self.embedding_model.encode([text])[0]
#         return self._to_1d_float_list(vec)

#     # ---------- insert markdown ----------
#     def insert_markdown(self, collection_name: str, cleaned_markdown: str, metadata: dict = None):
#         """
#         Nhận markdown string -> chunk theo header + recursive splitter -> embed + insert_many
#         """
#         headers_to_split_on = [
#             ("#", "h1"),
#             ("##", "h2"),
#             ("###", "h3"),
#         ]
#         markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
#         sections = markdown_splitter.split_text(cleaned_markdown)

#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=800,
#             chunk_overlap=150,
#             separators=["\n\n", "\n", ".", " ", ""],
#         )
#         final_chunks = text_splitter.split_documents(sections)

#         docs = []
#         for doc in final_chunks:
#             content = (doc.page_content or "").strip()
#             if not content:
#                 continue

#             emb = self._embed_text(content)

#             docs.append({
#                 "content": content,
#                 "embedding": emb,
#                 "metadata": {**(metadata or {}), **(doc.metadata or {})},
#             })

#         return self.insert_many(collection_name, docs)

#     # ---------- bulk insert ----------
#     def insert_many(self, collection_name: str, documents: list[dict]) -> int:
#         if not documents:
#             return 0
#         col = self.db[collection_name]

#         cleaned = []
#         for d in documents:
#             if "content" not in d:
#                 continue

#             doc = dict(d)

#             # nếu embedding chưa có thì embed từ content
#             if "embedding" not in doc or not doc["embedding"]:
#                 doc["embedding"] = self._embed_text(doc["content"])
#             else:
#                 doc["embedding"] = self._to_1d_float_list(doc["embedding"])

#             cleaned.append(doc)

#         if not cleaned:
#             return 0

#         res = col.insert_many(cleaned, ordered=False)
#         return len(res.inserted_ids)

#     # ---------- query ----------
#     def query(
#         self,
#         collection_name: str,
#         query_vector,
#         limit: int = 5,
#         num_candidates: int = 200,
#         index_name: str = "vector_index",
#         path: str = "embedding",
#         project_fields: dict | None = None,
#     ):
#         col = self.db[collection_name]

#         # đảm bảo query_vector là list[float] 1 chiều
#         q = self._to_1d_float_list(query_vector)

#         pipeline = [
#             {
#                 "$vectorSearch": {
#                     "index": index_name,
#                     "queryVector": q,
#                     "path": path,
#                     "numCandidates": num_candidates,
#                     "limit": limit,
#                 }
#             }
#         ]

#         # projection (rất nên có)
#         if project_fields:
#             pipeline.append({
#                 "$project": {
#                     **project_fields,
#                     "score": {"$meta": "vectorSearchScore"},
#                     "_id": 0
#                 }
#             })
#         else:
#             pipeline.append({
#                 "$project": {
#                     "_id": 0,
#                     "content": 1,
#                     "metadata": 1,
#                     "score": {"$meta": "vectorSearchScore"},
#                 }
#             })

#         return list(col.aggregate(pipeline))


#     def count_documents(self, collection_name: str) -> int:
#         return self.db[collection_name].count_documents({})
