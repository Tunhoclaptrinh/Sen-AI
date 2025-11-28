
from pymongo import MongoClient
from chromadb import HttpClient
from qdrant_client import QdrantClient
from supabase import create_client, Client
from dotenv import load_dotenv
from qdrant_client import models as qdrant_models
load_dotenv()
import os

load_dotenv()

class VectorDatabase:
    def __init__(self, db_type: str):
        self.db_type = db_type
        if self.db_type == "mongodb":
            self.client = MongoClient(os.getenv("MONGODB_URI"))
        elif self.db_type == "chromadb":
            pass
        elif self.db_type == "qdrant":
            pass
        elif self.db_type == "supabase":
            pass
    def _ensure_collection_exists(self, collection_name: str):
        """Ensure collection exists for Qdrant, create if it doesn't"""
        if self.db_type == "qdrant":
            if not self.client.collection_exists(collection_name=collection_name):
                print(f"[Info] Collection '{collection_name}' not found. Creating it...")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=1536,  # adjust size based on your embedding model
                        distance=qdrant_models.Distance.COSINE
                    )
                )
                
                # Create index for title field to enable filtering
                print(f"[Info] Creating index for 'title' field...")
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="title",
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD
                )
                return True  # Collection was created
        return False  # Collection already existed or not Qdrant
    def insert_document(self, collection_name: str, document: dict):
        if self.db_type == "mongodb":
            db = self.client.get_database("vector_db")
            collection = db[collection_name]
            collection.insert_one(document)
        elif self.db_type == "chromadb":
            pass
        elif self.db_type == "qdrant":
            pass
        elif self.db_type == "supabase":
            pass
    def query(self, collection_name: str, query_vector: list, limit: int = 5):
        if self.db_type == "mongodb":
            db = self.client.get_database("vector_db")
            collection = db[collection_name]
            results = collection.aggregate([
                {
                    "$vectorSearch": {
                        "index": "vector_index",  # tên index bạn đã tạo
                        "queryVector": query_vector,
                        "path": "embedding",
                        "numCandidates": 100,
                        "limit": limit
                    }
                }
            ])
            return list(results)
        elif self.db_type == "chromadb":
            pass
        elif self.db_type == "qdrant":
            pass
        elif self.db_type == "supabase":
            pass
    def document_exists(self, collection_name, filter_query):
        if self.db_type == "mongodb":
            db = self.client.get_database("vector_db")
            collection = db[collection_name]
            return collection.count_documents(filter_query) > 0
        elif self.db_type == "chromadb":
            pass
        elif self.db_type == "qdrant":
            pass
        elif self.db_type == "supabase":
            pass
        else:
            pass
    def count_documents(self, collection_name: str) -> int:
        if self.db_type == "mongodb":
            db = self.client.get_database("vector_db")  # Đảm bảo đúng tên DB
            collection = db[collection_name]
            return collection.count_documents({})
        else:
            raise NotImplementedError("count_documents chỉ hỗ trợ MongoDB trong phiên bản này.")

