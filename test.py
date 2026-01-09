import os, logging, redis, asyncio
from fastapi import FastAPI, BackgroundTasks
from sentence_transformers import SentenceTransformer # Local Embedding
from contextlib import asynccontextmanager

# --- KHỞI TẠO BỘ NHỚ ĐỆM (REDIS) ---
# Dùng Upstash hoặc Redis Local
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

# --- LOCAL EMBEDDING (Tăng tốc x10 lần) ---
# Chạy trực tiếp trên Server, không tốn tiền API
local_embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

@app.post("/process_query", response_model=ChatResponse)
async def process_query(request: ChatRequest, background_tasks: BackgroundTasks):
    user_input = request.user_input.strip()
    # Chỉ lấy 5 câu lịch sử gần nhất để tiết kiệm Token và tránh "loạn" AI
    history = request.history[-5:] if request.history else []

    # 1. KIỂM TRA REDIS CACHE (Tốc độ 0.001s)
    cached_res = redis_client.get(f"cache:{user_input.lower()}")
    if cached_res:
        logger.info("Dùng kết quả từ Cache")
        return ChatResponse(**json.loads(cached_res))

    # 2. ROUTER VÒNG 1 (Dùng Local Embedding để tính điểm nhanh)
    # Giả sử hàm router.guide đã được chuyển sang dùng local_embedder
    score, route_name, filter_dict = router.guide(user_input)

    # FAST TRACK: Nếu là Chitchat rõ ràng -> Trả lời ngay, thoát hàm
    if route_name == "chitchat" and score > 0.7:
        ans = "Chào bạn! Minh nghe đây. Bạn cần mình hỗ trợ gì về di sản không?"
        return ChatResponse(answer=ans, rewritten_query=user_input, route=route_name, score=score)

    # 3. UNIVERSAL REFLECTION (Độ chính xác cao cho câu hỏi đuổi)
    rewritten = user_input
    if score < 0.6 and len(history) > 0:
        # Gọi AI Rewrite (Async)
        rewritten = await reflector.rewrite_async(history, user_input)
        score_2, route_2, filter_2 = router.guide(rewritten)
        
        if score_2 > 0.5:
            score, route_name, filter_dict = score_2, route_2, filter_2

    # 4. RAG PIPELINE (Chỉ chạy khi đã rõ chủ đề)
    # Lấy Vector từ máy chủ (Local)
    q_vec = local_embedder.encode(rewritten).tolist()
    
    # Tìm kiếm DB (Vector + Hybrid)
    results = vector_db.query(COLLECTION_NAME, q_vec, filter_dict=filter_dict)
    
    if not results:
        return ChatResponse(answer="Tiếc quá, mình chưa có thông tin này...", route=route_name)

    # 5. GENERATE & CACHING
    # Gọi GPT để soạn câu trả lời cuối cùng
    final_res = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": f"CONTEXT: {results[0]['content']}\nQ: {rewritten}"}]
    )
    answer = final_res.choices[0].message.content

    # LƯU VÀO REDIS để lần sau không cần gọi GPT nữa (Lưu trong 1 tiếng)
    response_data = ChatResponse(answer=answer, rewritten_query=rewritten, route=route_name, score=score)
    redis_client.setex(f"cache:{user_input.lower()}", 3600, response_data.json())

    # 6. TTS CHẠY NGẦM (Không bắt khách hàng đợi âm thanh)
    # Bạn có thể trả về text trước, Audio sẽ được Frontend gọi sau hoặc dùng link
    return response_data