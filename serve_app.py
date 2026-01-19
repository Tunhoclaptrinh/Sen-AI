import os
import base64
import re
import json
import logging
from typing import List, Dict, Optional
from contextlib import asynccontextmanager
import time
import sys
import socket
import asyncio
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request
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
from my_semantic_logic.route import Route
from my_semantic_logic.router import SemanticRouter
import my_semantic_logic.samples as samples

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

# ====== 5. LIFESPAN (Include Startup Logic Here) ======

def get_network_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    if not REDIS_URL:
        raise ValueError("❌ Lỗi: REDIS_URL chưa được khai báo trong .env")
        
    app.state.redis = redis.from_url(REDIS_URL, decode_responses=True)
    app.state.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    app.state.reflector = Reflection(llm_client=app.state.openai_client)
    
    # auto_ingest_data(vector_db) # User has this commented out in their snippet
    
    # Print Banner
    port = 8000
    network_ip = get_network_ip()
    env = os.getenv("ENV", "development")
    
    print(f"\n✅ Server restart triggered at {time.strftime('%Y-%m-%dT%H:%M:%S.000Z')}", flush=True)
    
    import unicodedata

    def get_visual_width(s):
        width = 0
        for char in s:
            # Explicitly handle Emoji ranges and specific symbols that render wide
            code = ord(char)
            if (0x1F000 <= code <= 0x1F9FF) or (code == 0x2764) or (code == 0x2699):
                width += 2
                continue

            # Standard East Asian Width
            if unicodedata.east_asian_width(char) in ('W', 'F'):
                width += 2
            else:
                width += 1
        return width

    def print_line(icon, label, value, width=62):
        # Format: "   ICON  Label....... Value"
        label_part = f"{label:<13}"
        text = f"   {icon}  {label_part} {value}"
        
        # Robustly calculate exact visual display width
        vis_len = get_visual_width(text)
        
        padding = width - vis_len
        if padding < 0: padding = 0
        
        print(f"║{text}{' ' * padding}║", flush=True)

    border_width = 62
    border = "═" * border_width
    
    print(f"╔{border}╗", flush=True)
    
    # Center Title
    title_text = "🏛️   Sen Server Started!"
    title_vis_len = get_visual_width(title_text)
    total_pad = border_width - title_vis_len
    left_pad = total_pad // 2
    right_pad = total_pad - left_pad
    print(f"║{' ' * left_pad}{title_text}{' ' * right_pad}║", flush=True)
    
    print(f"╠{border}╣", flush=True)
    print_line("📍", "Local:", f"http://localhost:{port}", border_width)
    print_line("📡", "Network:", f"http://{network_ip}:{port}", border_width)
    print_line("🌍", "Env:", f"{env}", border_width)
    print(f"╠{border}╣", flush=True)
    print_line("📊", "API Docs:", f"http://localhost:{port}/docs", border_width)
    print_line("❤️", "Health:", f"http://localhost:{port}/", border_width)
    print(f"╚{border}╝", flush=True)

    yield
    
    # --- SHUTDOWN LOGIC ---
    await app.state.redis.close()

app = FastAPI(title="Heritage AI API", lifespan=lifespan)
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

# ====== MIDDLEWARE LOGGING (PURE ASGI - ROBUST) ======

def console_log(*args):
    print(*args, flush=True)

class ASGILoggerMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "https"):
            return await self.app(scope, receive, send)

        # 1. Setup Request Logging
        start_time = time.time()
        method = scope["method"]
        path = scope["path"]
        query_string = scope.get("query_string", b"").decode()
        
        # 2. Log Request (NO BODY, as requested)
        console_log(f"\n📥 REQUEST → {method} {path}")
        if query_string:
            try:
                parsed = parse_qs(query_string)
                clean_params = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
                console_log("   Query:", clean_params)
            except:
                console_log("   Query:", query_string)
        
        # 3. Wrap Send to capture Response
        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                process_time = (time.time() - start_time) * 1000
                console_log(f"📤 RESPONSE ← {method} {path}")
                console_log(f"   Status: {status_code}")
                console_log(f"   Time: {process_time:.2f}ms")
            await send(message)

        await self.app(scope, receive, wrapped_send)

# Replace the old middleware with the new pure ASGI one
app.add_middleware(ASGILoggerMiddleware)


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
            ans = "Chào bạn! Mình là Sen. Bạn cần mình giúp gì về văn hóa Việt Nam không?"
            resp = ChatResponse(answer=ans, rewritten_query=user_input, route=route_name, score=score, audio_base64=await generate_audio_async(ans))
            console_log("   Response:", resp.model_dump()) # Added manual log
            return resp

        # 3. Rewrite câu hỏi (GPT fix không dấu, lỗi chính tả ở đây)
        rewritten = await reflector.rewrite(history, user_input)
        
        # 4. Check Cache
        cache_key = f"cache:{rewritten.lower()}"
        cached_data = await redis_conn.get(cache_key)
        if cached_data:
            logger.info("🚀 Cache Hit!")
            data = json.loads(cached_data)
            resp = ChatResponse(**data)
            console_log("   Response:", data) # Added manual log
            return resp

        # 5. [NÂNG CẤP] HYBRID RAG PIPELINE (Vector + Keyword)
        
        # Bước A: Tìm kiếm Vector (Lấy 10 ứng viên)
        q_vec = local_embedder.encode([rewritten])[0].tolist()
        candidates = vector_db.query(COLLECTION_NAME, q_vec, limit=10, filter_dict=filter_dict)
        
        if not candidates:
            ans = "Tiếc quá, hiện tại mình chưa có thông tin về phần này."
            resp = ChatResponse(answer=ans, rewritten_query=rewritten, route=route_name, score=score, audio_base64=await generate_audio_async(ans))
            console_log("   Response:", resp.model_dump()) # Added manual log
            return resp

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
                {"role": "system", "content": "Bạn là AI tên Sen. Trả lời thân thiện dựa trên CONTEXT được cung cấp. Nếu không có trong context, hãy xin lỗi khéo léo."},
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
        
        console_log("   Response:", response_data.model_dump()) # Added manual log
        return response_data

    except Exception as e:
        logger.error(f"❌ Server Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 8. Endpoint Root
@app.get("/")
async def root():
    return {
        "message": "AI Sen API is running!",
        "status": "online",
        "author": "Hieu"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)