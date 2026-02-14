---
title: Sen AI - Trợ Lý Di Sản
emoji: 🌸
colorFrom: red
colorTo: pink
sdk: docker
pinned: false
app_port: 8000
---

# 🌸 Sen AI - Trợ Lý Ảo Di Sản Thông Minh
> *Hệ thống Agentic RAG tương tác giọng nói dành cho Di Sản Văn Hóa Việt Nam.*

![Status](https://img.shields.io/badge/Status-Active_Development-green?style=flat-square)
![Version](https://img.shields.io/badge/Version-2.0.0-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)
![Architecture](https://img.shields.io/badge/Architecture-Clean_Agentic_RAG-orange?style=flat-square)

## 📖 Tổng Quan (Overview)

**Sen AI** là một AI Agent chuyên biệt được thiết kế để cung cấp thông tin sâu sắc, chính xác và hấp dẫn về lịch sử và văn hóa Việt Nam. Khác với các mô hình ngôn ngữ chung (LLM) dễ bị "ảo giác" (hallucination), Sen AI sử dụng phương pháp **Strict RAG (Retrieval-Augmented Generation)** kết hợp với **Công cụ Thời gian thực (Real-time Tools)**. Điều này đảm bảo thông tin luôn chính xác trong khi vẫn duy trì cuộc trò chuyện tự nhiên, đậm chất nhân vật.

### 🌟 Tính Năng Nổi Bật

- **🎙️ Tương Tác Giọng Nói (Voice-to-Voice):** Giao tiếp bằng lời nói mượt mà sử dụng OpenAI Whisper (STT) và EdgeTTS/GoogleTTS (TTS).
- **🧠 Luồng Xử Lý Thông Minh (Agentic Workflow):** Bộ điều phối (Planner) thông minh sẽ tự động chuyển đổi giữa các chế độ:
    - **Chế Độ Di Sản (Heritage Mode):** Tra cứu sâu từ Vector DB (RAG) cho các câu hỏi lịch sử.
    - **Chế Độ Thời Gian Thực (Realtime Mode):** Lấy dữ liệu sống (thời tiết, giá vé, giờ mở cửa).
    - **Chế Độ Trò Chuyện (Chitchat Mode):** Giao tiếp xã giao, giữ vững tính cách nhân vật (Persona).
- **📚 Tìm Kiếm Lai & Xếp Hạng Lại (Hybrid Search & Reranking):** Kết hợp Tìm kiếm Ngữ nghĩa (Vector Search) với Tăng cường Từ khóa (Keyword Boosting) và Cross-Encoder Reranking để đạt độ chính xác cao nhất.
- **🛡️ Bộ Kiểm Chứng (Strict Verifier):** Lớp bảo vệ AI giúp đối chiếu câu trả lời với ngữ cảnh gốc để ngăn chặn thông tin sai lệch.
- **⚡ Hiệu Suất Cao:** Chiến lược Caching Redis và kiến trúc tối ưu hóa cho độ trễ thấp.

---

## 🏗️ Kiến Trúc Hệ Thống & Khả Năng Mở Rộng

Dự án tuân theo **Kiến Trúc Modular Service-Repository**, được thiết kế đặc biệt để tách biệt **Core AI (Trí tuệ)** khỏi **Luồng Game (Điều phối)**.

### Tại sao lại chọn kiến trúc này?
Thiết kế này đảm bảo rằng **các nâng cấp trong tương lai sẽ KHÔNG làm hỏng Game**.
- **Tình huống:** Bạn muốn nâng cấp từ Vector Search sang **Knowledge Graph**.
- **Giải pháp:** Bạn chỉ cần viết lại file `app/services/knowledge.py`. Client Game và các API Endpoint (`main.py`) vẫn giữ nguyên 100%.
- **Tình huống:** Bạn muốn triển khai suy luận phức tạp bằng **LangGraph**.
- **Giải pháp:** Bạn cập nhật `app/services/workflow.py`. Phần "Bộ não" (Knowledge Base) và "Miệng" (TTS) không bị ảnh hưởng.

```mermaid
graph TD
    Client[Game Client / Frontend] <-->|JSON REST API| Main[main.py (Lớp API)]
    
    subgraph "Core Ứng Dụng (Ổn định)"
        Main <--> Workflow[app.services.workflow]
    end
    
    subgraph "Năng Lực AI (Có thể cắm thêm)"
        Workflow -->|Lấy Thông Tin| Knowledge[app.services.knowledge]
        Workflow -->|Kiểm Tra An Toàn| Verifier[app.services.verifier]
        Workflow -->|Dữ Liệu Thời Gian Thực| Tools[app.services.tools]
    end
    
    subgraph "Lớp Dữ Liệu (Có thể thay thế)"
        Knowledge <-->|Vector Search| MongoDB[(MongoDB Atlas)]
        Knowledge -.->|Nâng Cấp Tương Lai| KnowledgeGraph[(Neo4j / GraphDB)]
    end
```

### Chi Tiết Các Thành Phần Cốt Lõi

1.  **Bộ Điều Phối Workflow (`app.services.workflow`)**: 
    - *Vai trò:* "Nhạc trưởng". Nó quyết định *làm gì* dựa trên đầu vào của người dùng (Di sản vs. Thời gian thực vs. Trò chuyện).
    - *Độ ổn định:* Cao. Thay đổi ở đây chỉ ảnh hưởng đến *luồng hội thoại*, không ảnh hưởng đến việc lấy dữ liệu.
    
2.  **Cơ Sở Tri Thức (`app.services.knowledge`)**: 
    - *Vai trò:* "Bộ não". Nó xử lý *cách* lấy thông tin. Hiện tại đang sử dụng **Vector Search**. 
    - *Khả năng mở rộng:* **Đây là lớp trừu tượng của bạn.** Để triển khai Knowledge Graph, bạn chỉ cần tạo một phương thức mới ở đây. Phần còn lại của ứng dụng chỉ gọi `brain.search()`, không quan tâm đến công nghệ bên dưới là gì.

3.  **Trình Điều Khiển Vector DB (`app.core.vector_db`)**: 
    - *Vai trò:* "Tài xế". Kết nối cấp thấp đến MongoDB. 

---

## 📁 Cấu Trúc Dự Án & Trách Nhiệm File

Hiểu rõ `ai làm gì` giúp việc bảo trì dễ dàng hơn:

```bash
sen-ai/
├── app/                        
│   ├── core/                   # 🧱 LỚP HẠ TẦNG (INFRASTRUCTURE)
│   │   ├── vector_db.py        # Database Driver. Xử lý kết nối & truy vấn MongoDB.
│   │   ├── config_loader.py    # Load 'monuments.json'. Thêm địa điểm mới? Kiểm tra file này.
│   │   ├── config_prompts.py   # Load system prompts. Đổi tính cách AI? Kiểm tra file này.
│   │   └── __init__.py
│   │
│   ├── services/               # 🧠 LỚP TRÍ TUỆ (INTELLIGENCE)
│   │   ├── workflow.py         # "Vòng lặp chính". Quyết định Intent -> RAG -> Phản hồi.
│   │   ├── knowledge.py        # Động cơ Tìm kiếm. Logic Hybrid Search nằm ở đây.
│   │   ├── tools.py            # API bên ngoài (Thời tiết, Giá vé).
│   │   ├── verifier.py         # Bộ lọc an toàn. Kiểm tra ảo giác (hallucinations).
│   │   ├── emotion.py          # Phân tích cảm xúc cho biểu cảm Avatar 3D.
│   │   └── __init__.py
│   │
│   ├── utils/                  # 🛠️ CÔNG CỤ TIỆN ÍCH
│   │   ├── cache.py            # Helper cho Redis.
│   │   ├── cleaner.py          # Dọn dẹp file tạm.
│   │   └── __init__.py
│   └── __init__.py
│
├── data/                       # 📂 TÀI SẢN DỮ LIỆU
│   ├── documents/              # Đặt file .md, .pdf, .docx của bạn vào đây để Ingest.
│   ├── monuments.json          # DATABASE REGISTRY. Định nghĩa Metadata địa điểm ở đây.
│   └── prompts.json            # SYSTEM PROMPTS. Chỉnh sửa tính cách AI ở đây.
│
├── scripts/                    # ⚙️ VẬN HÀNH
│   └── ingest.py               # CHẠY FILE NÀY để cập nhật database khi bạn thêm file mới.
│
├── main.py                     # 🚦 CỔNG API. Định nghĩa endpoints (/chat, /chat-audio).
├── Dockerfile                  # Cấu hình Triển khai Production.
├── docker-compose.yml          # Khởi chạy 1 chạm (App + Redis).
└── requirements.txt            # Thư viện Python phụ thuộc.
```

---

## 🚀 Bắt Đầu Nhanh (Quick Start)

### Yêu Cầu Tiền Quyết
- **Python 3.10+**
- **MongoDB Atlas** (Cluster M0+ đã bật Vector Search)
- **Redis** (Local hoặc Cloud)
- **OpenAI API Key**

### 1. Cài Đặt

```bash
# Clone repository
git clone <repository_url>
cd sen-ai

# Tạo môi trường ảo (Virtual Environment)
python -m venv .venv

# Kích hoạt (Windows)
.venv\Scripts\activate

# Kích hoạt (Linux/Mac)
source .venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt
```

### 2. Cấu Hình

Tạo file `.env` ở thư mục gốc:

```ini
MONGODB_URI=mongodb+srv://<user>:<password>@cluster...
OPENAI_API_KEY=sk-...
REDIS_URL=redis://localhost:6379
BOT_NAME=Sen
ENABLE_VERIFIER=true
DOCUMENTS_SRC_DIR=./data/documents
```

### 3. Nạp Dữ Liệu (Data Ingestion)

Nạp các tài liệu kiến thức (Markdown, PDF, DOCX):

```bash
# Đặt file vào data/documents/
# Chạy script ingest
python ingest.py
```

### 4. Chạy Server

```bash
# Khởi chạy FastAPI server
python -m uvicorn main:app --port 8000 --reload
```

---

## 📚 Tài Liệu API

### Chat Endpoint
**POST** `/chat`
```json
{
  "user_input": "Hoàng Thành Thăng Long có gì đặc biệt?",
  "history": []
}
```

### Real-time Streaming
**POST** `/chat/stream`
*Trả về Server-Sent Events (SSE) để hiển thị trạng thái đang suy nghĩ và sinh câu trả lời theo thời gian thực.*

### Tương Tác Giọng Nói
**POST** `/chat-audio`
*Nhận `multipart/form-data` chứa file âm thanh. Trả về phản hồi dạng âm thanh.*

---

## 🛠️ Bảo Trì & Vận Hành

- **Xóa Cache:**
  ```bash
  python -m app.utils.cache
  ```
  *(Hoặc gọi POST `/cache/clear`)*

- **Giám sát Hiệu suất:**
  Kiểm tra logs xem các tag `[HERITAGE RAG]`, `[REALTIME]`, và thời gian thực thi.

---

## 🤝 Đóng Góp (Contribution)

Chúng tôi hoan nghênh mọi đóng góp! Vui lòng tuân theo quy trình Pull Request chuẩn.
1. Fork dự án
2. Tạo Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`)
4. Push lên Branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📄 Giấy Phép (License)

Được phân phối dưới giấy phép MIT License. Xem `LICENSE` để biết thêm chi tiết.
