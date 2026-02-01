import base64
import re
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List
from edge_tts import Communicate
import redis.asyncio as redis
from dotenv import load_dotenv
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer
from vector_db import VectorDatabase
from knowledge_base import KnowledgeBase
from heritage_tool import HeritageTools
import logging
import os
import asyncio
from agentic_rag_workflow import agentic_workflow
import io
from uuid import uuid4
import edge_tts
import tempfile

# Tải .env để lấy các biến môi trường
load_dotenv()
ENABLE_FILE_LOGGING = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"

# Khởi tạo ứng dụng FastAPI
app = FastAPI()

# Cấu hình CORS để cho phép Admin Dashboard (hoặc frontend khác) gọi API
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn (trong môi trường dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Khởi tạo logger
logger = logging.getLogger("uvicorn")

async def generate_tts(text: str) -> str:
    """
    Generate Text-to-Speech: Edge TTS (Primary) -> Google TTS (Fallback).
    Returns: Base64 encoded audio string.
    """
    # 1. Remove Markdown links: [Text](URL) -> Text
    # This ensures TTS reads the description but skips the http link
    clean_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)

    # 2. Remove standalone URLs (http/https)
    clean_text = re.sub(r'http[s]?://\S+', '', clean_text)
    
    # 3. Remove Markdown chars (*, _, `, ~)
    clean_text = re.sub(r'[*_`~]', '', clean_text)

    # 4. Remove ALL Emojis (Unicode ranges for symbols, pictographs, etc.)
    # Range includes: 1F600-1F64F (Emoticons), 1F300-1F5FF (Symbols), 1F680-1F6FF (Transport), etc.
    clean_text = re.sub(r'[^\w\s,.;:?!áàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ]', '', clean_text)
    
    # 5. Clean up extra spaces
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    temp_dir = tempfile.gettempdir()
    output_file = os.path.join(temp_dir, f"temp_tts_{uuid4()}.mp3")
    
    # 1. Thử Edge TTS (Giọng hay)
    VOICE_CANDIDATES = ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"]
    for voice in VOICE_CANDIDATES:
        try:
            # Tăng tốc độ đọc lên đáng kể theo yêu cầu
            communicate = edge_tts.Communicate(clean_text, voice, rate="+30%")
            await communicate.save(output_file)
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 100:
                with open(output_file, "rb") as f: audio_data = f.read()
                os.remove(output_file)
                return base64.b64encode(audio_data).decode()
        except Exception as e:
            logger.warning(f"⚠️ Edge TTS ({voice}) failed: {e}")
            if os.path.exists(output_file): os.remove(output_file)
            continue

    # 2. Fallback: Google TTS (Giọng ổn định)
    try:
        try:
            from gtts import gTTS
        except ImportError:
            logger.error("❌ Thư viện 'gTTS' chưa được cài đặt! Đang cố gắng import nhưng thất bại.")
            raise

        logger.info("🔄 Switching to Google TTS fallback...")
        tts = gTTS(text=clean_text, lang='vi')
        tts.save(output_file)
        
        with open(output_file, "rb") as f: audio_data = f.read()
        os.remove(output_file)
        return base64.b64encode(audio_data).decode()
    except Exception as e:
        logger.error(f"❌ Google TTS also failed: {e}")
        return ""

# Khởi tạo các thành phần cần thiết cho ứng dụng
@app.on_event("startup")
async def startup():
    # Khởi tạo Redis kết nối
    app.state.redis = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
    
    # Khởi tạo OpenAI API
    app.state.openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Khởi tạo Vector Database và Sentence Transformer cho KnowledgeBase
    v_db = VectorDatabase(db_name="vector_db")
    embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # Khởi tạo KnowledgeBase cho việc lưu trữ và truy vấn dữ liệu
    app.state.brain = KnowledgeBase(v_db, embedder)
    
    # Khởi tạo Verifier module
    from verifier import Verifier
    app.state.verifier = Verifier(app.state.openai)
    
    # Khởi tạo HeritageTools để lấy thông tin thời gian thực
    app.state.tools = HeritageTools()
    
    # Thêm hàm generate_tts vào app.state để có thể truy cập từ workflow
    app.state.generate_tts = generate_tts

