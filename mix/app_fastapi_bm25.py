import os
import base64
import re
import io
import logging
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from gtts import gTTS
from langdetect import detect

# Các module tùy chỉnh của bạn
from embeddings import Embeddings
from vector_db import VectorDatabase
from reflection import Reflection

# Semantic Router
from semantic_router.route import Route
from semantic_router.router import SemanticRouter
import semantic_router.samples as samples

load_dotenv()

# ====== CẤU HÌNH ======
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Heritage NPC API")

# ====== MODELS ======
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

# ====== INITIALIZATION (Khởi tạo 1 lần) ======
DB_NAME = "vector_db"
COLLECTION_NAME = "culture_collection"

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
embedding = Embeddings(model_name="text-embedding-3-small")
vector_db = VectorDatabase(db_name=DB_NAME)
reflector = Reflection(llm_client=client)

# Setup Router
routes = [
    Route(name="roi_nuoc", samples=samples.roiNuocSample, filter_dict={"culture_type": "mua_roi_nuoc"}),
    Route(name="hoang_thanh", samples=samples.hoangThanhSample, filter_dict={"culture_type": "hoang_thanh"}),
    Route(name="chitchat", samples=samples.chitchatSample, filter_dict={}),
]
router = SemanticRouter(embedding=embedding, routes=routes, threshold=0.5)

# ====== PROMPT & LOGIC ======
SYSTEM_PROMPT = (
    "Bạn là một hướng dẫn viên ảo tên là 'Sen', chuyên gia về Di sản Văn hóa Việt Nam.\n"
    "--- NGÔN NGỮ (LANGUAGE RULES) ---\n"
    "- Nếu khách hỏi bằng tiếng Việt, hãy trả lời bằng tiếng Việt.\n"
    "- If the user asks in English, you MUST respond in English.\n"
    "- Tuyệt đối không trả lời song ngữ trong cùng một câu (trừ tên riêng di tích).\n"
    "--- PHONG CÁCH DIỄN ĐẠT ---\n"
    "- TÔNG GIỌNG: Thân thiện, niềm nở, tự hào và giàu cảm xúc.\n"
    "- CÁCH XƯNG HÔ: Sử dụng 'Tôi' hoặc 'Mình' và gọi người dùng là 'Bạn' hoặc 'Quý khách'.\n"
    "--- QUY TẮC NỘI DUNG ---\n"
    "1. Chỉ trả lời dựa trên thông tin trong CONTEXT. Không được bịa đặt.\n"
    "2. XỬ LÝ KHI THIẾU TIN: Nếu không có dữ liệu, hãy nói: 'Tiếc quá, hiện tại mình chưa có thông tin chi tiết về phần này. Bạn có muốn tìm hiểu về [gợi ý chủ đề] không?'.\n"
    "3. TỐI ƯU CHO GIỌNG ĐỌC (TTS): Trình bày mạch lạc, không dùng gạch đầu dòng, không ký tự đặc biệt."
)

def generate_audio(text: str) -> str:
    """Chuyển văn bản thành chuỗi Base64 âm thanh"""
    try:
        clean_text = re.sub(r'[^\w\s,.!??áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ]', '', text).strip()
        lang = 'vi'
        try:
            if detect(clean_text) == 'en': lang = 'en'
        except: pass
        
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return base64.b64encode(fp.read()).decode()
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return ""

def simple_keyword_score(text, query, rewritten):
    query_words = set(re.findall(r'\w{3,}', query.lower()))
    text_lower = text.lower()
    score = sum(1.5 if w in text_lower else 0 for w in query_words)
    proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', rewritten)
    for pn in proper_nouns:
        if pn.lower() in text_lower: score += 2.0
    return score

