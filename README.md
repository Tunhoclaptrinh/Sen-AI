# Sen NPC - Agentic RAG Heritage Assistant

![Status](https://img.shields.io/badge/Status-Active_Development-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Architecture](https://img.shields.io/badge/Architecture-Agentic_RAG-orange)

> **"Không chỉ là Hỏi-Đáp. Đây là Trải nghiệm Nghe-Nhìn về Di sản."**
>
> Sen NPC là một trợ lý ảo thông minh (AI Agent) chuyên biệt cho lĩnh vực Di sản & Văn hóa Việt Nam, tích hợp khả năng giao tiếp Voice-to-Voice, tra cứu Semantic Search thời gian thực và tự động kiểm chứng nội dung.

---
## 📑 Mục lục
1. [Tổng quan (Overview)](#-tổng-quan-overview)
2. [Tính năng Chính (Key Features)](#-tính-năng-chính-key-features)
3. [Kiến trúc Hệ thống (Architecture)](#-kiến-trúc-hệ-thống-architecture)
4. [Cấu trúc Dự án (Project Structure)](#-cấu-trúc-dự-án-project-structure)
5. [Yêu cầu Tiền quyết (Prerequisites)](#-yêu-cầu-tiền-quyết-prerequisites)
6. [Cài đặt & Chạy Local (Quickstart)](#-cài-đặt--chạy-local-quickstart)
7. [Cấu hình (Configuration)](#-cấu-hình-configuration)
8. [API Reference](#-api-reference)
9. [Triển khai Production (Deployment)](#-triển-khai-production-deployment)
10. [Bảo mật & Vận hành (Security & Ops)](#-bảo-mật--vận-hành-security--ops)
11. [Xử lý sự cố (Troubleshooting)](#-xử-lý-sự-cố-troubleshooting)

---

## 🔭 Tổng quan (Overview)

### 🎯 Mục tiêu (Goals)
*   Cung cấp trải nghiệm hỏi đáp tự nhiên về lịch sử, di tích Việt Nam thông qua giọng nói.
*   Giải quyết vấn đề "ảo giác" (hallucination) thường gặp ở LLM bằng cơ chế **Strict RAG** & **Verifier**.
*   Cung cấp thông tin thiết thực (giá vé, giờ mở cửa, thời tiết) thông qua Live Tools.

### ⛔ Giới hạn (Non-goals)
*   Không phải là Chatbot đa năng (như ChatGPT) để code, làm toán hay tâm sự chuyện đời tư.
*   Không lưu trữ vĩnh viễn lịch sử chat của user (Stateless REST API design).

---

## ✨ Tính năng Chính (Key Features)

*   **🎙️ Voice-to-Voice Interaction:** Tích hợp OpenAI Whisper (STT) và EdgeTTS/GoogleTTS (TTS) cho phản hồi giọng nói tự nhiên.
*   **🧠 Agentic Workflow:** Sử dụng LLM Planner để định tuyến thông minh giữa:
    *   **Heritage:** Tra cứu kiến thức lịch sử (RAG).
    *   **Realtime:** Tra cứu thời tiết, link đặt vé, giờ mở cửa.
    *   **Chitchat:** Giao tiếp xã giao.
*   **📚 Hybrid Search RAG:** Kết hợp Vector Search (Semantic) + Keyword Boosting + Re-ranking để tìm kiếm thông tin chính xác nhất.
*   **🛡️ Strict Mode & Verifier:**
    *   Chặn trả lời nếu độ khớp câu hỏi thấp (Threshold checking).
    *   Lớp bảo vệ (Verifier) dùng LLM để rà soát lại câu trả lời trước khi gửi (đảm bảo không bịa đặt).
*   **⚡ Smart Caching:** Redis Cache cho các câu hỏi lặp lại (TTL 1 giờ), giảm chi phí LLM và độ trễ.
*   **🔗 Dynamic Config:** Cấu hình địa điểm, link vé, mô tả ngữ nghĩa qua file JSON nóng (không cần sửa code).

---

## 🏗 Kiến trúc Hệ thống (Architecture)

### Agentic RAG Workflow

```ascii
User Input (Audio/Text)
       ⬇
[STT Service (Whisper)]
       ⬇
[🔍 Semantic Router / Planner] ───(Out of Scope)──➡ ⛔ Từ chối
       │
       ├────(Chitchat) ──────➡ [💬 Persona Engine] ──➡ (To Synthesize)
       │
       ├────(Realtime) ──────➡ [🛠️ External Tools] (Weather, Time, Ticket Links)
       │                              ⬇
       └────(Heritage) ──────➡ [💾 Redis Cache Check]
                                      │
              (Cache Miss) ⬅─────────┘
                   │
           [📚 Vector DB Retrieval] (MongoDB Atlas)
                   ⬇
           [📊 Cross-Encoder Rerank] ──(Low Score)──➡ ⛔ "Không tìm thấy thông tin"
                   ⬇
           [🧠 Contextual Synthesis] (GPT-4o)
                   ⬇
           [🕵️ Content Verifier] (Optional Safety Layer)
                   ⬇
[🔊 TTS Synthesizer] (Edge/Google/OpenAI)
       ⬇
Response (Text + Audio)
```

### Giải thích Module
*   **Router (Planner):** Phân tích intent người dùng dựa trên từ khóa và ngữ nghĩa (Prompt Engineering).
*   **Retriever:** Query Vector DB (MongoDB Atlas) sử dụng embeddings (`paraphrase-multilingual-MiniLM-L12-v2`).
*   **Verifier:** Một LLM instance riêng biệt, đóng vai "Cảnh sát" so sánh câu trả lời với Context gốc.
*   **Ingestor:** Script độc lập giúp nạp dữ liệu từ file Text/MD vào Vector DB.

---

## � Cấu trúc Dự án (Project Structure)

```bash
STT-Agentic-RAG/
├── .env                  # (Gitignored) Biến môi trường & Secrets
├── .gitignore            # Cấu hình Git ignore
├── app.py                # Main Entry: FastAPI Server
├── agentic_rag_workflow.py # Core Logic: Workflow điều phối Agent
├── heritage_tool.py      # Tools: Weather, Ticket, Opening Status
├── knowledge_base.py     # RAG: Search, Rerank, Embedding logic
├── verifier.py           # Safety: Kiểm chứng nội dung
├── prompts.py            # Quản lý & Load Prompts
├── ingest_data.py        # Script: Nạp dữ liệu vào DB
├── clear_cache.py        # Script: Xóa Redis Cache
├── requirements.txt      # Python Dependencies
├── data/
│   ├── documents/        # Folder chứa file text/md cần nạp
│   ├── monuments.json    # Config các địa điểm (Metadata, Links)
│   └── prompts.json      # File chứa Prompt (Planner, Persona, etc)
└── README.md             # Tài liệu dự án
```

---

## ✅ Yêu cầu Tiền quyết (Prerequisites)

*   **OS:** Windows 10/11, macOS, hoặc Linux.
*   **Python:** 3.10 trở lên.
*   **Database:**
    *   **MongoDB Atlas:** Cluster M0 (Free) trở lên (bật Vector Search).
    *   **Redis:** Local server hoặc Cloud (Upstash/RedisLabs).
*   **API Keys:** OpenAI API Key (có credit).

---

## 🚀 Cài đặt & Chạy Local (Quickstart)

### 1. Clone & Setup Environment
```bash
git clone <your-repo-url>
cd STT-Agentic-RAG
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Cấu hình Environment
Tạo file `.env` từ template bên dưới và điền API Key vào:
```ini
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster...
OPENAI_API_KEY=sk-...
REDIS_URL=redis://...
BOT_NAME=Sen
ENABLE_VERIFIER=true
```

### 3. Nạp Dữ liệu (Ingest Data)
Chuẩn bị file nội dung vào `data/documents/` (ví dụ `lam_son.txt`), sau đó chạy:
```bash
python ingest_data.py
```

### 4. Khởi chạy Server
```bash
python -m uvicorn app:app --port 8000 --reload
```
*   API Docs: `http://localhost:8000/docs`
*   Health Check: `http://localhost:8000/`

---

## ⚙️ Cấu hình (Configuration)

### Các tham số quan trọng (.env)

| Biến | Mô tả | Mặc định/Ví dụ |
| :--- | :--- | :--- |
| `MONGODB_URI` | Kết nối Vector DB | `mongodb+srv://...` |
| `OPENAI_API_KEY` | Key chạy LLM & STT | `sk-...` |
| `REDIS_URL` | Kết nối Cache | `redis://localhost:6379` |
| `BOT_NAME` | Tên nhân vật NPC | `Sen` |
| `ENABLE_VERIFIER` | Bật/Tắt kiểm duyệt | `true` hoặc `false` |

### Cấu hình RAG & Tools
*   **Chunk Size:** 800 tokens (Hardcoded trong `ingest_data.py`).
*   **Top K Retrieval:** 15 candidates.
*   **Reranker Threshold:** -2.0 (Trong `knowledge_base.py`).
*   **Cache TTL:** 3600 giây (1 giờ).

---

## � API Reference

### 1. Chat Text
*   **Endpoint:** `POST /chat`
*   **Description:** Giao tiếp bằng văn bản.
*   **Body:**
    ```json
    {
      "user_input": "Hoàng Thành Thăng Long ở đâu?",
      "history": [] 
    }
    ```

### 2. Chat Audio (Voice-to-Voice)
*   **Endpoint:** `POST /chat-audio`
*   **Description:** Upload file âm thanh, nhận về text và audio câu trả lời.
*   **Body (Multipart):** `file: <audio.wav/mp3/webm>`

### 3. Quản lý Cache
*   **Endpoint:** `POST /cache/clear`
*   **Description:** Xóa toàn bộ bộ nhớ Redis của Bot.

---

## 🚢 Triển khai Production (Deployment)

### Mô hình đề xuất
Sử dụng **Docker** (TODO: Cần tạo Dockerfile) hoặc chạy trực tiếp với **PM2/Systemd** phía sau **Nginx**.

### Nginx Reverse Proxy Config (Ví dụ)
```nginx
server {
    listen 80;
    server_name api.sennpc.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Cấu hình cho WebSocket (nếu dùng)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Ghi chú Scale
*   **Stateless:** API hiện tại là stateless (History gửi từ client), nên có thể chạy nhiều Worker (`uvicorn app:app --workers 4`).
*   **Redis:** Đảm bảo dùng chung Redis instance nếu scale nhiều server để đồng bộ Cache.

---

## �️ Bảo mật & Vận hành (Security & Ops)

### Security Checklist
*   [x] **HTTPS:** Bắt buộc sử dụng SSL (Let's Encrypt) khi deploy live để trình duyệt cho phép ghi âm.
*   [x] **API Keys:** Không bao giờ commit `.env`.
*   [ ] **Rate Limit:** TODO: Cần thêm middleware giới hạn request/phút để tránh DDOS hoặc tốn tiền OpenAI.
*   [ ] **Auth:** TODO: Thêm cơ chế API Key hoặc JWT cho Client nếu cần bán dịch vụ.

### Observability
*   **Logging:** Hệ thống log ra console (stdout). Nên pipe vào CloudWatch hoặc Filebeat.
*   **Trace ID:** Hiện tại log theo flow. TODO: Gán UID cho mỗi request để trace dễ hơn.

---

## 🔧 Xử lý sự cố (Troubleshooting)

**1. Lỗi `403 Forbidden` từ EdgeTTS:**
*   *Nguyên nhân:* Microsoft chặn IP hoặc thay đổi token.
*   *Xử lý:* Hệ thống tự fallback sang Google Translate TTS. Không cần hành động, hoặc chuyển sang OpenAI TTS (chỉnh code).

**2. Lỗi `Method Not Allowed` (GET /chat):**
*   *Nguyên nhân:* Truy cập API bằng trình duyệt.
*   *Xử lý:* Dùng Postman hoặc Client gửi request POST.

**3. MongoDB Connection Timeout:**
*   *Nguyên nhân:* Sai IP Whitelist trên Atlas.
*   *Xử lý:* Vào Network Access trên MongoDB Atlas -> Add Current IP.

**4. Bot trả lời "Sen chỉ là AI..." (Mất persona):**
*   *Nguyên nhân:* Lỗi load file `prompts.json` hoặc biến `BOT_NAME`.
*   *Xử lý:* Check log khởi động xem có báo lỗi load prompt không.

**5. Import Error `ModuleNotFoundError`:**
*   *Nguyên nhân:* Chưa activate venv hoặc chưa install requirements.
*   *Xử lý:* Chạy lại `pip install -r requirements.txt`.

---

## 🤝 Contributing
Dự án closed-source phục vụ mục đích nghiên cứu/sản phẩm riêng.
Mọi Pull Request cần qua review của Maintainer chính.

## 📜 License
MIT License.
