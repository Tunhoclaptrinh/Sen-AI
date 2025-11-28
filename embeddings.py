from openai import OpenAI
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from google import genai

load_dotenv()

class Embeddings:
    def __init__(self, model_name, type):
        self.model_name = model_name
        self.type = type
        if type == "openai":
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif type == "sentence_transformers":
            pass
        elif type == "gemini":
            pass

    def encode(self, doc):
        if self.type == "openai":
            return self.client.embeddings.create(
                input=doc,
                model=self.model_name
            ).data[0].embedding
        elif self.type == "sentence_transformers":
            pass
        elif self.type == "gemini":
            pass