# ====== ENDPOINT ======
@app.post("/process_query", response_model=ChatResponse)
async def process_query(request: ChatRequest):

    user_input = request.user_input.strip()
    history = request.history

    # --- VÒNG 1: ROUTER CÂU GỐC ---
    score, route_name, filter_dict = router.guide(user_input)
    rewritten = user_input # Mặc định ban đầu

    # TRƯỜNG HỢP 1: Chắc chắn là Chitchat hoặc câu chào ngay từ đầu
    if score > 0.6 and route_name in ("uncertain", "chitchat"):
        ans = "Chào bạn! Mình là Sen đây. Bạn cần mình hỗ trợ gì về di sản không?"
        # QUAN TRỌNG: Phải return ngay để không chạy xuống phần RAG phía dưới
        return ChatResponse(
            answer=ans, 
            rewritten_query=user_input, 
            route=route_name, 
            score=score, 
            audio_base64=generate_audio(ans)
        )

    # TRƯỜNG HỢP 2: Nếu câu gốc rõ ràng (> 0.6) và đúng chủ đề di sản -> Giữ nguyên để xuống RAG
    if score > 0.6 and route_name not in ("uncertain", "chitchat"):
        logger.info(f"Layer 1: Khớp chủ đề {route_name}")
    
    # TRƯỜNG HỢP 3: Điểm thấp (score <= 0.6) -> Cần xem xét Rewrite hoặc Chitchat
    else:
        # --- LỚP 2: REWRITE + ROUTER LẠI (Layer 2) ---
        ambiguous_keywords = ["nó", "đó", "đấy", "kia", "ấy", "họ", "ông ấy", "bà ấy", "ở đó", "chỗ đó"]
        is_ambiguous = any(word in user_input.lower() for word in ambiguous_keywords)
        
        # Chỉ tốn 2s Rewrite nếu có từ mơ hồ (nó, đấy...) và có lịch sử chat
        if (is_ambiguous or len(user_input.split()) < 3) and len(history) > 1:
            logger.info("Layer 2: Đang Rewrite để hiểu ngữ cảnh...")
            rewritten = reflector.rewrite(history, user_input)
            
            # Router lại lần 2 sau khi đã rõ nghĩa
            score, route_name, filter_dict = router.guide(rewritten)
            
            # Nếu sau khi Rewrite vẫn không phải di sản hoặc điểm vẫn thấp (bbb, ccc...)
            if route_name in ("uncertain", "chitchat") or score < 0.4:
                ans = "Chào bạn! Câu này Sen chưa rõ lắm, nhưng bạn có muốn nghe về Hoàng Thành hay Múa rối nước không?"
                return ChatResponse(
                    answer=ans, rewritten_query=rewritten, 
                    route=route_name, score=score, 
                    audio_base64=generate_audio(ans)
                )
        else:
            # Không có từ mơ hồ mà điểm vẫn thấp -> Đích thị là nói linh tinh (bbb, ccc, alooo)
            # Trả về câu chào luôn, không cho xuống RAG
            ans = "Sen nghe đây! Bạn muốn hỏi gì về di sản văn hóa Việt Nam nào?"
            return ChatResponse(
                answer=ans, rewritten_query=user_input, 
                route=route_name, score=score, 
                audio_base64=generate_audio(ans)
            )

    # --- CHỐT CHẶN: NẾU ĐI XUỐNG ĐƯỢC ĐẾN ĐÂY NGHĨA LÀ ĐÃ CÓ ROUTE DI SẢN CHUẨN ---
    # 3. RETRIEVAL & HYBRID RERANK... (Phần code cũ của bạn giữ nguyên bên dưới)

    # user_input = request.user_input.strip()
    # history = request.history

    # # --- LỚP 1: ROUTER CÂU GỐC (Layer 1) ---
    # score, route_name, filter_dict = router.guide(user_input)
    # rewritten = user_input # Mặc định ban đầu

    # # Nếu câu gốc rõ ràng (> 0.6) và đúng chủ đề di sản, đi thẳng tới RAG
    # if score > 0.6 and route_name not in ("uncertain", "chitchat"):
    #     logger.info(f"Layer 1: Khớp chủ đề {route_name}")
    # else:
    #     # --- LỚP 2: REWRITE + ROUTER LẠI (Layer 2) ---
    #     # Kiểm tra xem có cần dùng lịch sử để giải nghĩa (nó, đấy, kia...) không
    #     ambiguous_keywords = ["nó", "đó", "đấy", "kia", "ấy", "họ", "ông ấy", "bà ấy", "ở đó", "chỗ đó"]
    #     is_ambiguous = any(word in user_input.lower() for word in ambiguous_keywords)
        
    #     # Chỉ tốn thời gian Rewrite nếu câu ngắn hoặc có từ mơ hồ
    #     if (is_ambiguous or len(user_input.split()) < 5) and len(history) > 1:
    #         logger.info("Layer 2: Đang Rewrite để hiểu ngữ cảnh...")
    #         rewritten = reflector.rewrite(history, user_input)
    #         # Router lại lần 2 sau khi đã có context rõ ràng
    #         score, route_name, filter_dict = router.guide(rewritten)
        
    #     # Sau khi Rewrite vẫn là chitchat hoặc điểm quá thấp (bbb, ccc...)
    #     if route_name in ("uncertain", "chitchat") or score < 0.4:
    #         ans = "Chào bạn! Tôi là Sen. Bạn muốn tìm hiểu về Múa rối nước hay Hoàng thành Thăng Long nhỉ?"
    #         return ChatResponse(
    #             answer=ans, 
    #             rewritten_query=rewritten, 
    #             route=route_name, 
    #             score=score, 
    #             audio_base64=generate_audio(ans)
    #         )

    # 3. RETRIEVAL & HYBRID RERANK (Chỉ chạy khi Layer 1 hoặc Layer 2 đã xác định đúng route)
    q_vec = embedding.encode([rewritten])[0]
    results = vector_db.query(COLLECTION_NAME, q_vec, limit=15, filter_dict=filter_dict)
    
    if not results:
        ans = "Tiếc quá, hiện tại mình chưa có thông tin chi tiết về phần này. Bạn có muốn tìm hiểu về [gợi ý chủ đề] không?"
        return ChatResponse(answer=ans, rewritten_query=rewritten, route=route_name, score=score, audio_base64=generate_audio(ans))

    # Lọc thô (Heuristic) - Giữ nguyên của bạn
    for r in results:
        r['hybrid_score'] = r.get('score', 0) + (simple_keyword_score(r['content'], user_input, rewritten) * 0.1)
    results.sort(key=lambda x: x['hybrid_score'], reverse=True)
    
    top_candidates = results[:5]
    passages = [r["content"] for r in top_candidates]

    # Lọc tinh (LLM Rerank) - Giữ nguyên của bạn
    rerank_input = "\n\n".join([f"--- ID [{i}] ---\n{p}" for i, p in enumerate(passages)])
    rerank_prompt = f"Chọn ID đoạn văn chứa thông tin trả lời câu hỏi: {rewritten}\n\n{rerank_input}\n\nChỉ trả về ID dạng [0, 2] hoặc [None]."

    context = passages[0]
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Chỉ trả về ID."}, {"role": "user", "content": rerank_prompt}],
            temperature=0
        )
        selected_indices = [int(i) for i in re.findall(r'\d+', res.choices[0].message.content)]
        if selected_indices:
            context = "\n\n".join([passages[i] for i in selected_indices if i < len(passages)])
    except: pass

    # 4. GENERATE ANSWER - Giữ nguyên của bạn
    final_res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"CONTEXT:\n{context}\n\nQ: {rewritten}"}
        ]
    )
    answer = final_res.choices[0].message.content
    
    # 5. AUDIO
    audio_b64 = generate_audio(answer)

    return ChatResponse(
        answer=answer,
        rewritten_query=rewritten,
        route=route_name,
        score=score,
        audio_base64=audio_b64,
        context_used=context[:200] + "..."
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)