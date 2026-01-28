import json
import logging
import asyncio
from knowledge_base import KnowledgeBase
from heritage_tool import HeritageTools
from prompts import get_planner_prompt, SEN_CHARACTER_PROMPT
from data_manager import get_default_site_key

# Khởi tạo logger
logger = logging.getLogger("uvicorn")

async def agentic_workflow_stream(u_input: str, history: list, state, use_verifier: bool = False):
    """
    Unified Streaming Workflow for Agentic RAG.
    Mọi intent (Heritage, Chitchat, Realtime) đều tuân thủ output stream chuẩn.
    Yields:
    - {"status": "processing", "step": N, "message": "..."}
    - {"status": "streaming", "content": "..."} (Text tokens)
    - {"status": "finished", "result": FinalJSON}
    """
    try:
        # [STEP 1] Normalize Input
        yield {"status": "processing", "step": 1, "message": "Đang phân tích câu hỏi..."}
        norm_input = state.brain.normalize_query(u_input)
        
        # --- REDIS CACHE CHECK (Only for consistent queries, can optimize later) ---
        # Chiến lược: Kiểm tra cache trước. Nếu hit cache HERITAGE -> Stream giả lập từ cache.
        # Realtime không dùng cache này để đảm bảo tươi mới.
        cache_key = f"sen:cache:{norm_input}"
        cached_data = None
        try:
            if state.redis:
                cached_json = await state.redis.get(cache_key)
                if cached_json:
                    data = json.loads(cached_json)
                    # CHỈ DÙNG CACHE NẾU LÀ HERITAGE
                    if data.get("intent") == "heritage":
                        cached_data = data
        except Exception as e:
            logger.warning(f"Redis Check Error: {e}")

        if cached_data:
            yield {"status": "processing", "step": 1.1, "message": "Đã tìm thấy câu trả lời trong bộ nhớ (Cache)..."}
            logger.info(f"✅ Cache Hit: {cache_key}")
            
            # Stream giả lập từ text có sẵn
            full_text = cached_data.get("answer", "")
            chunk_size = 10
            for i in range(0, len(full_text), chunk_size):
                yield {"status": "streaming", "content": full_text[i:i+chunk_size]}
                await asyncio.sleep(0.01) # Giả lập độ trễ tí xíu cho mượt
                
            yield {"status": "finished", "result": cached_data}
            return

        # Build history string
        hist_str = ""
        for i, entry in enumerate(history[-6:]):
            if isinstance(entry, dict):
                q = entry.get('user_input', '')
                a = entry.get('generated_answer', '')[:100]
                if q: hist_str += f"User: {q}\n"
                if a: hist_str += f"AI: {a}\n"
            elif isinstance(entry, str):
                role = "User" if i % 2 == 0 else "AI"
                hist_str += f"{role}: {entry[:200]}\n"

        # [STEP 1] Contextualize Query (Rewrite if history exists)
        search_query = norm_input # Mặc định là input gốc
        if hist_str.strip(): 
            yield {"status": "processing", "step": 1, "message": "Hiểu ngữ cảnh hội thoại..."}
            try:
                from prompts import get_contextualize_prompt
                rw_res = await state.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": get_contextualize_prompt()},
                        {"role": "user", "content": f"History:\n{hist_str}\n\nInput: {norm_input}"}
                    ]
                )
                rewrite = rw_res.choices[0].message.content.strip()
                # Kiểm tra sanity check: Không được quá ngắn hoặc là chính input cũ
                if rewrite and len(rewrite) > 4 and rewrite != norm_input:
                    logger.info(f"🔄 [REWRITE] '{norm_input}' → '{rewrite}'")
                    search_query = rewrite
            except Exception as e:
                logger.error(f"❌ Rewrite error: {e}")

        # [STEP 1.5] Semantic Site Retrieval (Routing using Search Query)
        yield {"status": "processing", "step": 1.5, "message": "Đang định tuyến ngữ nghĩa..."}
        
        # Tìm site tiềm năng để planner quyết định tốt hơn
        try:
            candidate_sites = state.brain.find_potential_sites(search_query, top_k=3)
        except Exception:
            candidate_sites = []

        dynamic_prompt = get_planner_prompt(candidate_sites)
        planner_input = f"History:\n{hist_str}\n\nOriginal Input: {norm_input}\nRewritten Input: {search_query}\n"

        # Gọi LLM Planner
        plan_res = await state.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": dynamic_prompt},
                {"role": "user", "content": planner_input}
            ]
        )
        
        try:
            plan = json.loads(plan_res.choices[0].message.content)
            intent = plan.get("intent", "chitchat")
            site_key = plan.get("site")
        except:
            intent = "chitchat"
            site_key = None

        logger.info(f"📋 Intent: {intent} | Site: {site_key}")
        yield {"status": "processing", "step": 3, "message": f"Ý định: {intent} ({site_key})"}

        # [STEP 3] Execution based on Intent
        final_context = ""
        source_type = "none"
        full_answer = ""  # Initialize to avoid UnboundLocalError

        # --- CASE A: OUT OF SCOPE ---

        if intent == "out_of_scope":
            response_msg = "Dạ, Sen chỉ được đào tạo về Di sản, Văn hóa và Lịch sử Việt Nam thôi ạ. Bác vui lòng hỏi chủ đề liên quan để Sen phục vụ nhé! 🇻🇳"
            # Stream response này giả lập
            yield {"status": "streaming", "content": response_msg}
            final_res = await _build_response_data(state, response_msg, intent, site_key, "none")
            yield {"status": "finished", "result": final_res}
            return

        # --- CASE B: CHITCHAT ---
        if intent == "chitchat":
            res = await state.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": SEN_CHARACTER_PROMPT}, {"role": "user", "content": u_input}],
                stream=True
            )
            full_ans = ""
            async for chunk in res:
                txt = chunk.choices[0].delta.content
                if txt:
                    full_ans += txt
                    yield {"status": "streaming", "content": txt}
            
            # Thay vì return ngay, gán vào full_answer và để code chạy tiếp xuống phần TTS
            full_answer = full_ans
            final_context = "Chitchat conversation" # Dummy context for logging
            # yield {"status": "finished", "result": {"answer": full_ans, "intent": intent, "site": site_key}}
            # return

        # --- MAIN FLOW: HERITAGE & REALTIME ---
        # 1. Static Info
        from data_manager import get_site_config
        static_info = ""
        if site_key:
            site_config = get_site_config(site_key)
            if site_config:
                static_info = f"THÔNG TIN DI TÍCH ({site_config.get('name')}):\n Địa chỉ: {site_config.get('address')}\nGiờ mở cửa: {site_config.get('open_hour')}h-{site_config.get('close_hour')}h"
        
        # 2. Dynamic Info / RAG
        if intent == "realtime":
            if not site_key: 
                err = "Dạ bác muốn hỏi thông tin này ở địa điểm nào ạ? (Hoàng Thành, Văn Miếu...)"
                yield {"status": "streaming", "content": err}
                yield {"status": "finished", "result": {"answer": err, "intent": intent, "site": None}}
                return
            
            yield {"status": "processing", "step": 4, "message": f"Kết nối dữ liệu thực tế tại {site_key}..."}
            try:
                # Gọi song song các tool
                tasks = [
                    state.tools.get_weather(site_key),
                    state.tools.get_ticket_prices(site_key),
                    asyncio.to_thread(state.tools.get_opening_status, site_key)
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filter kết quả hợp lệ (không None, không Exception)
                valid_results = []
                for r in results:
                    if isinstance(r, Exception):
                        logger.error(f"Tool error: {r}")
                        continue
                    if r and isinstance(r, str) and len(r.strip()) > 0:
                        valid_results.append(r)
                
                if not valid_results:
                    # Nếu tất cả tools đều fail
                    realtime_data = "Hiện tại Sen chưa kết nối được với các nguồn dữ liệu thời gian thực. Xin lỗi bác!"
                else:
                    realtime_data = "\n\n".join(valid_results)
                
                final_context = f"{static_info}\n\n{'='*50}\nDỮ LIỆU THỜI GIAN THỰC:\n{'='*50}\n{realtime_data}"
                source_type = "tools"
            except Exception as e:
                logger.error(f"Realtime Tool Error: {e}", exc_info=True)
                final_context = static_info + "\n\n(Lỗi kết nối công cụ thời gian thực)"
                source_type = "tools_error"

        elif intent == "heritage": # RAG
            yield {"status": "processing", "step": 4, "message": "Tra cứu sử liệu..."}
            
            # Log chi tiết Heritage routing
            logger.info(f"🔍 [HERITAGE RAG] Raw: '{u_input}' -> Search: '{search_query}'")
            logger.info(f"   → Site Key: '{site_key}' (Collection & Filter wil be loaded from config)")
            
            # Lưu ý: KnowledgeBase đã có logic global fallback nên cứ gọi
            rag_content = await state.brain.fetch_and_rerank(
                query=search_query, 
                site_key=site_key,
                history=history # [STATELESS] Pass user history
            )

            # [STRICT MODE] Kiểm tra nếu không có dữ liệu RAG
            # fetch_and_rerank có thể trả về string rỗng hoặc None
            if not rag_content or not rag_content.strip():
                fallback_msg = "Dạ, hiện tại trong thư viện của Sen chưa có tài liệu nào về địa điểm này ạ (Hoặc dữ liệu chưa được nạp). Bác thông cảm hỏi địa điểm khác nhé!"
                yield {"status": "streaming", "content": fallback_msg}
                # Kết thúc flow ngay, không cho LLM chém gió
                yield {"status": "finished", "result": {"answer": fallback_msg, "intent": intent, "site": site_key}}
                return

            final_context = f"{static_info}\n\nTHÔNG TIN LỊCH SỬ/VĂN HÓA:\n{rag_content}"
            source_type = "rag"

        # --- CASE C: GENERATION (Only if answer not yet generated) ---
        if not full_answer:
            # [STEP 7] Generator (Stream) WITH MEMORY & REDIS CACHE
            yield {"status": "processing", "step": 5, "message": "Sen đang trả lời..."}
            
            # Tái tạo tin nhắn context (Memory Injection)
            system_prompt = SEN_CHARACTER_PROMPT
            msgs = [{"role": "system", "content": system_prompt}]
            
            # Short history (Client sends full list but we take last 4 items)
            for entry in history[-4:]:
                 if isinstance(entry, dict):
                     if 'user_input' in entry: msgs.append({"role": "user", "content": entry['user_input']})
                     if 'generated_answer' in entry: msgs.append({"role": "assistant", "content": entry['generated_answer']})
            
            # Prompt chính
            user_p = f"THÔNG TIN TRA CỨU (CONTEXT):\n{final_context}\n\nCÂU HỎI: {u_input}\n\nHãy trả lời dựa trên Context."
            msgs.append({"role": "user", "content": user_p})

            stream_resp = await state.openai.chat.completions.create(
                model="gpt-4o-mini", messages=msgs, stream=True
            )

            async for chunk in stream_resp:
                txt = chunk.choices[0].delta.content
                if txt:
                    full_answer += txt
                    yield {"status": "streaming", "content": txt}
        
        # [STEP 6: PREPARE DEBUG INFO]
        debug_col = "N/A"
        debug_filter = "N/A"
        
        if intent == "heritage" and site_key:
            from data_manager import get_site_config
            sc = get_site_config(site_key)
            if sc:
                 debug_col = sc.get("collection", "culture")
                 # Convert filter dict to string for display
                 flt = sc.get("filter", {})
                 debug_filter = json.dumps(flt, ensure_ascii=False) if flt else "Global Search"
        
        # [STEP 8] Optional Verifier
        # Chỉ chạy nếu bật mode Verifier và có context để đối chiếu (Heritage mode)
        if use_verifier and intent == "heritage" and 'final_context' in locals():
             yield {"status": "processing", "step": 5.5, "message": "🕵️ Đang kiểm chứng thông tin..."}
             try:
                 from verifier import Verifier
                 # Init Verifier (đảm bảo imports không lỗi)
                 verifier = Verifier(state.openai)
                 
                 # Thực hiện verify
                 verify_res = await verifier.verify(u_input, final_context, full_answer)
                 
                 note = ""
                 if verify_res.get("is_valid"):
                     note = f"\n\n----------\n✅ [Kiểm chứng]: {verify_res.get('reason')}"
                 else:
                     note = f"\n\n----------\n⚠️ [Cảnh báo]: {verify_res.get('reason')}"
                 
                 # Stream kết quả kiểm chứng ra giao diện
                 yield {"status": "streaming", "content": note}
                 full_answer += note
                 
             except Exception as e:
                 logger.error(f"Verifier Error: {e}")

        # [AUTO TTS]
        audio_b64 = ""
        try:
            if hasattr(state, 'generate_tts') and full_answer:
                 yield {"status": "processing", "step": 6, "message": "Đang tạo giọng đọc..."}
                 audio_b64 = await state.generate_tts(full_answer)
        except Exception as e:
            logger.error(f"❌ Auto TTS Failed: {e}")

        # [FINISH]
        final_res = await _build_response_data(state, full_answer, intent, site_key, source_type, debug_col, debug_filter)
        final_res["audio"] = audio_b64
        
        # --- REDIS SET (SAVE CACHE) ---
        # CHỈ LƯU NẾU LÀ HERITAGE
        if intent == "heritage" and state.redis:
            try:
                 # Lưu cache 1 tiếng (3600s)
                 await state.redis.setex(cache_key, 3600, json.dumps(final_res, ensure_ascii=False))
                 logger.info(f"💾 Caching HERITAGE response: {cache_key}")
            except Exception as e:
                 logger.warning(f"Redis Set Error: {e}")

        yield {"status": "finished", "result": final_res}

    except Exception as e:
        logger.error(f"❌ Workflow Error: {e}", exc_info=True)
        err_msg = "Ôi hỏng, Sen bị vấp cục đá (Lỗi hệ thống). Bác hỏi lại giùm Sen nhé!"
        yield {"status": "streaming", "content": err_msg}
        yield {"status": "finished", "result": {"answer": err_msg, "intent": "error", "site": None}}

async def _build_response_data(state, text, intent, site, source, collection="N/A", filter_info="N/A"):
    """Helper đóng gói kết quả cuối cùng (để cache hoặc debug)"""
    # Không cần sinh audio base64 ở đây nữa vì Frontend đã tự queue
    return {
        "answer": text,
        "intent": intent,
        "site": site,
        "data_source": source,
        "collection": collection,
        "filter": filter_info
    }

# Wrapper cho code cũ nếu cần (nhưng nên dùng stream)
async def agentic_workflow(u_input, history, state):
    res = None
    async for event in agentic_workflow_stream(u_input, history, state):
        if event["status"] == "finished":
            res = event["result"]
    return res
