import json
import logging
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from app.services.knowledge import KnowledgeBase
from app.services.tools import HeritageTools
from app.core.config_prompts import get_planner_prompt, SEN_CHARACTER_PROMPT
from app.core.config_loader import get_default_site_key
# Vietnam timezone
VN_TZ = ZoneInfo('Asia/Ho_Chi_Minh')

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
        
        # Build history string

        hist_str = ""
        for i, entry in enumerate(history[-6:]):
            if isinstance(entry, dict):
                # Support standard OpenAI format {role, content} from Node.js
                if 'role' in entry and 'content' in entry:
                    role = entry.get('role', '').capitalize()
                    content = entry.get('content', '')
                    # Truncate AI response — rewrite chỉ cần biết ngữ cảnh, không cần full text
                    if role.lower() == 'assistant':
                        content = content[:200] + ('...' if len(content) > 200 else '')
                    hist_str += f"{role}: {content}\n"
                else:
                    # Support internal format {user_input, generated_answer}
                    q = entry.get('user_input', '')
                    a = entry.get('generated_answer', '')[:200]
                    if q: hist_str += f"User: {q}\n"
                    if a: hist_str += f"AI: {a}...\n"
            elif isinstance(entry, str):
                role = "User" if i % 2 == 0 else "AI"
                hist_str += f"{role}: {entry[:200]}\n"

        # [STEP 1] Contextualize Query (Rewrite if history exists)
        search_query = norm_input # Mặc định là input gốc
        if hist_str.strip(): 
            yield {"status": "processing", "step": 1, "message": "Hiểu ngữ cảnh hội thoại..."}
            try:
                from app.core.config_prompts import get_contextualize_prompt
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
        
        # --- REDIS CACHE CHECK (after query rewrite) ---
        # ⭐ KIỂM TRA GAME CONTEXT (Level/Character/Knowledge Base)
        # Nếu có game context → KHÔNG DÙNG CACHE để đảm bảo đúng KB + persona
        has_game_context = False
        level_context_name = ""
        for entry in history:
            if isinstance(entry, dict) and entry.get('role') == 'system':
                content = entry.get('content', '')
                # Check nếu có Level, Chapter, hoặc Knowledge Base trong system message
                if any(keyword in content for keyword in ['Level:', 'Chapter:', 'KIẾN THỨC RIÊNG', '📍 CONTEXT:', '📚']):
                    has_game_context = True
                    logger.info("🎮 Game context detected → Cache DISABLED")
                    
                    # Extract specifically the Level Name if available for Planner Constraint
                    import re
                    # Match pattern: - Level: "tên level"
                    match = re.search(r'- Level:\s*"(.*?)"', content)
                    if match:
                        level_context_name = match.group(1)
                        logger.info(f"   → Explicit Level Context: '{level_context_name}'")
                    break
        
        # ⭐ SEMANTIC CACHE CHECK — sau rewrite để dùng search_query đã chuẩn hóa
        # VD: 'cột cờ ở đó' → rewrite → 'Cột cờ Hoàng Thành Thăng Long' → similarity=0.97 → HIT!
        if not has_game_context and hasattr(state, 'sem_cache'):
            cached = state.sem_cache.get(search_query, intent_filter="heritage")
            if cached:
                yield {"status": "processing", "step": 1.1, "message": "Đã tìm thấy trong bộ nhớ..."}
                logger.info(f"✅ [SemanticCache HIT] query='{search_query[:50]}'")
                full_text = cached.get("answer", "")
                for i in range(0, len(full_text), 10):
                    yield {"status": "streaming", "content": full_text[i:i+10]}
                    await asyncio.sleep(0.005)
                yield {"status": "finished", "result": cached}
                return

        # [STEP 1.5] Semantic Site Retrieval (Routing using Search Query)
        yield {"status": "processing", "step": 1.5, "message": "Đang định tuyến ngữ nghĩa..."}
        
        # Tìm site tiềm năng để planner quyết định tốt hơn
        try:
            candidate_sites = state.brain.find_potential_sites(search_query, top_k=3)
        except Exception:
            candidate_sites = []

        dynamic_prompt = get_planner_prompt(candidate_sites, level_context=level_context_name)
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
            # [IMPROVED] Dùng LLM để từ chối khéo léo theo Persona thay vì hardcode
            yield {"status": "processing", "step": 3.1, "message": "Sen đang suy nghĩ câu trả lời..."}
            
            # Lấy danh sách các site ĐANG CÓ trong hệ thống để bot tự tin giới thiệu
            from app.core.config_loader import get_heritage_config
            known_sites = get_heritage_config()
            known_sites_names = [s['name'] for s in known_sites.values()]
            known_list_str = ", ".join(known_sites_names)

            refusal_prompt = f"""{SEN_CHARACTER_PROMPT}
            
            NGƯỜI DÙNG VỪA HỎI VỀ: "{u_input}"
            
            SỰ THẬT LÀ:
            1. Bạn KHÔNG có dữ liệu về địa điểm/chủ đề này trong sổ tay.
            2. Bạn HIỆN TẠI CHỈ CÓ DỮ LIỆU VỀ: {known_list_str}.
            
            NHIỆM VỤ CỦA BẠN:
            - Nhắc lại tên địa điểm người dùng vừa hỏi (để xác nhận là bạn hiểu đúng ý).
            - Xin lỗi khéo léo rằng hiện tại trong sổ tay của Sen chưa kịp cập nhật thông tin về nơi đó.
            - TUYỆT ĐỐI KHÔNG được bịa ra các chủ đề liên quan (như món ăn, lễ hội vùng đó) để gợi ý.
            - CHỈ ĐƯỢC MỜI người dùng tham quan các địa điểm bạn ĐANG BIẾT ({known_list_str}).
            - Giữ thái độ cầu thị, hứa sẽ học thêm trong tương lai.
            """
            
            try:
                res = await state.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": refusal_prompt}],
                    temperature=0.7
                )
                response_msg = res.choices[0].message.content
            except Exception as e:
                logger.error(f"Out of scope generation error: {e}")
                response_msg = "Dạ, Sen chỉ được đào tạo về Di sản, Văn hóa và Lịch sử Việt Nam thôi ạ. Bác vui lòng hỏi chủ đề liên quan để Sen phục vụ nhé! 🇻🇳"

            yield {"status": "streaming", "content": response_msg}
            final_res = await _build_response_data(state, response_msg, intent, site_key, "none")
            yield {"status": "finished", "result": final_res}
            return

        # --- CASE B: CHITCHAT ---
        if intent == "chitchat":
            # Inject Current Time
            current_time = datetime.now(VN_TZ).strftime("%H:%M ngày %d/%m/%Y")
            
            # [FIX] Level Context Constraint for Chitchat Refusal
            level_refusal_prompt = ""
            if level_context_name:
                level_refusal_prompt = f"""
[GAMEPLAY MODE]: Người dùng đang chơi màn: "{level_context_name}".
[CHỈ DẪN QUAN TRỌNG]: 
- Nếu câu hỏi của người dùng là về một DI TÍCH/SỰ KIỆN KHÁC (không phải {level_context_name}), bạn hãy KHÉO LÉO TỪ CHỐI cung cấp thông tin chi tiết. 
- Hãy gợi ý quay lại chủ đề của màn chơi hiện tại.
- Mẫu câu: "Dạ, cậu ơi, mình đang ở {level_context_name} mà? Cứ tập trung vào đây đã nhé, chuyện đó để lúc khác Sen kể cho!"
- Nếu là chào hỏi xã giao (hi, hello) -> Trả lời bình thường.
"""

            # [FIX] Inject Candidate Sites into Chitchat Context for smarter clarification
            # Nếu Planner đẩy về Chitchat vì câu hỏi ngắn (vd: "lá cờ"), nhưng thực tế KnowledgeBase lại tìm thấy "Hoàng Thành"
            # thì Bot nên dùng thông tin đó để gợi ý ngược lại User.
            candidate_names = []
            if candidate_sites:
                candidate_names = [site['name'] for site in candidate_sites]
            
            site_hint_msg = ""
            if candidate_names:
                site_hint_msg = f"\n[GỢI Ý TỪ HỆ THỐNG]: Từ khóa trong câu hỏi có thể liên quan đến: {', '.join(candidate_names)}. Hãy dùng thông tin này để hỏi lại người dùng (Ví dụ: 'Ý cậu là Cột Cờ ở Hoàng Thành phải không?')."

            # [FIX] Inject Explicit Known Sites for Recommendation to prevent Hallucination
            from app.core.config_loader import get_heritage_config
            all_known = get_heritage_config()
            # Format list: "Tên (Mô tả ngắn)"
            valid_recommendations = []
            for k, v in all_known.items():
                valid_recommendations.append(f"- {v['name']}")
            
            valid_recs_str = "\n".join(valid_recommendations)

            system_msg = f"""{SEN_CHARACTER_PROMPT}

[THÔNG TIN THỜI GIAN THỰC]: Hiện tại là {current_time}.
{level_refusal_prompt}
{site_hint_msg}

[DANH SÁCH ĐỊA ĐIỂM BẠN CÓ DỮ LIỆU]:
{valid_recs_str}

[QUY TẮC SỐNG CÒN - CHẶN CHỦ ĐỀ LẠ]:
1. KIỂM TRA CHỦ ĐỀ CÂU NÓI:
   - Nếu người dùng KHEN/CHÊ/HỎI về món ăn, địa điểm, sự vật KHÔNG NẰM TRONG DANH SÁCH: {valid_recs_str.replace(chr(10), ", ")}.
   - HÀNH ĐỘNG: TUYỆT ĐỐI KHÔNG ĐƯỢC HƯỞNG ỨNG hay bình luận sâu (Dù là đồng tình "ngon lắm", "đẹp lắm").
   - PHẢI lái ngay về chủ đề Sen biết.
   - Ví dụ SAI: "Bánh Pía ngon lắm! Vỏ giòn tan..." (SAI vì Bánh Pía không có trong DB).
   - Ví dụ ĐÚNG: "Dạ nghe tả bánh Pía hấp dẫn quá, nhưng tiếc là Sen chưa được học kỹ về ẩm thực vùng này. Hay là mình quay về bàn chuyện Múa Rối Nước đi ạ? Cũng thú vị lắm đó!"

2. TUYỆT ĐỐI KHÔNG DÙNG KIẾN THỨC GPT-4 (PRE-TRAINED KNOWLEDGE) để mô tả những thứ ngoài Database.
   - Nếu bạn không có dữ liệu về "Bánh Pía" trong monuments.json -> Coi như bạn KHÔNG BIẾT nó là gì.

3. KHI NGƯỜI DÙNG NHỜ GỢI Ý/RECOMMEND:
   - CHỈ ĐƯỢC GỢI Ý các địa điểm trong danh sách ở trên.
   
4. KHÔNG "DẠY ĐỜI" TRONG CHITCHAT:
   - Tuyệt đối KHÔNG đưa ra các thông tin lịch sử cụ thể.
   - Thay vào đó: Hãy giới thiệu cảm xúc, không gian, vẻ đẹp.

[QUY TẮC FORMAT]: Nếu có Link/URL, BẮT BUỘC định dạng Markdown: [Tên Link](URL). Không để URL trần."""
            
            # [FIX] Cần truyền toàn bộ HISTORY để LLM nhìn thấy System Prompt (có chứa Knowledge Base từ AI Service)
            # Lọc history để chỉ lấy đúng format OpenAI support (role, content)
            chat_messages = [{"role": "system", "content": system_msg}]
            
            for entry in history:
                if isinstance(entry, dict) and 'role' in entry and 'content' in entry:
                    chat_messages.append({"role": entry['role'], "content": entry['content']})
            
            # Append cú chót là user input hiện tại (nếu chưa có trong history)
            if not chat_messages or chat_messages[-1]['role'] != 'user' or chat_messages[-1]['content'] != u_input:
                 chat_messages.append({"role": "user", "content": u_input})

            res = await state.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=chat_messages,
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
        from app.core.config_loader import get_site_config
        static_info = ""
        if site_key:
            site_config = get_site_config(site_key)
            if site_config:
                static_info = f"THÔNG TIN DI TÍCH ({site_config.get('name')}):\n Địa chỉ: {site_config.get('address')}\nGiờ mở cửa: {site_config.get('open_hour')}h-{site_config.get('close_hour')}h"
        
        # 2. Dynamic Info / RAG
        # 2. Dynamic Info / RAG
        if intent == "realtime":
            if not site_key: 
                err = "Dạ bác muốn hỏi thông tin này ở địa điểm nào ạ? (Hoàng Thành, Văn Miếu...)"
                yield {"status": "streaming", "content": err}
                yield {"status": "finished", "result": {"answer": err, "intent": intent, "site": None}}
                return
            
            yield {"status": "processing", "step": 4, "message": f"Kết nối dữ liệu thực tế tại {site_key}..."}
            
            # Kiểm tra xem có cần RAG không — query thuần realtime (giá vé, thời tiết, giờ) thì skip RAG
            PURE_REALTIME_KEYWORDS = ["giá vé", "vé vào", "mấy giờ", "mở cửa", "đóng cửa", "thời tiết", "mưa", "nắng", "nhiệt độ"]
            check_text = norm_input + " " + search_query.lower()  # Kiểm tra cả câu gốc lẫn rewrite
            is_pure_realtime = any(kw in check_text for kw in PURE_REALTIME_KEYWORDS)
            
            if is_pure_realtime:
                logger.info(f"⚡ [REALTIME ONLY] Skip RAG — query thuần realtime: '{norm_input[:40]}'")
                rag_context_str = ""
            else:
                # Câu hỏi realtime có kết hợp lịch sử/văn hóa → cần RAG context
                logger.info(f"🔍 [REALTIME + RAG] Fetching base knowledge for {site_key}...")
                rag_content = await state.brain.fetch_and_rerank(
                    query=search_query,
                    site_key=site_key,
                    history=history
                )
                rag_context_str = f"\n\nTHÔNG TIN LỊCH SỬ/VĂN HÓA:\n{rag_content}" if rag_content else ""

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
                    realtime_data = "Hiện tại Sen chưa kết nối được với các nguồn dữ liệu thời gian thực."
                else:
                    realtime_data = "\n\n".join(valid_results)
                
                final_context = f"{static_info}{rag_context_str}\n\n{'='*50}\nDỮ LIỆU THỜI GIAN THỰC:\n{'='*50}\n{realtime_data}"
                source_type = "tools+rag"
            except Exception as e:
                logger.error(f"Realtime Tool Error: {e}", exc_info=True)
                final_context = f"{static_info}{rag_context_str}\n\n(Lỗi kết nối công cụ thời gian thực)"
                source_type = "rag_only_fallback"

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
                # ✨ STRICT MODE UPDATE: User yêu cầu CHỈ lấy từ DB.
                # Nếu không có, log lỗi và báo không tìm thấy.
                logger.error("❌ MONGODB RETRIEVAL FAILED: Không tìm thấy document nào khớp câu hỏi.")
                
                fallback_msg = "Xin lỗi, Sen không tìm thấy thông tin này trong Cơ sở dữ liệu của mình (MongoDB trả về rỗng). Vui lòng kiểm tra lại kết nối hoặc dữ liệu."
                yield {"status": "streaming", "content": fallback_msg}
                yield {"status": "finished", "result": {"answer": fallback_msg, "intent": intent, "site": site_key}}
                return

            final_context = f"{static_info}\n\nTHÔNG TIN LỊCH SỬ/VĂN HÓA:\n{rag_content}"
            source_type = "rag"

        # --- CASE C: GENERATION (Only if answer not yet generated) ---
        if not full_answer:
            # [STEP 7] Generator (Stream) WITH MEMORY & REDIS CACHE
            yield {"status": "processing", "step": 5, "message": "Sen đang trả lời..."}
            
            # Tái tạo tin nhắn context (Memory Injection)
            current_time = datetime.now(VN_TZ).strftime("%H:%M ngày %d/%m/%Y")
            
            # [IMPROVED] FALLBACK MECHANISM FOR GENERAL KNOWLEDGE
            # Nếu RAG Context (final_context) quá ngắn hoặc rỗng, nhưng câu hỏi lại về kiến thức phổ thông (VD: "ý nghĩa sao vàng 5 cánh"),
            # cho phép LLM "chém" dựa trên kiến thức chung nhưng phải đánh dấu là kiến thức bổ trợ.
            
            allow_general_knowledge_instruction = ""
            if intent == "heritage" and (not final_context or len(final_context) < 50): # Check final_context, not rag_content directly
                 allow_general_knowledge_instruction = """
[CHẾ ĐỘ KIẾN THỨC BỔ TRỢ]:
Hiện tại tài liệu (Context) không có đủ thông tin cho câu hỏi này.
TUY NHIÊN, đây là một câu hỏi về kiến thức phổ thông/biểu tượng văn hóa (Ví dụ: Ý nghĩa sao vàng, Chú Tễu là ai...).
HÃY TRẢ LỜI dựa trên kiến thức chung của bạn, NHƯNG phải bắt đầu bằng cụm từ:
"Theo hiểu biết chung của Sen thì..." hoặc "Tuy trong sổ tay di tích không ghi rõ, nhưng theo Sen biết..."
TUYỆT ĐỐI KHÔNG BỊA ĐẶT các thông tin cụ thể như ngày tháng, số liệu nếu không chắc chắn.
"""

            system_prompt = f"""{SEN_CHARACTER_PROMPT}

[THÔNG TIN THỜI GIAN THỰC]: Hiện tại là {current_time}.
[QUY TẮC FORMAT]: Nếu có Link/URL, BẮT BUỘC định dạng Markdown: [Tên Link](URL). Không để URL trần.
{allow_general_knowledge_instruction}
[QUY TẮC GỢI Ý]: Khi người dùng nhờ giới thiệu/gợi ý địa điểm đi chơi, HÃY CHỈ tập trung vào các DI SẢN VĂN HÓA, LỊCH SỬ, hoặc DANH LAM THẮNG CẢNH VIỆT NAM (Ví dụ: Hoàng Thành, Văn Miếu, Chùa Một Cột, Nhà Tù Hỏa Lò...). Tránh gợi ý các khu vui chơi giải trí thuần túy trừ khi được hỏi."""
            msgs = [{"role": "system", "content": system_prompt}]
            
            # Short history (Client sends full list but we take last 4 items)
            for entry in history[-4:]:
                 if isinstance(entry, dict):
                     # Standard OpenAI format
                     if 'role' in entry and 'content' in entry:
                         msgs.append({"role": entry['role'], "content": entry['content']})
                     # Internal format
                     else:
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
            from app.core.config_loader import get_site_config
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
                 from app.services.verifier import Verifier
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

        # [EMOTION ANALYSIS] 🎭 Phân tích biểu cảm
        emotion_data = {}
        try:
            from app.services.emotion import EmotionAnalyzer
            emotion_data = EmotionAnalyzer.analyze(u_input, full_answer, intent)
            logger.info(f"🎭 Emotion selected: {emotion_data}")
        except Exception as e:
            logger.error(f"❌ Emotion Analysis failed: {e}")
            emotion_data = {"gesture": "normal", "mouthState": "smile", "eyeState": "normal"}

        # [FINISH]
        final_res = await _build_response_data(state, full_answer, intent, site_key, source_type, debug_col, debug_filter)
        final_res["audio_base64"] = audio_b64
        final_res["emotion"] = emotion_data  # ✨ Thêm emotion metadata
        
        # ⭐ Lưu Semantic Cache SAU KHI hoàn thành — key = search_query (đã rewrite)
        if intent == "heritage" and not has_game_context and hasattr(state, 'sem_cache'):
            try:
                state.sem_cache.set(search_query, final_res, intent="heritage", ttl=3600)
            except Exception as e:
                logger.warning(f"⚠️ [SemanticCache] Save error: {e}")


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