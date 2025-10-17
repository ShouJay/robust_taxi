# 使用官方 Python 運行時作為父鏡像
FROM python:3.10-slim-buster

# 設置工作目錄
WORKDIR /app

# 複製依賴文件
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程序代碼
COPY src ./src
COPY tests ./tests
COPY run_app.py .

# 暴露應用程序運行端口
EXPOSE 8080

# 設置健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

# 運行應用程序
CMD ["python", "run_app.py"]
