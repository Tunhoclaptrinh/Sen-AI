# Sử dụng Python 3.10 slim để tối ưu dung lượng (nhẹ hơn bản full)
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Thiết lập biến môi trường
# PYTHONDONTWRITEBYTECODE: Ngăn Python tạo file .pyc (không cần trong container)
# PYTHONUNBUFFERED: Log in ra console ngay lập tức (dễ debug)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cài đặt các gói hệ thống cần thiết (nếu có thư viện cần biên dịch C/C++)
# sentence-transformers/numpy đôi khi cần gcc
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements trước để tận dụng Docker Cache layer
COPY requirements.txt .

# Cài đặt dependencies
# --no-cache-dir giúp giảm dung lượng image
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code còn lại vào container
COPY . .

# Expose port (Mặc định FastAPI chạy 8000)
EXPOSE 8000

# Lệnh chạy ứng dụng
# --host 0.0.0.0 để container nhận request từ bên ngoài
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
