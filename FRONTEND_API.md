# 前端管理介面 API 文檔

此文檔列出所有可供前端 Web 管理介面使用的 API 端點。

**基礎 URL**: `http://localhost:8080/api/v1/admin`

---

## API 端點總覽

### 連接與設備管理
- `GET /connections` - 獲取當前連接狀態
- `GET /devices` - 獲取所有設備列表
- `GET /devices/:id` - 獲取設備詳情

### 廣告管理
- `GET /advertisements` - 獲取廣告列表
- `GET /advertisements/:id` - 獲取廣告詳情

### 活動管理
- `GET /campaigns` - 獲取活動列表
- `GET /campaigns/:id` - 獲取活動詳情

### 推送控制
- `POST /override` - 管理員推送命令

### 統計數據
- `GET /stats/overview` - 獲取統計總覽

---

## 詳細 API 說明

### 1. 獲取當前連接狀態

```
GET /api/v1/admin/connections
```

**用途**: 儀表板、設備監控頁面

**響應示例**:
```json
{
  "status": "success",
  "stats": {
    "total_connections": 12,
    "active_devices": 5,
    "messages_sent": 45,
    "location_updates": 30
  },
  "active_devices": [
    {
      "device_id": "taxi-AAB-1234-rooftop",
      "sid": "abc123...",
      "connected_at": "2025-10-17T10:00:00",
      "last_activity": "2025-10-17T10:30:00"
    }
  ]
}
```

---

### 2. 獲取所有設備列表

```
GET /api/v1/admin/devices
```

**查詢參數**:
- `status` (可選): 過濾狀態 (active/inactive)
- `type` (可選): 過濾設備類型

**用途**: 設備管理頁面、設備選擇器

**請求示例**:
```
GET /api/v1/admin/devices?status=active
```

**響應示例**:
```json
{
  "status": "success",
  "total": 3,
  "devices": [
    {
      "device_id": "taxi-AAB-1234-rooftop",
      "device_type": "rooftop_display",
      "last_location": {
        "type": "Point",
        "coordinates": [121.5645, 25.0330]
      },
      "groups": ["general", "tourists"],
      "is_online": true
    }
  ]
}
```

---

### 3. 獲取設備詳情

```
GET /api/v1/admin/devices/:device_id
```

**用途**: 設備詳情頁面

**請求示例**:
```
GET /api/v1/admin/devices/taxi-AAB-1234-rooftop
```

**響應示例**:
```json
{
  "status": "success",
  "device": {
    "device_id": "taxi-AAB-1234-rooftop",
    "device_type": "rooftop_display",
    "last_location": {
      "type": "Point",
      "coordinates": [121.5645, 25.0330]
    },
    "groups": ["general", "tourists"],
    "is_online": true,
    "connection_info": {
      "device_id": "taxi-AAB-1234-rooftop",
      "connected_at": "2025-10-17T10:00:00",
      "last_activity": "2025-10-17T10:30:00"
    }
  }
}
```

---

### 4. 獲取廣告列表

```
GET /api/v1/admin/advertisements
```

**查詢參數**:
- `status` (可選): 過濾狀態 (active/inactive)
- `type` (可選): 過濾類型 (tourism/promotional/etc)

**用途**: 廣告管理頁面、廣告選擇器

**請求示例**:
```
GET /api/v1/admin/advertisements?status=active
```

**響應示例**:
```json
{
  "status": "success",
  "total": 4,
  "advertisements": [
    {
      "advertisement_id": "adv-001",
      "name": "台北 101 觀光廣告",
      "type": "tourism",
      "video_filename": "taipei101_tour_30s.mp4",
      "duration_seconds": 30,
      "target_groups": ["tourists"],
      "priority": 8,
      "status": "active"
    }
  ]
}
```

---

### 5. 獲取廣告詳情

```
GET /api/v1/admin/advertisements/:ad_id
```

**用途**: 廣告詳情頁面、廣告預覽

**請求示例**:
```
GET /api/v1/admin/advertisements/adv-001
```

**響應示例**:
```json
{
  "status": "success",
  "advertisement": {
    "advertisement_id": "adv-001",
    "name": "台北 101 觀光廣告",
    "type": "tourism",
    "video_filename": "taipei101_tour_30s.mp4",
    "duration_seconds": 30,
    "target_groups": ["tourists"],
    "priority": 8,
    "status": "active"
  }
}
```

---

### 6. 獲取活動列表

```
GET /api/v1/admin/campaigns
```

**查詢參數**:
- `status` (可選): 過濾狀態 (active/inactive)

**用途**: 活動管理頁面

**請求示例**:
```
GET /api/v1/admin/campaigns?status=active
```

**響應示例**:
```json
{
  "status": "success",
  "total": 4,
  "campaigns": [
    {
      "campaign_id": "camp-001",
      "name": "信義區商圈推廣",
      "advertisement_id": "adv-001",
      "advertisement_name": "台北 101 觀光廣告",
      "advertisement_video": "taipei101_tour_30s.mp4",
      "priority": 8,
      "target_groups": ["tourists"],
      "geo_fence": {
        "type": "Polygon",
        "coordinates": [[[121.56, 25.03], [121.57, 25.03], ...]]
      },
      "status": "active"
    }
  ]
}
```

