import os
import base64
import re
import json
import logging
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI 
import redis.asyncio as redis 
from edge_tts import Communicate
from langdetect import detect
from sentence_transformers import SentenceTransformer

# Các bộ chia nhỏ văn bản (Cần thiết cho Ingest)
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# Module tùy chỉnh của Hiếu
from vector_db import VectorDatabase
from reflection import Reflection
from semantic_router.route import Route
from semantic_router.router import SemanticRouter
import semantic_router.samples as samples

# ====== 1. CẤU HÌNH GLOBAL ======
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "vector_db"
COLLECTION_NAME = "culture"
REDIS_URL = os.getenv("REDIS_URL")

# Model 384 chiều dùng cho cả Router và Search
local_embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Đường dẫn file dữ liệu
CULTURE_FILES = [
    ("mua_roi_nuoc", "mua_roi_nuoc.md"),
    ("hoang_thanh", "hoang_thanh.md"),
]

# ====== 2. HÀM HỖ TRỢ NẠP DỮ LIỆU & LOGIC HYBRID ======

def simple_keyword_score(content: str, rewritten_query: str) -> float:
    """
    [MỚI BỔ SUNG] 
    Tính điểm thưởng dựa trên mức độ trùng lặp từ vựng giữa câu hỏi và nội dung.
    """
    content_lower = content.lower()
    # Tách từ, bỏ qua các từ quá ngắn (như 'là', 'ở', 'có')
    query_words = [w for w in rewritten_query.lower().split() if len(w) > 2]
    
    if not query_words:
        return 0.0
    
    matched_count = 0
    for word in query_words:
        if word in content_lower:
            matched_count += 1
            
    return matched_count / len(query_words)

def chunk_markdown(md_text: str) -> List[Dict]:
    headers_to_split_on = [("#", "h1"), ("##", "h2"), ("###", "h3")]
    splitter1 = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    sections = splitter1.split_text(md_text)
    splitter2 = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=180)
    docs = splitter2.split_documents(sections)
    return [{"content": d.page_content.strip(), "metadata": d.metadata} for d in docs if d.page_content.strip()]

def auto_ingest_data(v_db: VectorDatabase):
    """Kiểm tra và tự động nạp dữ liệu 384 chiều nếu DB trống"""
    for culture_type, file_path in CULTURE_FILES:
        if v_db.count_documents(COLLECTION_NAME, {"culture_type": culture_type}) == 0:
            if os.path.exists(file_path):
                logger.info(f"🔄 Đang nạp lại dữ liệu 384 chiều cho: {culture_type}")
                with open(file_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                
                chunks = chunk_markdown(md_content)
                vectors = local_embedder.encode([c["content"] for c in chunks]).tolist()
                
                docs_to_insert = [
                    {
                        "content": c["content"],
                        "embedding": vectors[i],
                        "culture_type": culture_type,
                        "metadata": c["metadata"]
                    } for i, c in enumerate(chunks)
                ]
                v_db.insert_many(COLLECTION_NAME, docs_to_insert)
                logger.info(f"✅ Đã nạp xong {len(docs_to_insert)} đoạn cho {culture_type}")
            else:
                logger.warning(f"⚠️ Không tìm thấy file {file_path}")

# ====== 3. ROUTER ======
routes = [
    Route(name="roi_nuoc", samples=samples.roiNuocSample, filter_dict={"culture_type": "mua_roi_nuoc"}),
    Route(name="hoang_thanh", samples=samples.hoangThanhSample, filter_dict={"culture_type": "hoang_thanh"}),
    Route(name="chitchat", samples=samples.chitchatSample, filter_dict={}),
]
router = SemanticRouter(embedding=local_embedder, routes=routes, threshold=0.5)

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
    if not REDIS_URL:
        raise ValueError("❌ Lỗi: REDIS_URL chưa được khai báo trong .env")
        
    app.state.redis = redis.from_url(REDIS_URL, decode_responses=True)
    app.state.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    app.state.reflector = Reflection(llm_client=app.state.openai_client)
    
    # auto_ingest_data(vector_db)
    yield
    await app.state.redis.close()

app = FastAPI(title="Heritage NPC API", lifespan=lifespan)
vector_db = VectorDatabase(db_name=DB_NAME)

# ====== 6. UTILS ======
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

        # 1. Router câu gốc
        score_raw, route_name, filter_dict = router.guide(user_input)
        score = float(score_raw.item()) if hasattr(score_raw, 'item') else float(score_raw)

        # 2. Xử lý Chitchat sớm
        if score > 0.7 and route_name in ("uncertain", "chitchat"):
            ans = "Chào bạn! Mình là Minh. Bạn cần mình giúp gì về văn hóa Việt Nam không?"
            return ChatResponse(answer=ans, rewritten_query=user_input, route=route_name, score=score, audio_base64=await generate_audio_async(ans))

        # 3. Rewrite câu hỏi (GPT fix không dấu, lỗi chính tả ở đây)
        rewritten = await reflector.rewrite(history, user_input)
        
        # 4. Check Cache
        cache_key = f"cache:{rewritten.lower()}"
        cached_data = await redis_conn.get(cache_key)
        if cached_data:
            logger.info("🚀 Cache Hit!")
            return ChatResponse(**json.loads(cached_data))

        # 5. [NÂNG CẤP] HYBRID RAG PIPELINE (Vector + Keyword)
        
        
        # Bước A: Tìm kiếm Vector (Lấy 10 ứng viên)
        q_vec = local_embedder.encode([rewritten])[0].tolist()
        candidates = vector_db.query(COLLECTION_NAME, q_vec, limit=10, filter_dict=filter_dict)
        
        if not candidates:
            ans = "Tiếc quá, hiện tại mình chưa có thông tin về phần này."
            return ChatResponse(answer=ans, rewritten_query=rewritten, route=route_name, score=score, audio_base64=await generate_audio_async(ans))

        # Bước B: Reranking bằng Keyword Score
        for res in candidates:
            v_score = res.get('score', 0)  # Điểm tương đồng từ Vector DB
            k_score = simple_keyword_score(res['content'], rewritten) # Điểm khớp từ khóa
            
            # Tính điểm lai: Vector đóng góp chính, Keyword cộng thêm điểm thưởng
            res['hybrid_score'] = v_score + (k_score * 0.15) 

        # Bước C: Sắp xếp lại danh sách theo điểm Hybrid
        candidates.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        # Bước D: Lấy Top 3 đoạn Context sát ý nhất
        top_3_results = candidates[:3]
        context = "\n\n".join([r["content"] for r in top_3_results])
        logger.info(f"✅ Hybrid Search thành công. Top score: {candidates[0]['hybrid_score']:.2f}")

        # 6. Generate Answer (GPT-4o-mini)
        final_res = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Bạn là NPC tên Minh. Trả lời thân thiện dựa trên CONTEXT được cung cấp. Nếu không có trong context, hãy xin lỗi khéo léo."},
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

        # 7. Lưu cache (Hết hạn sau 1 tiếng)
        await redis_conn.setex(cache_key, 3600, response_data.model_dump_json())
        return response_data

    except Exception as e:
        logger.error(f"❌ Server Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 1. Thêm cái này TRƯỚC khối __main__
@app.get("/")
async def root():
    return {
        "message": "NPC Minh API is running!",
        "status": "online",
        "author": "Hieu"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