# Định nghĩa dữ liệu đầu vào (câu hỏi và lịch sử)
class ChatRequest(BaseModel):
    user_input: str
    history: List[dict] = []
    session_id: Optional[str] = None
    use_verifier: bool = False

@app.on_event("shutdown")
async def shutdown():
    # Đóng kết nối Redis khi ứng dụng dừng
    if hasattr(app.state, 'redis'):
        await app.state.redis.close()
    else:
        logger.warning("Redis không được khởi tạo, không thể đóng kết nối.")

@app.get("/chat")
async def chat_get_info():
    """
    Endpoint GET để hướng dẫn người dùng nếu họ truy cập nhầm bằng trình duyệt.
    """
    return {
        "message": "Đây là API Chat (POST). Bạn không thể truy cập trực tiếp bằng trình duyệt (GET).",
        "instruction": "Vui lòng sử dụng method POST với body JSON: {'user_input': '...'}",
        "docs": "Truy cập /docs để test API."
    }

@app.post("/chat")
async def chat_api(request: ChatRequest):
    """
    API chính nhận câu hỏi từ người dùng.
    Flow: LLM (detect intent) → [CHITCHAT: return ngay] [REALTIME/HERITAGE: cache check → Process → Cache save]
    """
    try:
        import json
        
        # 🔴 BƯỚC 1: Gọi LLM trước để phân loại intent (chitchat, realtime, rag)
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 INPUT: {request.user_input}")
        logger.info(f"{'='*80}")
        
        # Gọi workflow để LLM phân loại
        result = await agentic_workflow(request.user_input, request.history, app.state)
        intent = result.get("intent", "chitchat")
        
        logger.info(f"📋 Intent detected: {intent}")
        
        # ✨ CHITCHAT: Response ngay (tính tế, không cache)
        if intent == "chitchat":
            logger.info(f"💬 CHITCHAT mode: Response ngay, không dùng cache")
            result["from_cache"] = False
            return result
        
        # 🔴 BƯỚC 2: Normalize input để tạo cache key (cho realtime/heritage)
        normalized_input = " ".join(request.user_input.lower().split())
        cache_key = f"sen:cache:{normalized_input}"
        
        # 🔴 BƯỚC 3: Kiểm tra Redis (chỉ cache realtime/heritage)
        logger.info(f"🔍 Kiểm tra cache Redis: {cache_key}")
        cached_result = await app.state.redis.get(cache_key)
        
        if cached_result:
            logger.info(f"✅ [Step 10] FINISHED (Cache Hit). Data Source: 💾 CACHE (Redis)")
            final_res = json.loads(cached_result)
            final_res["from_cache"] = True
            return final_res
        
        logger.info(f"❌ MISS CACHE. Sử dụng kết quả vừa tính từ LLM")
        
        # Kết quả đã có từ BƯỚC 1, không cần gọi lại workflow
        result["from_cache"] = False
        
        # 🔴 BƯỚC 4: Lưu kết quả vào cache (realtime/rag: 30 phút để có data mới)
        cache_ttl = 1800  # 30 minutes cho realtime/heritage
        await app.state.redis.setex(cache_key, cache_ttl, json.dumps(result, ensure_ascii=False))
        logger.info(f"💾 Lưu cache với TTL {cache_ttl}s: {cache_key} (intent: {intent})")
        
        return result
    except Exception as e:
        logger.error(f"❌ Lỗi xử lý câu hỏi: {str(e)}", exc_info=True)
        import traceback
        return {"error": "Có lỗi xảy ra trong quá trình xử lý yêu cầu.", "details": str(e), "traceback": traceback.format_exc()}

