# 🧠 SEN AI - BỘ NHỚ HỆ THỐNG (MEMORY)

> **Mục đích**: File này lưu toàn bộ ngữ cảnh về sen-ai, giúp mỗi lần làm việc đều hiểu được hệ thống đã có gì, hoạt động ra sao.
>
> **Cập nhật lần cuối**: 2026-02-24 (Semantic Cache + Graph RAG fixes)

---

## 📌 TỔNG QUAN

**sen-ai** là backend AI phục vụ nhân vật hướng dẫn viên ảo tên **"Sen"**, chuyên về **Di sản Văn hóa Việt Nam**. Sen tương tác với người dùng qua chat (text/voice) để cung cấp thông tin về các di tích lịch sử, văn hóa, đồng thời hỗ trợ trong game giáo dục.

### Tech Stack:
- **Framework**: FastAPI (Python)
- **LLM**: OpenAI GPT-4o-mini (AsyncOpenAI)
- **Embedding**: `paraphrase-multilingual-MiniLM-L12-v2` (SentenceTransformer, 384 dims)
- **Reranker**: CrossEncoder (SentenceTransformers)
- **Vector DB**: MongoDB Atlas Vector Search
- **Cache / Session**: Redis (Async)
- **TTS**: Edge TTS (chính) → Google TTS (fallback)
- **STT**: OpenAI Whisper API
- **Deploy**: Docker + Docker Compose

---

## 📂 CẤU TRÚC THƯ MỤC

```
sen-ai/
├── main.py                    # FastAPI app, endpoints, TTS, startup
├── ingest.py                  # Nạp dữ liệu vào Vector DB + Graph extraction
├── build_graph.py             # ⭐ [NEW] Script chạy 1 lần build Knowledge Graph từ MongoDB
├── requirements.txt           # Dependencies
├── docker-compose.yml         # Docker Compose (sen-api + redis)
├── Dockerfile
├── data/
│   ├── monuments.json         # Cấu hình di tích (key, name, collection, filter, coords...)
│   ├── prompts.json           # Tất cả system prompts (planner, persona, verifier, contextualize)
│   └── documents/
│       ├── hoang_thanh.md     # Tài liệu Hoàng Thành Thăng Long (~1MB)
│       └── mua_roi_nuoc.md   # Tài liệu Múa Rối Nước (~62KB)
├── app/
│   ├── core/
│   │   ├── config_loader.py   # Load monuments.json, quản lý danh sách di tích
│   │   ├── config_prompts.py  # Load prompts.json, build dynamic planner prompt
│   │   ├── vector_db.py       # MongoDB Atlas Vector Search client
│   │   ├── graph_store.py     # ⭐ [NEW] Knowledge Graph CRUD (MongoDB collection knowledge_graph)
│   │   └── semantic_cache.py  # ⭐ [NEW] Semantic Cache (cosine similarity, MongoDB query_cache)
│   ├── services/
│   │   ├── workflow.py        # ⭐ CORE: Agentic RAG workflow (stream + non-stream)
│   │   ├── knowledge.py       # KnowledgeBase: semantic routing, RAG, rerank, pronoun resolution
│   │   ├── tools.py           # HeritageTools: weather, opening status, ticket prices
│   │   ├── emotion.py         # EmotionAnalyzer: cảm xúc → biểu cảm cho avatar
│   │   └── verifier.py        # Verifier: kiểm chứng câu trả lời (anti-hallucination)
│   └── utils/
│       ├── cache.py           # Clear Redis cache
│       └── cleaner.py         # Xóa temp files khỏi Vector DB
```

---

## 🔄 LUỒNG XỬ LÝ CHÍNH (Agentic RAG Workflow)

```
User Input → Normalize → Contextualize (Rewrite) → Cache Check
  → Semantic Site Routing → LLM Planner (Intent Detection)
  → [Intent Branch]:
      ├── HERITAGE  → Vector Search + Rerank
      │               + ⭐ Graph Expand (knowledge_graph)
      │               → Merge Context → LLM Generate → Verifier (optional)
      ├── REALTIME  → RAG + Tools (Weather/Opening/Ticket) → LLM Generate
      ├── CHITCHAT  → Direct LLM Response (persona + constraints)
      ├── OUT_OF_SCOPE → Polite Refusal (liệt kê site đang có)
  → Emotion Analysis → TTS (optional) → Cache Save → Response
```

### Các bước chi tiết:

