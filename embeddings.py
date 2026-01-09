# embeddings.py
import os
from typing import List, Union

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class Embeddings:
    """
    Một wrapper thống nhất cho embedding.
    - Mặc định dùng OpenAI embedding để đảm bảo dims đồng nhất (text-embedding-3-small: 1536).
    """

    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Thiếu OPENAI_API_KEY trong .env")
        self.client = OpenAI(api_key=api_key)

    def encode(self, texts: Union[str, List[str]]) -> List[List[float]]:
        if not texts:
            return []

        if isinstance(texts, str):
            texts = [texts]

        # ép về list[str]
        texts = [str(t) for t in texts if str(t).strip()]
        if not texts:
            return []

        resp = self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        return [item.embedding for item in resp.data]



# import openai
# from sentence_transformers import SentenceTransformer
# import os
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# class Embeddings:
#     def __init__(self, model_name="text-embedding-3-small", type="openai"):
#         """
#         :param model_name: Name of the model to use (e.g., "text-embedding-3-small").
#         :param type: Type of embedding model ("openai", "sentence_transformers", "gemini").
#         """
#         self.model_name = model_name
#         self.type = type

#         # Initialize client based on embedding type
#         if self.type == "openai":
#             # CẬP NHẬT 1: Khởi tạo Client theo chuẩn mới
#             api_key = os.getenv("OPENAI_API_KEY")
#             if not api_key:
#                 raise ValueError("OPENAI_API_KEY not found in environment variables")
#             self.client = openai.Client(api_key=api_key)
            
#         elif self.type == "sentence_transformers":
#             self.client = SentenceTransformer(model_name)
#         elif self.type == "gemini":
#             # Giả sử bạn đã cài google-generativeai
#             import google.generativeai as genai
#             self.client = genai
#             genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
#         else:
#             raise ValueError(f"Embedding type '{type}' not supported.")

#     def encode(self, doc):
#         """
#         Converts the text into an embedding based on the chosen model.
#         :param doc: A list of sentences or documents to encode.
#         :return: Embeddings as a list of vectors.
#         """
#         # Xử lý trường hợp input rỗng để tránh lỗi API
#         if not doc:
#             return []

#         # Ensure `doc` is a list of strings
#         if isinstance(doc, str):
#             doc = [doc]
        
#         if not isinstance(doc, list):
#             raise ValueError("Input must be a list of strings.")
        
#         doc = [str(item) for item in doc]

#         # Debug print
#         # print(f"Input to {self.type} embeddings: {doc}")

#         if self.type == "openai":
#             try:
#                 # Call OpenAI API
#                 response = self.client.embeddings.create(
#                     model=self.model_name,
#                     input=doc
#                 )

#                 # CẬP NHẬT 2: Truy cập dữ liệu kiểu Object (v1.0+) thay vì Dictionary
#                 # response.data là một list các object, mỗi object có thuộc tính .embedding
#                 return [item.embedding for item in response.data]

#             # CẬP NHẬT 3: Sửa tên class lỗi
#             except openai.OpenAIError as e:
#                 print(f"Error during OpenAI embedding: {e}")
#                 return []
#             except Exception as e:
#                 print(f"Unexpected error: {e}")
#                 return []

#         elif self.type == "sentence_transformers":
#             return self.client.encode(doc).tolist() # Convert numpy array to list

#         elif self.type == "gemini":
#             try:
#                 # Lưu ý: Gemini API có cấu trúc khác, đây là ví dụ cơ bản
#                 result = [self.client.embed_content(model=self.model_name, content=d, task_type="retrieval_document")['embedding'] for d in doc]
#                 return result
#             except Exception as e:
#                 raise ValueError(f"Error using Gemini API: {e}")

#         else:
#             raise ValueError(f"Embedding type '{self.type}' not supported.")




