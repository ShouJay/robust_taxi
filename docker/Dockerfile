FROM python:3.11-slim

WORKDIR /app

# 複製依賴文件
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製源代碼
COPY src/ ./src/

# 暴露端口
EXPOSE 5000 5001

# 預設命令
CMD ["python", "src/app.py"]
