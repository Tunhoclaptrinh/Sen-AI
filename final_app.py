import os
import base64
import re
import json
import logging
import asyncio
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI 
import redis.asyncio as redis 
from edge_tts import Communicate
from langdetect import detect

# Các bộ chia nhỏ văn bản
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# Module tùy chỉnh của Hiếu
from vector_db import VectorDatabase
from reflection import Reflection
from semantic_router.route import Route
from semantic_router.layer import RouteLayer
from semantic_router.encoders import OpenAIEncoder # Dùng encoder của OpenAI cho nhẹ

# ====== 1. CẤU HÌNH GLOBAL ======
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "vector_db"
COLLECTION_NAME = "culture"
REDIS_URL = os.getenv("REDIS_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Khởi tạo Encoder OpenAI cho Router (Cực nhẹ, không tốn RAM)
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
encoder = OpenAIEncoder(name="text-embedding-3-small")

# Đường dẫn file dữ liệu
CULTURE_FILES = [
    ("mua_roi_nuoc", "mua_roi_nuoc.md"),
    ("hoang_thanh", "hoang_thanh.md"),
]

# ====== 2. HÀM HỖ TRỢ NẠP DỮ LIỆU & LOGIC HYBRID ======

async def get_openai_embedding(text: str, client: AsyncOpenAI) -> List[float]:
    """Lấy vector từ OpenAI thay vì dùng model nội bộ"""
    text = text.replace("\n", " ")
    response = await client.embeddings.create(input=[text], model="text-embedding-3-small")
    return response.data[0].embedding

def simple_keyword_score(content: str, rewritten_query: str) -> float:
    content_lower = content.lower()
    query_words = [w for w in rewritten_query.lower().split() if len(w) > 2]
    if not query_words: return 0.0
    matched_count = sum(1 for word in query_words if word in content_lower)
    return matched_count / len(query_words)

def chunk_markdown(md_text: str) -> List[Dict]:
    headers_to_split_on = [("#", "h1"), ("##", "h2"), ("###", "h3")]
    splitter1 = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    sections = splitter1.split_text(md_text)
    splitter2 = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=180)
    docs = splitter2.split_documents(sections)
    return [{"content": d.page_content.strip(), "metadata": d.metadata} for d in docs if d.page_content.strip()]