from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream_api(request: ChatRequest):
    """
    API Streaming (SSE) cho phép UI hiển thị trạng thái "Thinking..." theo thời gian thực.
    Client sẽ nhận được các event JSON line-by-line.
    Hỗ trợ Redis Session History nếu có session_id.
    """
    import json
    
    # [Start] Load History from Redis if session_id provided
    history = request.history
    redis_key = None
    
    if request.session_id:
        redis_key = f"chat_history:{request.session_id}"
        try:
            cached_hist = await app.state.redis.get(redis_key)
            if cached_hist:
                history = json.loads(cached_hist)
                logger.info(f"📜 Loaded {len(history)} turns from Redis session: {request.session_id}")
        except Exception as e:
            logger.error(f"❌ Redis History Load Error: {e}")

    async def event_generator():
        try:
            from agentic_rag_workflow import agentic_workflow_stream
            
            # [Step 1] Initial Log
            yield json.dumps({"status": "start", "message": "Bắt đầu xử lý..."}) + "\n"
            
            full_final_res = None

            # [Core Pipeline]
            async for event in agentic_workflow_stream(request.user_input, history, app.state, use_verifier=request.use_verifier):
                yield json.dumps(event) + "\n"
                
                # Check for finish event to save history
                if event.get("status") == "finished":
                    full_final_res = event.get("result")

            # [Step End] Post-processing (Save History)
            if full_final_res:
                try:
                    answer = full_final_res.get("answer", "")
                    site_hint = full_final_res.get("site") 
                    
                    if answer:
                        from datetime import datetime
                        from uuid import uuid4
                        import os
                        
                        # Tạo entry
                        new_entry = {
                            "id": str(uuid4()),
                            "user_id": getattr(request, "user_id", "anonymous"),
                            "level_id": getattr(request, "level_id", 1),
                            "character_id": getattr(request, "character_id", 1),
                            "message": request.user_input,
                            "response": answer,
                            "audio_base64": full_final_res.get("audio", ""),
                            "context": {
                                "characterId": getattr(request, "character_id", 1),
                                "rewritten": full_final_res.get("debug_info", {}).get("rewritten", ""),
                                "intent": full_final_res.get("intent", "unknown"),
                                "site": site_hint
                            },
                            "created_at": datetime.utcnow().isoformat() + "Z",
                            "user_input": request.user_input, "generated_answer": answer, "site": site_hint
                        }
                        
                        # 1. Update in-memory history (cho redis)
                        history.append(new_entry)
                        
                        # 2. Save to Redis (if session exists)
                        if redis_key:
                            trimmed_history = history[-20:]
                            await app.state.redis.set(redis_key, json.dumps(trimmed_history, ensure_ascii=False))
                            logger.info(f"💾 Saved to Redis: {redis_key}")
                            
                        # 3. [DEV] Save to local JSON file (Append mode logic)
                        if ENABLE_FILE_LOGGING:
                            log_file = "chat_logs.json"
                            try:
                                current_logs = []
                                if os.path.exists(log_file):
                                    with open(log_file, "r", encoding="utf-8") as f:
                                        try: 
                                            current_logs = json.load(f)
                                            if not isinstance(current_logs, list): current_logs = []
                                        except: current_logs = []
                                        
                                current_logs.append(new_entry)
                                
                                with open(log_file, "w", encoding="utf-8") as f:
                                    json.dump(current_logs, f, ensure_ascii=False, indent=2)
                                logger.info(f"📁 Appended log to {log_file}")
                            except Exception as file_e:
                                logger.error(f"❌ File Save Error: {file_e}")

                except Exception as e:
                    logger.error(f"❌ Post-processing Error: {e}")

        except Exception as e:
            yield json.dumps({"status": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

class TTSRequest(BaseModel):
    text: str

@app.post("/api/tts")
async def tts_endpoint(req: TTSRequest):
    """
    API chuyển văn bản thành giọng nói (TTS).
    Trả về chuỗi base64 của file âm thanh.
    """
    if not req.text:
        return {"audio": ""}
    
    # Sử dụng hàm generate_tts có sẵn
    audio_base64 = await generate_tts(req.text)
    return {"audio": audio_base64}

@app.post("/chat-audio")
async def chat_audio_api(
    audio_file: UploadFile = File(...),
    history: str = ""
):
    """
    API nhận audio từ người dùng.
    Flow: Audio → STT (Whisper) → Text → agentic_workflow → TTS → Audio output
    """
    try:
        import json
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🎙️ AUDIO INPUT: {audio_file.filename}")
        logger.info(f"{'='*80}")
        
        # 🔴 BƯỚC 1: Convert audio to text (STT using OpenAI Whisper)
        logger.info(f"🔄 STT: Chuyển audio thành text...")
        audio_data = await audio_file.read()
        
        # Gọi OpenAI Whisper API
        transcript = await app.state.openai.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.webm", io.BytesIO(audio_data), "audio/webm")
        )
        
        user_input = transcript.text
        logger.info(f"✅ STT Result: {user_input}")
        
        # Parse history từ JSON string
        try:
            history_list = json.loads(history) if history else []
        except:
            history_list = []
        
        # 🔴 BƯỚC 2: Gọi agentic_workflow như endpoint /chat
        result = await agentic_workflow(user_input, history_list, app.state)
        intent = result.get("intent", "chitchat")
        
        logger.info(f"📋 Intent detected: {intent}")
        
        # 🔴 BƯỚC 3: CHITCHAT → return ngay
        if intent == "chitchat":
            logger.info(f"💬 CHITCHAT mode: Response ngay, không dùng cache")
            result["from_cache"] = False
            result["transcribed_text"] = user_input  # Thêm text đã transcribe
            return result
        
        # 🔴 BƯỚC 4: REALTIME/HERITAGE → check cache
        normalized_input = " ".join(user_input.lower().split())
        cache_key = f"sen:cache:{normalized_input}"
        
        logger.info(f"🔍 Kiểm tra cache Redis: {cache_key}")
        cached_result = await app.state.redis.get(cache_key)
        
        if cached_result:
            logger.info(f"✅ [Step 10] FINISHED (Cache Hit). Data Source: 💾 CACHE (Redis)")
            cached_result_obj = json.loads(cached_result)
            cached_result_obj["from_cache"] = True
            cached_result_obj["cache_key"] = cache_key
            cached_result_obj["transcribed_text"] = user_input
            return cached_result_obj
        
        logger.info(f"❌ MISS CACHE. Sử dụng kết quả vừa tính từ LLM")
        
        result["from_cache"] = False
        result["transcribed_text"] = user_input
        
        # 🔴 BƯỚC 5: Lưu kết quả vào cache
        cache_ttl = 1800  # 30 minutes
        await app.state.redis.setex(cache_key, cache_ttl, json.dumps(result, ensure_ascii=False))
        logger.info(f"💾 Lưu cache với TTL {cache_ttl}s: {cache_key} (intent: {intent})")
        
        return result
        
    except Exception as e:
        # Xử lý lỗi Audio ngắn hoặc lỗi OpenAI
        error_msg = str(e)
        logger.error(f"❌ Lỗi xử lý audio: {error_msg}", exc_info=True)
        
        friendly_msg = "Dạ, Sen đang gặp chút trục trặc khi nghe. Bác nói lại giúp Sen nhé!"
        transcribed = "(Lỗi kỹ thuật)"

        if "audio_too_short" in error_msg or "Minimum audio length" in error_msg:
             friendly_msg = "Dạ Sen nghe chưa rõ, bác nói lại dài hơn chút nhé! 🎤"
             transcribed = "(Âm thanh quá ngắn)"
        
        # Generate TTS for error message to keep UX consistent
        try:
            audio_b64 = await generate_tts(friendly_msg)
        except:
            audio_b64 = ""

        return {
           "intent": "chitchat",
           "answer": friendly_msg,
           "transcribed_text": transcribed,
           "from_cache": False,
           "audio": audio_b64
        }


@app.get("/")
async def health():
    """
    Endpoint kiểm tra trạng thái hệ thống.
    """
    return {"status": "Sen NPC Online! ✨"}

@app.get("/data-source")
async def data_source_info():
    """
    Endpoint kiểm tra nguồn dữ liệu hiện tại đang sử dụng.
    Trả về thông tin về dữ liệu cào (scraped) hay default (hardcoded).
    """
    from data_manager import get_data_source_info
    info = get_data_source_info()
    return {
        "data_source": info,
        "message": "🔄 Dữ liệu được load từ file JSON (data/monuments.json). Chỉnh sửa file này để thêm/bớt di tích."
    }



@app.get("/cache/stats")
async def cache_stats():
    """
    Endpoint kiểm tra thống kê cache redis.
    Hiển thị danh sách các câu hỏi đã cache và TTL còn lại.
    """
    try:
        # Lấy tất cả keys trong redis có pattern "sen:cache:*"
        keys = await app.state.redis.keys("sen:cache:*")
        
        cache_entries = []
        for key in keys:
            ttl = await app.state.redis.ttl(key)
            data = await app.state.redis.get(key)
            
            # Extract query from cache key
            query = key.replace("sen:cache:", "")
            
            try:
                parsed_data = json.loads(data)
                cache_entries.append({
                    "query": query,
                    "key": key,
                    "ttl_seconds": ttl,
                    "intent": parsed_data.get("intent"),
                    "answer_preview": parsed_data.get("answer", "")[:50],
                    "data_source": parsed_data.get("data_source", {}).get("final_context_source")
                })
            except:
                pass
        
        return {
            "total_cached_queries": len(cache_entries),
            "cache_entries": sorted(cache_entries, key=lambda x: x["ttl_seconds"], reverse=True),
            "message": f"📊 Có {len(cache_entries)} câu hỏi trong cache. TTL: giây"
        }
    except Exception as e:
        logger.error(f"❌ Error getting cache stats: {e}")
        return {"error": str(e), "cache_entries": []}

@app.post("/cache/clear")
async def clear_cache():
    """
    Endpoint xóa toàn bộ cache redis (Public for now, should move to admin router).
    """
    try:
        keys = await app.state.redis.keys("sen:cache:*")
        if keys:
            await app.state.redis.delete(*keys)
            logger.info(f"🗑️ Xóa {len(keys)} entries khỏi cache")
            return {"status": "success", "message": f"✅ Đã xóa sạch {len(keys)} records trong Cache!", "deleted_count": len(keys)}
        else:
            return {"status": "success", "message": "ℹ️ Cache đã trống sẵn, không cần xóa.", "deleted_count": 0}
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}")
        return {"status": "error", "message": str(e)}