---

### 7. 獲取活動詳情

```
GET /api/v1/admin/campaigns/:campaign_id
```

**用途**: 活動詳情頁面、活動編輯表單

**請求示例**:
```
GET /api/v1/admin/campaigns/camp-001
```

**響應示例**:
```json
{
  "status": "success",
  "campaign": {
    "campaign_id": "camp-001",
    "name": "信義區商圈推廣",
    "advertisement_id": "adv-001",
    "advertisement": {
      "advertisement_id": "adv-001",
      "name": "台北 101 觀光廣告",
      "video_filename": "taipei101_tour_30s.mp4"
    },
    "priority": 8,
    "target_groups": ["tourists"],
    "geo_fence": {
      "type": "Polygon",
      "coordinates": [[[121.56, 25.03], ...]]}
    },
    "status": "active"
  }
}
```

---

### 8. 管理員推送命令

```
POST /api/v1/admin/override
```

**用途**: 即時推送頁面

**請求 Body**:
```json
{
  "target_device_ids": ["taxi-AAB-1234-rooftop", "taxi-BBB-5678-rooftop"],
  "advertisement_id": "adv-002"
}
```

**響應示例**:
```json
{
  "status": "success",
  "advertisement": {
    "id": "adv-002",
    "name": "西門町購物廣告",
    "video_filename": "shopping_promo_20s.mp4",
    "type": "promotional"
  },
  "results": {
    "sent": ["taxi-AAB-1234-rooftop"],
    "offline": ["taxi-BBB-5678-rooftop"]
  },
  "summary": {
    "total_targets": 2,
    "sent_count": 1,
    "offline_count": 1
  },
  "timestamp": "2025-10-17T14:30:00"
}
```

---

### 9. 獲取統計總覽

```
GET /api/v1/admin/stats/overview
```

**用途**: 儀表板統計卡片

**響應示例**:
```json
{
  "status": "success",
  "stats": {
    "devices": {
      "total": 5,
      "online": 3,
      "offline": 2
    },
    "advertisements": {
      "total": 10,
      "active": 8,
      "inactive": 2
    },
    "campaigns": {
      "total": 6,
      "active": 5,
      "inactive": 1
    },
    "connections": {
      "total_connections": 12,
      "active_devices": 3,
      "messages_sent": 45,
      "location_updates": 30
    }
  }
}
```

---

## 前端使用示例

### JavaScript/TypeScript 封裝

```typescript
// lib/api.ts
const API_BASE = 'http://localhost:8080/api/v1/admin';

// 獲取連接狀態
export async function getConnections() {
  const res = await fetch(`${API_BASE}/connections`);
  return res.json();
}

// 獲取設備列表
export async function getDevices(status?: string) {
  const url = status 
    ? `${API_BASE}/devices?status=${status}`
    : `${API_BASE}/devices`;
  const res = await fetch(url);
  return res.json();
}

// 獲取廣告列表
export async function getAdvertisements(status?: string) {
  const url = status 
    ? `${API_BASE}/advertisements?status=${status}`
    : `${API_BASE}/advertisements`;
  const res = await fetch(url);
  return res.json();
}

// 執行推送
export async function pushAd(deviceIds: string[], adId: string) {
  const res = await fetch(`${API_BASE}/override`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_device_ids: deviceIds,
      advertisement_id: adId
    })
  });
  return res.json();
}

// 獲取統計數據
export async function getStats() {
  const res = await fetch(`${API_BASE}/stats/overview`);
  return res.json();
}
```

### React 使用示例

```typescript
import { useEffect, useState } from 'react';
import { getConnections, pushAd } from '@/lib/api';

function Dashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    // 獲取連接狀態
    async function fetchData() {
      const data = await getConnections();
      setStats(data.stats);
    }
    
    fetchData();
    
    // 每 5 秒自動刷新
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h1>儀表板</h1>
      {stats && (
        <div>
          <p>在線設備: {stats.active_devices}</p>
          <p>總連接數: {stats.total_connections}</p>
        </div>
      )}
    </div>
  );
}
```

---

## 錯誤處理

所有 API 在發生錯誤時會返回以下格式：

```json
{
  "status": "error",
  "message": "錯誤描述"
}
```

**常見 HTTP 狀態碼**:
- `200` - 成功
- `400` - 請求參數錯誤
- `404` - 資源不存在
- `500` - 服務器內部錯誤

---

## CORS 支持

後端已啟用 CORS，前端可以直接從任何域名訪問這些 API。

---

## 測試 API

使用 curl 測試：

```bash
# 測試連接狀態
curl http://localhost:8080/api/v1/admin/connections

# 測試設備列表
curl http://localhost:8080/api/v1/admin/devices

# 測試廣告列表
curl http://localhost:8080/api/v1/admin/advertisements

# 測試推送
curl -X POST http://localhost:8080/api/v1/admin/override \
  -H "Content-Type: application/json" \
  -d '{
    "target_device_ids": ["taxi-AAB-1234-rooftop"],
    "advertisement_id": "adv-001"
  }'

# 測試統計數據
curl http://localhost:8080/api/v1/admin/stats/overview
```