1. **Normalize**: Chuẩn hóa unicode, lowercase
2. **Contextualize**: GPT-4o-mini rewrite câu ngắn/mơ hồ thành đầy đủ (xử lý đại từ, follow-up)
3. **Cache Check**: Redis (`sen:cache:{query}`). Bỏ qua cache nếu có Game Context
4. **Semantic Routing**: Cosine similarity tìm top-3 di tích phù hợp
5. **Planner**: GPT-4o-mini + dynamic prompt → JSON `{intent, site}`
6. **Execution**:
   - Heritage: Vector Search → Cross-Encoder Rerank + Keyword Boost
               → ⭐ Graph Expand (query `knowledge_graph` collection) → Merge → LLM Generate
   - Realtime: RAG + parallel tools (weather, opening, ticket) → LLM Generate
   - Chitchat: Direct LLM với persona, thời gian thực, site hints
   - Out of Scope: LLM refusal, giới thiệu known sites
7. **Verifier** (optional): Kiểm hallucination
8. **Emotion**: Rule-based → gesture, mouthState, eyeState cho avatar
9. **TTS**: Edge TTS → Base64 audio
10. **Cache Save**: Heritage → Redis TTL 1 giờ

---

## 📡 API ENDPOINTS

| Method | Path | Mô tả |
|--------|------|--------|
| `GET` | `/` | Health check |
| `POST` | `/chat` | Chat (non-streaming) |
| `POST` | `/chat/stream` | Chat (SSE streaming) ⭐ Chính |
| `POST` | `/chat-audio` | Audio → STT → Chat → TTS |
| `POST` | `/api/tts` | Text-to-Speech |
| `WS` | `/ws/chat` | WebSocket real-time chat |
| `GET` | `/data-source` | Kiểm tra nguồn dữ liệu |
| `GET` | `/cache/stats` | Thống kê cache |
| `POST` | `/cache/clear` | Xóa toàn bộ cache |
| `DELETE` | `/cache/{query}` | Xóa 1 entry cache |

---

## 🗄️ DỮ LIỆU HIỆN CÓ

### Di tích (monuments.json):
| Key | Tên | Collection | Filter |
|-----|-----|------------|--------|
| `hoang_thanh` | Hoàng Thành Thăng Long | `heritage` | `heritage_type: "hoang_thanh"` |
| `mua_roi_nuoc` | Múa Rối Nước - Nhà hát Thăng Long | `culture` | `culture_type: "mua_roi_nuoc"` |

### Tài liệu (data/documents/):
- `hoang_thanh.md` (~1MB)
- `mua_roi_nuoc.md` (~62KB)

### Vector DB Collections & Index:
- Collections: `heritage`, `culture`, `history`, `knowledge_graph` (⭐ NEW)
- Index: `vector_index` (384 dims, cosine, filter: `culture_type`/`heritage_type`/`history_type`/`metadata.level`)
- `knowledge_graph` collection: **KHÔNG cần Vector Index** — chỉ dùng regular B-tree index (tự tạo khi app start)

### Cấu trúc document trong `knowledge_graph`:
```json
{
  "subject": "Hoàng Thành Thăng Long",
  "relation": "XÂY_BỞI",
  "object": "Lý Thái Tổ",
  "site_key": "hoang_thanh",
  "confidence": 0.95,
  "source": "ingest:hoang_thanh.md"
}
```

---

## 🎭 PERSONA SEN

- **Xưng hô**: "Tớ" → gọi khách "Cậu"
- **Giọng**: Thân thiện, dí dỏm, lễ phép
- **KHÔNG**: Dùng từ tech (Context, RAG, Database), bịa đặt, bàn chính trị/tôn giáo
- **Prompts** (data/prompts.json): `planner_prompt`, `sen_persona`, `contextualize_prompt`, `verifier_prompt`

---

## 🎮 TÍCH HỢP GAME

- Frontend gửi system message chứa Level/Chapter → Workflow detect → **disable cache**
- Planner nhận level constraint → chỉ cho phép site thuộc level đó
- Hỏi sai level → chitchat (từ chối khéo)

### Emotion System (avatar 3D):
- **Gesture**: normal, hello, point, like, flag, hand_back
- **Mouth**: smile, smile_2, sad, open, close, half, tongue
- **Eye**: normal, blink, close, half, like, sleep

---

## ✅ FEATURES ĐÃ CÓ

### Core:
- [x] Agentic RAG Workflow (stream + non-stream)
- [x] 4 Intents: heritage, realtime, chitchat, out_of_scope
- [x] Semantic Site Routing (cosine similarity)
- [x] Hybrid Retrieval (Vector Search + Keyword Boost)
- [x] Cross-Encoder Reranking
- [x] ⭐ **Hybrid Graph RAG** (Vector + Knowledge Graph)
- [x] ⭐ **Semantic Cache** (cosine similarity, không phải exact string)
- [x] Query Contextualization (Rewrite câu mơ hồ)
- [x] Pronoun Resolution (đại từ "nó", "đó")
- [x] Gibberish Detection
- [x] Redis Session History (20 turns)