@app.delete("/cache/{query}")
async def delete_cache_entry(query: str):
    """
    Endpoint xóa một entry cụ thể trong cache.
    """
    try:
        normalized_query = " ".join(query.lower().split())
        cache_key = f"sen:cache:{normalized_query}"
        
        result = await app.state.redis.delete(cache_key)
        
        if result:
            logger.info(f"🗑️ Xóa cache entry: {cache_key}")
            return {"message": f"✅ Xóa cache entry thành công: {query}", "deleted": True}
        else:
            return {"message": f"ℹ️ Không tìm thấy cache entry: {query}", "deleted": False}
    except Exception as e:
        logger.error(f"❌ Error deleting cache entry: {e}")
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        
        # Determine Input Type
        # msg_type = data.get("type", "text_input") # default to text if missing
        # user_input = ""
        
        # if msg_type == "audio_input":
        #      audio_b64 = data.get("audio")
        #      if audio_b64:
        #          import io
        #          # Decode Base64
        #          audio_bytes = base64.b64decode(audio_b64)
        #          # Transcribe via Whisper
        #          transcript = await app.state.openai.audio.transcriptions.create(
        #             model="whisper-1",
        #             file=("audio.webm", io.BytesIO(audio_bytes), "audio/webm")
        #          )
        #          user_input = transcript.text
        #          logger.info(f"🎙️ WS Audio Transcribed: {user_input}")
                 
        #          # Send transcription back to UI (optional but good for UX)
        #          await websocket.send_json({"type": "text", "content": f"🎤 {user_input}"}) # Or logic to show user prompt
        
        # elif msg_type == "text_input":
        #      user_input = data.get("text")
             
        # # Fallback / Legacy
        # if not user_input:
        #      user_input = data.get("user_input", "")

        session_id = data.get("session_id")
        history = data.get("history", [])

        # [Redis Load]
        redis_key = None
        if session_id:
            redis_key = f"chat_history:{session_id}"
            try:
                cached = await app.state.redis.get(redis_key)
                if cached:
                    import json
                    history = json.loads(cached)
            except Exception as e:
                logger.error(f"WS Redis Load Error: {e}")

        # Processing
        from agentic_rag_workflow import agentic_workflow_stream
        import json
        
        buffer = ""
        full_answer = ""
        full_final_res = None
        
        await websocket.send_json({"type": "status", "message": "Thinking..."})

        async for event in agentic_workflow_stream(user_input, history, app.state):
            # 1. Forward process events
            if event.get("status") in ["processing", "start"]:
                await websocket.send_json({"type": "status", "message": event.get("message")})
            
            # 2. Text Streaming & TTS Buffering
            if event.get("status") == "streaming":
                chunk = event.get("content", "")
                full_answer += chunk
                buffer += chunk
                
                # Send text chunk immediately
                await websocket.send_json({"type": "text", "content": chunk})
                
                # Check sentence end for TTS
                if re.search(r'[.!?\n]+$', buffer.strip()) and len(buffer.strip()) > 10:
                    # Generate Audio for this sentence
                    logging.info(f"🎤 Auto-TTS Sentence: {buffer[:20]}...")
                    audio_b64 = await generate_tts(buffer)
                    if audio_b64:
                        await websocket.send_json({"type": "audio", "data": audio_b64})
                    buffer = "" # Reset buffer
            
            # 3. Handle Finish
            if event.get("status") == "finished":
                full_final_res = event.get("result")
                # Flush remaining buffer
                if buffer.strip():
                     audio_b64 = await generate_tts(buffer)
                     if audio_b64:
                        await websocket.send_json({"type": "audio", "data": audio_b64})

        # [Save Logic] (Redis + File)
        await websocket.send_json({"type": "finished", "data": full_final_res})
        
        if full_final_res:
             try:
                answer = full_final_res.get("answer", "")
                site_hint = full_final_res.get("site")
                if answer:
                    from datetime import datetime
                    from uuid import uuid4
                    import os
                    
                    new_entry = {
                        "id": str(uuid4()),
                        "user_id": data.get("user_id", "anonymous"),
                        "level_id": data.get("level_id", 1),
                        "character_id": data.get("character_id", 1),
                        "message": user_input,
                        "response": answer,
                        # "audio_base64": ... (omit for DB size)
                        "context": {
                             "characterId": data.get("character_id", 1),
                             "intent": full_final_res.get("intent"),
                             "site": site_hint
                        },
                        "created_at": datetime.utcnow().isoformat() + "Z",
                        "user_input": user_input, "generated_answer": answer, "site": site_hint
                    }
                    
                    history.append(new_entry)
                    if redis_key:
                        await app.state.redis.set(redis_key, json.dumps(history[-20:], ensure_ascii=False))
                    
                    # File Log
                    if ENABLE_FILE_LOGGING:
                        log_file = "chat_logs.json"
                        current_logs = []
                        if os.path.exists(log_file):
                            with open(log_file, "r", encoding="utf-8") as f:
                                 try: 
                                     current_logs = json.load(f)
                                     if not isinstance(current_logs, list): current_logs = []
                                 except: current_logs = []
                        current_logs.append(new_entry)
                        with open(log_file, "w", encoding="utf-8") as f:
                            json.dump(current_logs, f, ensure_ascii=False, indent=2)
             except Exception as e:
                logger.error(f"WS Save Error: {e}")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WS Error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except: pass