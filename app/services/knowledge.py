import unicodedata
import logging
import re
from sentence_transformers import CrossEncoder
from typing import List, Optional, Tuple
from sentence_transformers import SentenceTransformer
from app.core.config_loader import get_heritage_config

logger = logging.getLogger("uvicorn")

class KnowledgeBase:
    def __init__(self, v_db, embedder: SentenceTransformer):
        """
        Khởi tạo KnowledgeBase với vector database và sentence transformer (embedder).
        """
        self.v_db = v_db
        self.embedder = embedder
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.history = []

        # ⭐ Graph Store (Hybrid RAG)
        from app.core.graph_store import GraphStore
        self.graph = GraphStore(v_db.db) if v_db.db is not None else None
        logger.info("✅ [KnowledgeBase] GraphStore initialized.")

        # [NEW] Semantic Routing Index (In-Memory)
        self.route_data = []
        self.route_embeddings = None
        self._build_routing_index()

        self.reload_config()
        
    def reload_config(self):
        """
        Reload lại cấu hình từ khóa từ data_manager.
        """
        from app.core.config_loader import get_heritage_config
        config = get_heritage_config()
        self.site_keywords = {}
        for key, data in config.items():
            # Gom keyword: name + context keys (nếu có)
            # Tạm thời chỉ lấy name làm keyword chính
            keywords = [data["name"].lower()]
            # Nếu muốn tách name thành các từ khóa phụ, xử lý thêm ở đây
            # Ví dụ: "Văn Miếu Quốc Tử Giám" -> ["văn miếu", "quốc tử giám"]
            # Logic đơn giản: thêm key vào
            keywords.append(key.replace("_", " "))
            
            self.site_keywords[key] = keywords
            
        logger.info(f"🔄 KnowledgeBase reloaded. Sites: {list(self.site_keywords.keys())}")

    def _build_routing_index(self):
        """
        Khởi tạo index cho việc định tuyến semantic.
        Đọc config, embed descriptions và lưu vào RAM.
        """
        try:
            from app.core.config_loader import get_heritage_config
            config = get_heritage_config()
            
            texts = []
            self.route_data = []
            
            for key, data in config.items():
                # Kết hợp Tên + Mô tả để embed
                desc = f"{data['name']} {data.get('context_description', '')}"
                texts.append(desc)
                self.route_data.append(data)
            
            if texts:
                # Embed batch
                logger.info(f"🔄 Building Routing Index for {len(texts)} sites...")
                self.route_embeddings = self.embedder.encode(texts, convert_to_tensor=True)
                logger.info("✅ Routing Index Ready!")
            else:
                self.route_embeddings = None
                
        except Exception as e:
            logger.error(f"❌ Failed to build routing index: {e}")

    def find_potential_sites(self, query: str, top_k: int = 3) -> List[dict]:
        """
        Tìm top_k di tích khớp ngữ nghĩa nhất với câu hỏi.
        Dùng cosine similarity.
        """
        if self.route_embeddings is None or not self.route_data:
            return []
            
        from sentence_transformers import util
        t0 = logging.time.time()
        
        # Embed query
        q_vec = self.embedder.encode(query, convert_to_tensor=True)
        
        # Cosine Similarity
        # (1, D) x (N, D).T -> (1, N)
        scores = util.cos_sim(q_vec, self.route_embeddings)[0]
        
        # Get Top K
        # torch.topk trả về (values, indices)
        top_results = scores.topk(k=min(top_k, len(self.route_data)))
        
        results = []
        for score, idx in zip(top_results.values, top_results.indices):
            if score.item() > 0.3: # Threshold
                site_info = self.route_data[idx.item()]
                results.append(site_info)
                logger.info(f"   🔍 Route Match: {site_info['name']} (Score: {score.item():.2f})")
                
        # logger.info(f"⏱️ Routing took: {logging.time.time() - t0:.3f}s")
        return results
    def normalize_query(self, query: str) -> str:
        """
        [STEP 1] Normalize Input: Chuẩn hóa text đầu vào.
        """
        import re
        if not query: return ""
        # Lowercase, bỏ khoảng trắng thừa
        q = query.lower().strip()
        q = re.sub(r'\s+', ' ', q)
        return q

    def _keyword_boost(self, text, query):
        """
        Helper for Hybrid Keyword Scoring.
        """
        def norm(t): 
            return "".join(c for c in unicodedata.normalize('NFD', t.lower()) 
                          if unicodedata.category(c) != 'Mn')
        t_c, q_c = norm(text), norm(query)
        q_w = [w for w in q_c.split() if len(w) > 2]
        if not q_w: return 0
        return sum(1 for w in q_w if w in t_c) / len(q_w)

    # ... (Giữ nguyên các hàm detect_gibberish, resolve_pronoun) ...

    async def fetch_and_rerank(self, query: str, site_key: str, history: List[dict] = None):
        """
        [STEP 5] Hybrid Retrieve + Rerank
        - Retrieve: Vector Search (Semantic) from specified collection in config
        - Rerank: Cross-Encoder + Keyword Boost
        """
        # Load config for site to get collection and filter
        from app.core.config_loader import get_site_config
        site_config = get_site_config(site_key)
        
        if not site_config:
            logger.warning(f"⚠️ Site key '{site_key}' not found in config. Defaulting to 'culture'.")
            collection_name = "culture"
            filter_dict = {} # Global search fallback
        else:
            collection_name = site_config.get("collection", "culture") # Default to culture if missing
            filter_dict = site_config.get("filter", {}) # Default to empty filter if missing
            
        # [STATELESS] Không lưu history vào self.history để hỗ trợ multi-user
        # History được truyền vào từ request context nếu cần dùng cho retrieval metadata
        if history:
             pass # Logic xử lý history nếu cần (vd: preference profile)

        # Tạo vector cho câu hỏi
        # 🔧 FIX CASE SENSITIVITY: 
        # Nếu query toàn chữ thường (vd: 'ngô thì nhậm'), vector có thể lệch so với 'Ngô Thì Nhậm' trong DB.
        # Ta thử Auto-Capitalize (Title Case) để bắt tên riêng tốt hơn.
        queries_to_embed = [query]
        if query.islower():
            queries_to_embed.append(query.title()) # Thêm phiên bản viết hoa: "Ngô Thì Nhậm"
        
        # Lấy vector trung bình hoặc dùng vector tốt nhất? 
        # Đơn giản: Ưu tiên dùng phiên bản Title Case nếu có vẻ là tên riêng.
        # Hoặc search 2 lần merge kết quả.
        
        # CÁCH 2: Search bằng bản Title Case luôn nếu query ngắn (<10 từ) và lowercase
        target_query = query
        if query.islower() and len(query.split()) < 10:
             target_query = query.title()

        q_vec = self.embedder.encode([target_query])[0].tolist()
        
        # [FIX] Filter is already loaded from config above
        # filter_dict = {"metadata.site_key": site_key} if site_key else {}
        
        # === LOGGING CHI TIẾT ===
        logger.info(f"📚 [Knowledge Base] Retrieval Details:")
        logger.info(f"   ├─ Collection: '{collection_name}'")
        logger.info(f"   ├─ Filter: {filter_dict if filter_dict else 'None (Global Search)'}")
        logger.info(f"   ├─ Query (processed): '{target_query}'")
        logger.info(f"   └─ Limit: 15 candidates")

        # 1. Retrieve Candidates (Vector Search) - PHASE 1: Strict Site Filter
        candidates = await self.query(
            collection_name=collection_name,  # Dynamic collection
            query_vector=q_vec, 
            limit=15, 
            filter_dict=filter_dict
        )
        
        logger.info(f"   ✅ Retrieved {len(candidates)} candidates từ '{collection_name}' (Filter Strict)")

        # [NEW] PHASE 1.5: Fallback Unfiltered Search on SAME Collection
        # Nếu filter trả về 0 (có thể do lỗi Index chưa config filter field), thử tìm không filter
        if len(candidates) == 0 and site_key:
             logger.warning(f"⚠️ Filter Search trả về 0. Thử tìm KHÔNG filter trên '{collection_name}' (Check lỗi Index Atlas)...")
             unfiltered_candidates = await self.query(
                collection_name=collection_name,
                query_vector=q_vec,
                limit=10,
                filter_dict={} # Remove filter
             )
             # Post-filter bằng Python (nếu collection hỗn tạp)
             # Tuy nhiên nếu collection chuyên biệt (heritage chỉ có heritage) thì oke.
             # Nếu collection chung chung, ta cần check metadata.
             filtered_in_memory = []
             for c in unfiltered_candidates:
                 # Check 'heritage_type' or 'culture_type' field matches site_key
                 # Hoặc check metadata.site_key
                 c_site = c.get('metadata', {}).get('site_key')
                 # Dynamic field check
                 dyna_key = None
                 if 'heritage_type' in c: dyna_key = c['heritage_type']
                 elif 'culture_type' in c: dyna_key = c['culture_type']
                 
                 if c_site == site_key or dyna_key == site_key:
                     filtered_in_memory.append(c)
             
             if filtered_in_memory:
                 logger.info(f"   ✅ Tìm thấy {len(filtered_in_memory)} chunks khi bỏ Index Filter (Lỗi cấu hình Atlas!)")
                 candidates.extend(filtered_in_memory)
             else:
                 logger.info(f"   ❌ Vẫn không tìm thấy gì trên '{collection_name}' kể cả khi bỏ filter.")

        # PHASE 2: Global Fallback (Nếu tìm trong site không thấy, tìm toàn bộ kho)
        # Nếu filter filters quá chặt làm mất data (ví dụ Cột Cờ nằm file riêng nhưng user hỏi Hoàng Thành)
        if len(candidates) < 3 and site_key: 
            logger.info(f"⚠️ [FALLBACK PHASE 2] Ít kết quả ({len(candidates)} chunks). Mở rộng → Global Search (Multi-Collection)...")
            
            # List of collections to search
            fallback_cols = ["heritage", "culture", "history", "sites"]
            # Exclude current primary collection to avoid redundant search
            fallback_cols = [c for c in fallback_cols if c != collection_name]
            
            import asyncio
            # Run queries concurrently using self.query (async wrapper)
            tasks = [
                self.query(col, q_vec, limit=5, filter_dict={}) 
                for col in fallback_cols
            ]
            results_list = await asyncio.gather(*tasks)
            
            added_count = 0
            existing_ids = {c.get('id', str(c.get('content'))) for c in candidates} # Use content as fallback ID
            
            for res_batch, col_name in zip(results_list, fallback_cols):
                 for gc in res_batch:
                    # Simple dedupe
                    chk = gc.get('id', gc.get('content'))
                    if chk not in existing_ids:
                        # Mark source collection for debugging
                        if 'metadata' not in gc: gc['metadata'] = {}
                        gc['metadata']['fallback_source'] = col_name
                        candidates.append(gc)
                        existing_ids.add(chk)
                        added_count += 1
            
            logger.info(f"   ✅ Thêm {added_count} chunks từ Global Search. Tổng: {len(candidates)}")
        if len(candidates) < 1:
            logger.info(f"⚠️ [FALLBACK PHASE 3] Không có kết quả Vector Search. Thử Regex...")
            try:
                # Tạo regex query: "ngo thi nham" -> "ngo.*thi.*nham"
                # Chỉ áp dụng nếu query ngắn (< 5 từ) tránh regex quá dài chậm DB
                simple_q = query.lower()
                clean_q = re.sub(r'[^\w\s]', '', simple_q).strip() 
                if len(clean_q.split()) < 6:
                    regex_pat = ".*".join(clean_q.split())
                    
                    # Regex across collections? No, just primary + heritage/culture as backup.
                    regex_cols = [collection_name]
                    if collection_name != "culture": regex_cols.append("culture")
                    if collection_name != "heritage": regex_cols.append("heritage")
                    
                    # Deduplicate collections
                    regex_cols = list(set(regex_cols))
                    logger.info(f"   → Regex Pattern: '{regex_pat}' on {regex_cols}")
                    
                    for col in regex_cols:
                        regex_candidates = self.v_db.find_regex(
                            collection_name=col,
                            regex_pattern=regex_pat,
                            limit=2
                        )
                        for rc in regex_candidates:
                           rc['score'] = 0.4 # Default score for regex match
                           if not any(c.get('content') == rc['content'] for c in candidates):
                                 candidates.append(rc)
            except Exception as e:
                logger.error(f"Regex Search Error: {e}")

        if not candidates:
            logger.warning(f"❌ Không tìm thấy chunks nào (tất cả fallback đều fail)")
            return None # Return None để agentic workflow kích hoạt LLM Fallback

        # 2. Rerank (Hybrid: Semantic Score + Keyword Match)
        # Fix: Với Regex candidate (không có 'id'), có thể gây lỗi reranker predict nếu data lạ.
        # Clean candidates list
        valid_candidates = [c for c in candidates if 'content' in c]
        
        if not valid_candidates:
            return None
        
        logger.info(f"🔄 [RERANK] Processing {len(valid_candidates)} candidates...")
        pairs = [[query, c['content']] for c in valid_candidates]
        scores = self.reranker.predict(pairs)

        for i, res in enumerate(valid_candidates):
            k_boost = self._keyword_boost(res['content'], query)
            # Adjust score calculation
            base_score = scores[i]
            res['final_score'] = (base_score * 0.7) + (k_boost * 0.3)

        valid_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Log top 3
        logger.info(f"   📊 Top 3 Results:")
        for i, c in enumerate(valid_candidates[:3]):
            source = c.get('metadata', {}).get('source', 'unknown')
            score = c.get('final_score', 0)
            preview = c['content'][:80].replace('\n', ' ')
            logger.info(f"      {i+1}. Score={score:.3f} | Source={source} | '{preview}...'")

        # [STRICT FILTER] Kiểm tra điểm số của Top 1
        if not valid_candidates:
            return None
            
        top_score = valid_candidates[0]['final_score']
        # Ngưỡng chặn (Threshold):
        # CrossEncoder score thường là logit.
        # Match tốt: > 0.Match khá: > -2. Match tệ: < -4.
        # Set ngưỡng -2.0 để an toàn (Múa rối vs Lam Sơn ra -6.x -> Sẽ bị chặn)
        MIN_SCORE_THRESHOLD = -2.0
        
        if top_score < MIN_SCORE_THRESHOLD:
            logger.warning(f"⚠️ [STRICT MODE] Top 1 score ({top_score:.3f}) quá thấp (< {MIN_SCORE_THRESHOLD}). Coi như không tìm thấy.")
            return None

        answer = "\n\n".join([c['content'] for c in valid_candidates[:3]])
        
        logger.info(f"✅ [HERITAGE RAG] Trả về {len(answer)} ký tự context từ top-3 chunks")

        # ⭐ GRAPH EXPANSION: Expand context bằng Knowledge Graph
        graph_context = self._graph_expand(query, site_key)
        if graph_context:
            answer = answer + "\n\n" + graph_context
            logger.info(f"🕸️  [Graph] Appended {len(graph_context)} chars graph context")

        return answer

    def _graph_expand(self, query: str, site_key: Optional[str] = None) -> str:
        """
        ⭐ Hybrid RAG Graph Layer:
        1. Tìm entities trong query
        2. Query knowledge_graph collection
        3. Format thành text đưa vào LLM context
        """
        if self.graph is None:
            return ""

        try:
            site_triples = []
            entity_triples = []

            # B1: Lấy triples của site hiện tại (breadth)
            if site_key:
                site_triples = self.graph.get_by_site(site_key, limit=20)
                logger.info(f"   🕸️  [Graph B1] Site '{site_key}': {len(site_triples)} triples")

            # B2: Tìm entities trong query — dùng cách tách từ đơn giản hơn regex
            # Tách query thành các cụm từ 2-4 từ liên tiếp
            words = query.split()
            candidates = []
            for n in [3, 2, 4]:  # Ưu tiên cụm 3 từ, rồi 2, rồi 4
                for i in range(len(words) - n + 1):
                    phrase = " ".join(words[i:i+n])
                    # Loại bỏ cụm có từ nối phổ biến
                    skip_words = {"là", "và", "có", "gì", "của", "đến", "từ", "trong", "với", "không", "nào", "được"}
                    phrase_words = set(phrase.lower().split())
                    if len(phrase) >= 4 and not phrase_words.issubset(skip_words):
                        candidates.append(phrase)

            # Deduplicate và lấy max 5
            seen = set()
            unique_candidates = []
            for c in candidates:
                if c not in seen:
                    seen.add(c)
                    unique_candidates.append(c)

            logger.info(f"   🕸️  [Graph B2] Entity candidates: {unique_candidates[:5]}")
            for entity in unique_candidates[:5]:
                et = self.graph.get_neighbors(entity, depth=2, max_nodes=8)
                if et:
                    logger.info(f"      → '{entity}': +{len(et)} triples")
                entity_triples.extend(et)

            # Merge: Entity-specific triples TRƯỚC (liên quan hơn), site triples sau
            triples = entity_triples + site_triples

            if not triples:
                logger.info(f"   🕸️  [Graph] No triples → skip")
                return ""

            formatted = self.graph.format_triples_as_context(triples)
            if not formatted:
                return ""

            # Log 3 sample triples đầu (bây giờ là entity triples)
            sample_lines = formatted.strip().split("\n")[:3]
            logger.info(f"   🕸️  [Graph] {len(triples)} triples | Top sample:")
            for line in sample_lines:
                logger.info(f"      {line.strip()}")

            return f"\n🔗 MỐI QUAN HỆ (Knowledge Graph):\n{formatted}"

        except Exception as e:
            logger.warning(f"⚠️ [Graph] Expand error (non-critical): {e}")
            return ""

    def detect_gibberish_query(self, query: str, history: List[dict] = None) -> Tuple[bool, Optional[str]]:
        """
        🔧 NEW: Detect câu gibberish (ngắn, vô nghĩa, không rõ ý)
        """
        query_lower = query.lower().strip()
        history = history or [] # Safe fallback
        
        # Nếu câu quá ngắn (e.g., "hdpp", "v.v", "chi chi", "gì gì")
        if len(query_lower) < 10:
            # Kiểm tra nếu là những từ thường dùng trong gibberish
            gibberish_patterns = [
                "hdpp", "v.v", "vv", "vân vân", "v", "chi", "gì gì", "kháyy", "chi chi",
                "thế nào", "tại sao", "như nào", "cái gì", "cái chi", "ai", "cô", "cái",
                "à", "ơi", "ơi", "này", "kia", "kìa"
            ]
            
            is_gibberish = any(pattern in query_lower for pattern in gibberish_patterns)
            
            if is_gibberish and history:
                # Lấy topic từ câu hỏi trước
                prev_entry = history[-1] if history else None
                if prev_entry:
                    prev_question = prev_entry.get('user_input', '')
                    prev_site = prev_entry.get('site')
                    logger.info(f"🔍 GIBBERISH DETECTED: '{query}' → sử dụng context: '{prev_question}'")
                    
                    # Tạo hint để LLM hiểu là follow-up
                    hint = f"[Follow-up question về: {prev_question}]"
                    return True, hint
                else:
                    return True, None
        
        return False, None

    def resolve_pronoun(self, user_input: str, history: List[dict] = None) -> Tuple[str, Optional[str]]:
        """
        🔧 IMPROVED: Xử lý đại từ + gibberish + trả về (rewritten_query, site_hint)
        - Nếu có đại từ → sử dụng context lịch sử
        - Nếu gibberish → sử dụng topic trước
        - Trả về site hint để planner có thêm info
        """
        pronouns = ["nó", "đó", "chỗ này", "nơi đó", "chỗ đó"]
        user_lower = user_input.lower()
        history = history or []
        
        # 🔧 BƯỚC 1: Kiểm tra pronoun
        has_pronoun = any(p in user_lower for p in pronouns)
        
        if has_pronoun and history:
            # Tìm câu hỏi gần nhất trong lịch sử
            for entry in reversed(history[-3:]):  # Kiểm tra 3 câu gần nhất
                user_q = entry.get('user_input', '').lower()
                
                # Tìm site từ câu hỏi trước
                prev_site = entry.get('site')
                if prev_site:
                    logger.info(f"📌 Pronoun resolved: '{user_input}' → site={prev_site}")
                    return user_input, prev_site
        
        # 🔧 BƯỚC 2: Kiểm tra gibberish
        is_gibberish, gibberish_hint = self.detect_gibberish_query(user_input, history)
        if is_gibberish:
            logger.info(f"🔍 Gibberish query detected: '{user_input}'")
            if history:
                # Lấy topic + site từ câu hỏi trước
                prev_entry = history[-1]
                prev_question = prev_entry.get('user_input', '')
                prev_site = prev_entry.get('site')
                
                # Tạo rewritten query kết hợp gibberish + context trước
                rewritten = f"{user_input} (theo câu hỏi trước: {prev_question})"
                logger.info(f"   Rewritten: '{user_input}' → site={prev_site}, hint={prev_question}")
                return rewritten, prev_site
        
        # Không có pronoun/gibberish → trả query gốc + None
        return user_input, None



    async def query(self, collection_name: str, query_vector: List[float], limit: int, filter_dict: dict):
        """
        Truy vấn Vector Database và trả về các kết quả phù hợp.
        """
        # Sử dụng phương thức query từ VectorDatabase
        results = self.v_db.query(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            filter_dict=filter_dict
        )
        return results