### Tools:
- [x] Weather API (Open-Meteo) + đánh giá + lời khuyên
- [x] Opening Status (giờ mở/đóng + lời khuyên)
- [x] Ticket Prices (trả link, không hardcode giá)

### Voice:
- [x] STT: Whisper API (+ transcribe-only mode)
- [x] TTS: Edge TTS + Google TTS fallback
- [x] Auto TTS trong stream + clean markdown/emoji/URL

### Safety:
- [x] Verifier (anti-hallucination, env `ENABLE_VERIFIER`)
- [x] Out-of-Scope Refusal + Unknown Site Detection
- [x] Strict RAG Mode (không bịa nếu DB trống)
- [x] General Knowledge Fallback (có disclaimer)

### DevOps:
- [x] Docker + docker-compose (sen-api + redis)
- [x] CORS, health check, cache management

---

## ⚙️ ENV VARIABLES

| Variable | Mô tả | Default |
|----------|--------|---------|
| `MONGODB_URI` | MongoDB Atlas connection | (required) |
| `OPENAI_API_KEY` | OpenAI API key | (required) |
| `REDIS_URL` | Redis URL | (required) |
| `BOT_NAME` | Tên nhân vật | `Sen` |
| `ENABLE_VERIFIER` | Bật Verifier | `false` |
| `ENABLE_FILE_LOGGING` | Ghi log chat ra file | `true` |
| `DOCUMENTS_SRC_DIR` | Thư mục tài liệu | `data/documents` |
| `ENABLE_GRAPH_EXTRACTION` | ⭐ Bật extract Knowledge Graph khi ingest | `true` |

---

## 📝 VẤN ĐỀ ĐÃ XỬ LÝ

1. **Xưng hô sai** - "Bác" → "Cậu" → Fix trong prompts
2. **Routing sai source** - hoang_thanh nhảy vào mua_roi_nuoc → Fix semantic routing
3. **MongoDB Index** - `heritage_type` cần indexed as filter
4. **TTS Permission Denied** → Dùng `tempfile.gettempdir()`
5. **Hallucination** → Strict RAG + Verifier
6. **Out-of-scope sai** - Heritage bị coi out_of_scope → Improved refusal logic
7. **Cache sai level** → Disable cache khi có game context
8. **General mode** - Không trả lời được giờ → Inject thời gian thực
9. **Hidden Object hints** → Enhanced game context
10. **Cache luôn MISS** - key dùng rewrite query (thay đổi mỗi lần) → Fix: dùng norm_input
11. **Cache check sau RAG** - main.py check cache SAU khi gọi workflow → vô nghĩa → Fix: check TRƯỚC
12. **Entity detection sai tiếng Việt** - regex `[A-ZÀ-ỹ]` cắt nhầm `ều đại Nhà Lý` → Fix: N-gram sliding window
13. **Graph sample không liên quan** - entity triples bị chìm sau site triples → Fix: entity triples lên trước
14. **ingest.py `v_db.collection`** - AttributeError → Fix: `v_db.db[target_collection]`
15. **Windows asyncio warning** - `RuntimeError: Event loop is closed` sau ingest → Fix: WindowsSelectorEventLoopPolicy

---

## 🚀 TODO

- [ ] Thêm di tích mới (Văn Miếu, Chùa Một Cột, Hồ Gươm...)
- [x] ⭐ Knowledge Graph (Hybrid Graph RAG — DONE 2026-02-24)
- [x] ⭐ Semantic Cache (cosine similarity — DONE 2026-02-24)
- [ ] Adaptive Hinting System
- [ ] Admin Dashboard
- [ ] Multi-language support
- [ ] Performance optimization
- [ ] User feedback loop
- [ ] Custom TTS voice

---

> ⚡ **Quy trình thêm dữ liệu mới**:
> 1. Thêm entry vào `data/monuments.json`
> 2. Tạo file .md trong `data/documents/` (tên file PHẢI CHỨA site_key, vd: `hoang_thanh_v2.md`)
> 3. Chạy `python ingest.py` → tự động ghi vào `heritage`/`culture` VÀ `knowledge_graph`
> 4. Tạo Vector Search Index trên MongoDB Atlas (nếu collection mới — `knowledge_graph` và `query_cache` KHÔNG cần)

---

## 🕸️ HYBRID GRAPH RAG (Thêm ngày 2026-02-24)

### Mục tiêu:
Thêm **Knowledge Graph layer** on top of Vector RAG để AI có thể suy luận mối quan hệ giữa các thực thể (nhân vật, triều đại, sự kiện, địa danh).

