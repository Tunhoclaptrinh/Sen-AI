# 1. Sử dụng Python 3.11 bản nhẹ (slim) - Đúng với bản bạn đang dùng ở VS Code
FROM python:3.11-slim

# 2. Thiết lập các biến môi trường để tối ưu bộ nhớ
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Buộc SentenceTransformers lưu model vào thư mục cụ thể
ENV HF_HOME=/app/model_cache

WORKDIR /app

# 3. Cài đặt các gói hệ thống cần thiết (rất nhẹ, chỉ để hỗ trợ build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Sao chép và cài đặt thư viện
COPY requirements.txt .

# BƯỚC QUAN TRỌNG NHẤT: Cài Torch bản CPU-only (Chỉ ~150MB thay vì 2GB)
# Việc này giúp tiết kiệm khoảng 300MB RAM lúc vận hành
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# 5. [PRE-DOWNLOAD] Tải sẵn model 384 chiều ngay lúc build image
# Giúp server khởi động nhanh hơn và không bị lỗi Timeout trên Render
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# 6. Sao chép toàn bộ code vào Docker
COPY . .

# 7. Thông báo cổng (Render mặc định dùng 10000)
EXPOSE 10000

# 8. Lệnh khởi chạy: 1 Worker để dành trọn RAM cho Model
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "final_app:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]