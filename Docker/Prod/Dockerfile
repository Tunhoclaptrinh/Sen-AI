FROM python:3.11-slim

WORKDIR /app

# Cài đặt các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container
COPY . .

# Mở cổng 10000 cho Render
EXPOSE 10000

# Lệnh khởi chạy: Giảm timeout xuống 120 vì OpenAI khởi động rất nhanh
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "final_app:app", "--bind", "0.0.0.0:10000", "--timeout", "300"]