# 🧠 SEN Heritage AI - RAG System

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-teal.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Hệ thống RAG (Retrieval-Augmented Generation) thông minh cho Game Giáo Dục Văn Hóa Việt Nam**

[Tính Năng](#-tính-năng-chính) • [Cài Đặt](#-cài-đặt--chạy) • [API Docs](#-api-documentation) • [Cấu Trúc](#-cấu-trúc-dự-án)

</div>

---

## 📋 Mục Lục

- [Giới Thiệu](#-giới-thiệu)
- [Tính Năng Chính](#-tính-năng-chính)
- [Công Nghệ](#-công-nghệ)
- [Yêu Cầu Hệ Thống](#-yêu-cầu-hệ-thống)
- [Cài Đặt & Chạy](#-cài-đặt--chạy)
- [Cấu Trúc Dự Án](#-cấu-trúc-dự-án)
- [API Documentation](#-api-documentation)
- [Biến Môi Trường](#-biến-môi-trường)

---

## 🎯 Giới Thiệu

**RAG Practice** là service AI chuyên biệt của dự án SEN, chịu trách nhiệm xử lý các câu hỏi về văn hóa, lịch sử thông qua kỹ thuật **RAG (Retrieval-Augmented Generation)**. Hệ thống kết hợp giữa tìm kiếm Vector (Semantic Search) và Từ khóa (Keyword Matching) để đưa ra câu trả lời chính xác, mang đậm văn phong của nhân vật Sen.

### 🌟 Điểm Nổi Bật

- 🧠 **Hybrid Search**: Kết hợp Vector Search (MongoDB Atlas) và Keyword Scoring để tối ưu độ chính xác.
- 🔀 **Semantic Router**: Tự động phân loại câu hỏi (Múa rối nước, Hoàng thành, Chitchat...) để chọn chiến lược trả lời phù hợp.
- ⚡ **High Performance**: Caching thông minh với Redis, phản hồi cực nhanh cho các câu hỏi trùng lặp.
- 🗣️ **Text-to-Speech**: Tự động sinh audio phản hồi (Edge TTS) cho trải nghiệm tương tác giọng nói.
- 📝 **Auto Ingestion**: Tự động đọc, chia nhỏ (chunking) và vector hóa dữ liệu từ các file Markdown văn hóa.

---

## ✨ Tính Năng Chính

### 1. 🔍 Hybrid Retrieval System
- **Vector Search**: Sử dụng model `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions) để tìm kiếm theo ngữ nghĩa.
- **Keyword Scoring**: Thuật toán chấm điểm dựa trên tần suất từ khóa xuất hiện, giúp rerank kết quả tìm kiếm.
- **Context Awareness**: Chỉ lấy Top 3 context sát nhất để gửi cho LLM.

### 2. 🤖 AI Processing Pipeline
1. **Router**: Phân tích ý định người dùng (Intent Classification).
2. **Rewrite**: Viết lại câu hỏi (xử lý lỗi chính tả, thiếu dấu, ngữ cảnh lịch sử) bằng GPT-4o-mini.
3. **Cache Check**: Kiểm tra Redis cache để trả về kết quả ngay lập tức nếu đã có.
4. **Retrieval**: Truy xuất dữ liệu từ Vector DB.
5. **Generation**: Tổng hợp câu trả lời thân thiện từ LLM dựa trên context tìm được.
6. **TTS**: Sinh file âm thanh base64.

### 3. 🛠️ Quản Trị Dữ Liệu
- Hỗ trợ nạp dữ liệu kiến thức từ file Markdown (`mua_roi_nuoc.md`, `hoang_thanh.md`).
- Tự động chia nhỏ văn bản (Chunking) theo Header và Character count.

---

## 🛠️ Công Nghệ

| Category | Technology | Purpose |
|Data Science|
| **Core** | Python 3.10+ | Ngôn ngữ lập trình chính |
| **API Framework** | FastAPI | Xây dựng RESTful API hiệu năng cao |
| **LLM Integration** | OpenAI GPT-4o-mini | Tổng hợp câu trả lời & Rewrite logic |
| **Embeddings** | Sentence-Transformers | Tạo vector embeddings (Multilingual) |
| **Database** | MongoDB Atlas | Lưu trữ Vector & Metadata |
| **Caching** | Redis | Caching câu trả lời & Session history |
| **TTS** | Edge-TTS | Chuyển đổi văn bản thành giọng nói (Free) |
| **Ingestion** | LangChain | Text Splitting & Processing |
| **Validation** | Pydantic | Data validation |

---

## 📦 Yêu Cầu Hệ Thống

Để chạy hệ thống này, bạn cần có:

- **Docker Desktop** (Khuyến nghị)
- Hoặc cài đặt thủ công:
  - Python 3.10+
  - Redis Server
  - MongoDB Atlas Account (Vector Search enabled)

---

## 🚀 Cài Đặt & Chạy

### 🐳 Cách 1: Chạy Với Docker (Khuyến Nghị)

Sử dụng script `run.sh` được tích hợp sẵn để quản lý Docker container dễ dàng.

#### Bước 1: Cấu hình môi trường
Tạo file `.env` từ `.env.example` (nếu có) hoặc tạo mới:

```bash
OPENAI_API_KEY=...
MONGODB_URI=...
REDIS_URL=...
```

#### Bước 2: Sử dụng Menu Tương Tác
Chạy lệnh sau tại thư mục gốc của `RAG-Practice-main`:

```bash
bash run.sh
```

Menu sẽ hiện ra:
```
==========================================
     RAG Practice - Docker Runner
==========================================

  Select mode:

  [1] Build Images   (First time / Rebuild)
  [2] Start Dev      (Hot-reload server)
  [3] View Logs
  [4] Stop All       (docker-compose down)
  [5] Exit
```

- Chọn **[1]** để Build lần đầu.
- Chọn **[2]** để khởi động Server.

Server sẽ chạy tại: `http://localhost:8000`

### 💻 Cách 2: Chạy Local (Thủ Công)

1. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Cấu hình .env:**
   Đảm bảo `REDIS_URL` trỏ về Redis đang chạy (ví dụ `redis://localhost:6379/0`).

3. **Chạy Server:**
   ```bash
   python serve_app.py
   ```
   Hoặc:
   ```bash
   uvicorn serve_app:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## 📁 Cấu Trúc Dự Án

```
RAG-Practice-main/
│
├── 📁 Docker/                  # Docker configurations
│   └── Dev/
│       ├── Dockerfile
│       └── docker-compose.yml
│
├── 📁 mix/                     # Dữ liệu hỗn hợp (CSV, logs...)
├── 📁 my_semantic_logic/       # Logic định tuyến ngữ nghĩa
│   ├── route.py                # Định nghĩa Route
│   ├── router.py               # Semantic Router logic
│   └── samples.py              # Các mẫu câu hỏi training
│
├── 📄 serve_app.py             # 🚀 Main Entry Point (FastAPI app)
├── 📄 vector_db.py             # MongoDB Vector Search Wrapper
├── 📄 embeddings.py            # Embedding logic (nếu tách riêng)
├── 📄 reflection.py            # AI Self-correction/Rewrite module
├── 📄 final_app.py             # (Legacy/Alternative entry point)
├── 📄 run.sh                   # Script quản lý Docker tiện lợi
├── 📄 requirements.txt         # Python dependencies
├── 📄 mua_roi_nuoc.md          # Knowledge Base: Múa Rối
└── 📄 hoang_thanh.md           # Knowledge Base: Hoàng Thành
```

---

## 📖 API Documentation

### Base URL
```
Development: http://localhost:8000
Docs UI: http://localhost:8000/docs
```

### 1. Process Query (Chat)
Endpoint chính để tương tác với AI Sen.

**Request:** `POST /process_query`

```json
{
  "user_input": "Múa rối nước ra đời khi nào?",
  "history": []
}
```

**Response:**

```json
{
  "answer": "Múa rối nước ra đời vào khoảng thế kỷ 11... (Câu trả lời từ AI)",
  "rewritten_query": "Nguồn gốc múa rối nước",
  "route": "roi_nuoc",
  "score": 0.85,
  "audio_base64": "UklGRi...",
  "context_used": "Nội dung trích xuất từ DB..."
}
```

### 2. Health Check
**Request:** `GET /`

**Response:**
```json
{
  "message": "AI Sen API is running!",
  "status": "online",
  "author": "Hieu"
}
```

---

## 🔧 Biến Môi Trường (.env)

| Biến | Mô Tả | Bắt Buộc |
|------|-------|----------|
| `OPENAI_API_KEY` | API Key của OpenAI (GPT-4o-mini) | ✅ |
| `MONGODB_URI` | Connection String tới MongoDB Atlas | ✅ |
| `REDIS_URL` | Redis URL (VD: `redis://localhost:6379/0`) | ✅ |
| `ENV` | Môi trường (`development` / `production`) | ❌ |

---

<div align="center">
  <sub>Built with ❤️ for SEN Project</sub>
</div>