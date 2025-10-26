#!/bin/bash

# =============================================================================
# Docker 快速更新腳本
# 簡化版本，用於快速重新部署程式碼
# =============================================================================

echo "🚀 Docker 快速更新中..."

# 進入 docker 目錄
cd docker

# 停止並重新構建
echo "📦 重新構建容器..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 10

# 檢查狀態
echo "✅ 檢查服務狀態..."
if docker ps | grep -q "smart_taxi_service"; then
    echo "🎉 更新完成！服務運行在 http://localhost:8080"
else
    echo "❌ 服務啟動失敗，請檢查日誌: docker logs smart_taxi_service"
fi