async def auto_ingest_data(v_db: VectorDatabase, client: AsyncOpenAI):
    """SỬA ĐỔI: Dùng OpenAI để nạp dữ liệu"""
    for culture_type, file_path in CULTURE_FILES:
        if v_db.count_documents(COLLECTION_NAME, {"culture_type": culture_type}) == 0:
            if os.path.exists(file_path):
                logger.info(f"🔄 Đang nạp lại dữ liệu OpenAI (1536 dim) cho: {culture_type}")
                with open(file_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                
                chunks = chunk_markdown(md_content)
                docs_to_insert = []
                for c in chunks:
                    vec = await get_openai_embedding(c["content"], client)
                    docs_to_insert.append({
                        "content": c["content"],
                        "embedding": vec,
                        "culture_type": culture_type,
                        "metadata": c["metadata"]
                    })
                v_db.insert_many(COLLECTION_NAME, docs_to_insert)
                logger.info(f"✅ Đã nạp xong {len(docs_to_insert)} đoạn cho {culture_type}")

# ====== 3. ROUTER ======
from my_semantic_logic.samples import roiNuocSample, hoangThanhSample, chitchatSample
routes = [
    Route(name="roi_nuoc", samples=roiNuocSample),
    Route(name="hoang_thanh", samples=hoangThanhSample),
    Route(name="chitchat", samples=chitchatSample),
]
# Router dùng OpenAIEncoder nên khởi động mất 1 giây
router = RouteLayer(encoder=encoder, routes=routes)

# ====== 4. MODELS ======
class ChatRequest(BaseModel):
    user_input: str
    history: List[Dict[str, str]]

class ChatResponse(BaseModel):
    answer: str
    rewritten_query: str
    route: str
    score: float
    audio_base64: Optional[str] = None
    context_used: Optional[str] = None

# ====== 5. LIFESPAN ======
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not REDIS_URL: raise ValueError("❌ Lỗi: REDIS_URL chưa có")
    
    app.state.redis = redis.from_url(REDIS_URL, decode_responses=True)
    app.state.openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    app.state.reflector = Reflection(llm_client=app.state.openai_client)
    
    # Tự động nạp dữ liệu OpenAI khi khởi động
    await auto_ingest_data(vector_db, app.state.openai_client)
    yield
    await app.state.redis.close()

app = FastAPI(title="Heritage NPC API", lifespan=lifespan)

# THÊM CORS ĐỂ FRONTEND TRUY CẬP ĐƯỢC
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_db = VectorDatabase(db_name=DB_NAME)

# ====== 6. UTILS (TTS) ======
async def generate_audio_async(text: str) -> str:
    try:
        clean_text = re.sub(r'[*_#]', '', text).strip()
        lang = "vi-VN-HoaiMyNeural"
        try:
            if detect(clean_text[:30]) == 'en': lang = "en-US-GuyNeural"
        except: pass
        communicate = Communicate(clean_text, lang)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": audio_data += chunk["data"]
        return base64.b64encode(audio_data).decode()
    except: return ""

# ====== 7. ENDPOINT CHÍNH ======
@app.post("/process_query", response_model=ChatResponse)
async def process_query(request: ChatRequest):
    try:
        redis_conn = app.state.redis
        client = app.state.openai_client
        reflector = app.state.reflector
        
        user_input = request.user_input.strip()
        history = request.history[-5:]

        # 1. Router
        guide_res = router(user_input)
        route_name = guide_res.name if guide_res.name else "uncertain"
        score = 1.0 # SemanticRouter mới trả về object

        # 2. Xử lý Chitchat sớm
        if route_name == "chitchat":
            ans = "Chào bạn! Mình là Minh. Bạn cần mình giúp gì về văn hóa Việt Nam không?"
            return ChatResponse(answer=ans, rewritten_query=user_input, route=route_name, score=score, audio_base64=await generate_audio_async(ans))

        # 3. Rewrite câu hỏi
        rewritten = await reflector.rewrite(history, user_input)
        
        # 4. Check Cache
        cache_key = f"cache:{rewritten.lower()}"
        cached_data = await redis_conn.get(cache_key)
        if cached_data: return ChatResponse(**json.loads(cached_data))

        # 5. HYBRID RAG
        # Bước A: Lấy OpenAI Embedding cho câu hỏi
        q_vec = await get_openai_embedding(rewritten, client)
        
        # Bước B: Tìm kiếm Vector (Giờ là 1536 chiều)
        candidates = vector_db.query(COLLECTION_NAME, q_vec, limit=10)
        
        if not candidates:
            ans = "Tiếc quá, hiện tại mình chưa có thông tin về phần này."
            return ChatResponse(answer=ans, rewritten_query=rewritten, route=route_name, score=score, audio_base64=await generate_audio_async(ans))

        # Bước C: Reranking
        for res in candidates:
            res['hybrid_score'] = res.get('score', 0) + (simple_keyword_score(res['content'], rewritten) * 0.15) 

        candidates.sort(key=lambda x: x['hybrid_score'], reverse=True)
        context = "\n\n".join([r["content"] for r in candidates[:3]])

        # 6. Generate Answer
        final_res = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Bạn là NPC tên Minh. Trả lời thân thiện dựa trên CONTEXT. Nếu không có thông tin, hãy xin lỗi."},
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nQ: {rewritten}"}
            ],
            temperature=0.3
        )
        answer = final_res.choices[0].message.content
        audio_b64 = await generate_audio_async(answer)

        response_data = ChatResponse(
            answer=answer, rewritten_query=rewritten, route=route_name,
            score=score, audio_base64=audio_b64, context_used=context[:150] + "..."
        )

        await redis_conn.setex(cache_key, 3600, response_data.model_dump_json())
        return response_data

    except Exception as e:
        logger.error(f"❌ Server Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "NPC Minh API is online!", "mode": "OpenAI-Lightweight"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)