### Kiến trúc:
```
Vector RAG (chunks)  +  Graph RAG (triples)
        ↓                       ↓
 "Hoàng Thành là..."    "Hoàng Thành [XÂY_BỞI] Lý Thái Tổ"
                                    ↓
                          Merge context → LLM
```

### Files thêm/sửa:
| File | Loại | Mô tả |
|---|---|---|
| `app/core/graph_store.py` | ⭐ Mới | GraphStore class: insert/query/BFS triples trong MongoDB |
| `build_graph.py` | ⭐ Mới | Script 1 lần: đọc chunks MongoDB → GPT extract → lưu knowledge_graph |
| `ingest.py` | Sửa | Sau khi lưu chunks → tự động extract triples vào knowledge_graph |
| `app/services/knowledge.py` | Sửa | Sau vector search → `_graph_expand()` merge thêm graph context |

### Cách chạy lần đầu (build graph từ data cũ):
```bash
# Preview (không lưu)
python build_graph.py --dry-run

# Chỉ build cho 1 site
python build_graph.py --site hoang_thanh

# Build tất cả
python build_graph.py
```

### Context LLM nhận được sau Hybrid RAG:
```
[Vector chunks - top 3]
Hoàng Thành Thăng Long là kinh đô của nhiều triều đại...

🔗 MỐI QUAN HỆ (Knowledge Graph):
  - Hoàng Thành Thăng Long [XÂY_BỞI] Lý Thái Tổ
  - Lý Thái Tổ [THUỘC_TRIỀU_ĐẠI] Nhà Lý
  - Nhà Lý [CHIẾN_THẮNG] Quân Tống
  - Hoàng Thành Thăng Long [ĐƯỢC_UNESCO_CÔNG_NHẬN_NĂM] 2010
```

### Lưu ý kỹ thuật:
- `knowledge_graph` collection **không cần Vector Search Index** — chỉ dùng regular B-tree index (tự tạo khi app start)
- Graph extraction dùng `gpt-4o-mini` + batch 5 chunks/lần
- Nếu graph extraction lỗi → **không ảnh hưởng** ingest vector (try/except riêng)
- Tắt graph extraction: set `ENABLE_GRAPH_EXTRACTION=false` trong `.env`

---

## 🧠 SEMANTIC CACHE (Thêm ngày 2026-02-24)

### Mục tiêu:
Thay thế exact string cache bằng **cosine similarity cache** — cache HIT ngay cả khi user hỏi cùng ý nhưng khác câu chữ.

### Ví dụ:
```
"Lý Thái Tổ là ai?"          ← đã cached
"Ai là Lý Thái Tổ?"          → similarity=0.94 → HIT ✅
"Cho biết về Lý Thái Tổ"     → similarity=0.88 → MISS ❌ (< 0.92)
```

### Kiến trúc:
```
Request
    ↓ normalize lowercase
    ↓ embed (SentenceTransformer, ~5ms, local RAM)
    ↓ load 500 entries từ MongoDB query_cache
    ↓ cosine similarity với từng entry
    ↓ max_score >= 0.92 → HIT → return cached (skip toàn bộ RAG)
    ↓ MISS → gọi workflow → save {query, embedding, response}
```

### File mới:
| File | Mô tả |
|---|---|
| `app/core/semantic_cache.py` | SemanticCache class: get/set với cosine similarity |

### Tích hợp:
- **`main.py startup()`**: `app.state.sem_cache = SemanticCache(db=v_db.db, embedder=embedder)`
- **`main.py /chat`**: Check sem_cache TRƯỚC khi gọi workflow; save sau khi workflow xong

### MongoDB collection `query_cache`:
```json
{
  "query": "lý thái tổ là ai?",
  "query_embedding": [0.12, -0.45, ...],  // 384 dims
  "response": { "answer": "...", "intent": "heritage", ... },
  "intent": "heritage",
  "expires_at": 1740000000.0   // TTL tự xóa qua MongoDB index
}
```

### Lưu ý kỹ thuật:
- **Không cần Atlas Vector Search Index** — cosine tính trong Python (numpy dot product)
- **Embedder dùng chung** với KnowledgeBase (load 1 lần, tiết kiệm ~500MB RAM)
- **Threshold**: 0.92 (điều chỉnh trong `semantic_cache.py: SIMILARITY_THRESHOLD`)
- **TTL**: 3600s (1 tiếng) — MongoDB TTL index tự xóa
- **Max entries load**: 500 (điều chỉnh `MAX_CACHE_ENTRIES`)
- Chỉ cache intent `heritage` (chitchat/realtime không cache vì phụ thuộc thời gian/tool)
