#!/bin/bash

echo "========================================"
echo "整合測試腳本"
echo "========================================"

echo ""
echo "1. 檢查服務健康狀態..."
curl -s http://localhost:8080/health | python -m json.tool

echo ""
echo "2. 測試設備心跳（HTTP 方式）..."
curl -s -X POST http://localhost:8080/api/v1/device/heartbeat \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "taxi-AAB-1234-rooftop",
    "location": {
      "longitude": 121.5645,
      "latitude": 25.0330
    }
  }' | python -m json.tool

echo ""
echo "========================================"
echo "前端管理 API 測試"
echo "========================================"

echo ""
echo "3. 獲取連接狀態..."
curl -s http://localhost:8080/api/v1/admin/connections | python -m json.tool

echo ""
echo "4. 獲取設備列表..."
curl -s http://localhost:8080/api/v1/admin/devices | python -m json.tool

echo ""
echo "5. 獲取廣告列表..."
curl -s http://localhost:8080/api/v1/admin/advertisements | python -m json.tool

echo ""
echo "6. 獲取活動列表..."
curl -s http://localhost:8080/api/v1/admin/campaigns | python -m json.tool

echo ""
echo "7. 獲取統計總覽..."
curl -s http://localhost:8080/api/v1/admin/stats/overview | python -m json.tool

echo ""
echo "8. 測試管理員推送..."
curl -s -X POST http://localhost:8080/api/v1/admin/override \
  -H "Content-Type: application/json" \
  -d '{
    "target_device_ids": ["taxi-AAB-1234-rooftop"],
    "advertisement_id": "adv-002"
  }' | python -m json.tool

echo ""
echo "========================================"
echo "測試完成"
echo "========================================"
echo ""
echo "測試項目："
echo "  [1] 服務健康檢查"
echo "  [2] 設備心跳（HTTP）"
echo "  [3] 連接狀態查詢"
echo "  [4] 設備列表查詢"
echo "  [5] 廣告列表查詢"
echo "  [6] 活動列表查詢"
echo "  [7] 統計數據查詢"
echo "  [8] 管理員推送"
echo ""

