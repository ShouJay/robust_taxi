"""
智能計程車廣告服務 - 實時推送服務
使用 Flask + Flask-SocketIO + MongoDB 實現廣告主動推送功能

安裝依賴：
pip install flask flask-socketio pymongo python-socketio

運行應用程序：
1. 確保 MongoDB 正在運行
2. 運行：python app_push_service.py
3. 首次運行時，訪問 http://localhost:5001/init_db 來初始化示例數據
4. 設備客戶端通過 WebSocket 連接到 ws://localhost:5001
5. 管理員通過 POST /api/v1/admin/override 推送命令

測試範例：

1. 使用 Python 測試客戶端連接：
   python test_websocket_client.py

2. 使用 curl 測試管理員推送：
   curl -X POST http://localhost:5001/api/v1/admin/override \
     -H "Content-Type: application/json" \
     -d '{
       "target_device_ids": ["taxi-AAB-1234-rooftop"],
       "advertisement_id": "adv-002"
     }'
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import logging
from datetime import datetime

# ============================================================================
# 應用程序配置
# ============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
CORS(app)

# 初始化 SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",  # 生產環境應限制來源
    async_mode='threading'
)

# MongoDB 配置
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "smart_taxi_ads_push"

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 數據庫連接
# ============================================================================

try:
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    # 獲取集合
    devices_collection = db["devices"]
    advertisements_collection = db["advertisements"]
    
    logger.info(f"成功連接到 MongoDB 數據庫: {DATABASE_NAME}")
except Exception as e:
    logger.error(f"MongoDB 連接失敗: {e}")
    raise

# ============================================================================
# 連接管理 - 內存映射
# ============================================================================

# 映射: session_id (sid) -> device_id
active_connections = {}

# 映射: device_id -> session_id (sid) - 用於快速查找
device_to_sid = {}

# 連接統計
connection_stats = {
    "total_connections": 0,
    "active_devices": 0,
    "messages_sent": 0
}


def get_active_devices():
    """獲取所有活動設備列表"""
    return list(device_to_sid.keys())


def get_device_sid(device_id):
    """根據設備 ID 獲取 session ID"""
    return device_to_sid.get(device_id)


def register_device(sid, device_id):
    """註冊設備連接"""
    # 如果設備已經有連接，先移除舊連接
    if device_id in device_to_sid:
        old_sid = device_to_sid[device_id]
        if old_sid in active_connections:
            del active_connections[old_sid]
            logger.warning(f"設備 {device_id} 的舊連接 {old_sid} 已被替換")
    
    # 註冊新連接
    active_connections[sid] = {
        'device_id': device_id,
        'connected_at': datetime.now().isoformat(),
        'last_activity': datetime.now().isoformat()
    }
    device_to_sid[device_id] = sid
    connection_stats['active_devices'] = len(device_to_sid)
    
    logger.info(f"設備已註冊: {device_id} (SID: {sid})")


def unregister_device(sid):
    """取消註冊設備連接"""
    if sid in active_connections:
        device_id = active_connections[sid]['device_id']
        del active_connections[sid]
        
        if device_id in device_to_sid:
            del device_to_sid[device_id]
        
        connection_stats['active_devices'] = len(device_to_sid)
        logger.info(f"設備已斷開: {device_id} (SID: {sid})")
        return device_id
    return None


# ============================================================================
# 數據庫初始化函數
# ============================================================================

def insert_sample_data():
    """
    插入示例數據
    
    包含：
    - 設備數據（計程車和固定廣告屏）
    - 廣告數據（包含緊急廣告）
    """
    try:
        # 清空現有數據
        devices_collection.delete_many({})
        advertisements_collection.delete_many({})
        logger.info("已清空所有集合")
        
        # 插入設備數據
        devices_data = [
            {
                "_id": "taxi-AAB-1234-rooftop",
                "device_type": "rooftop",
                "description": "計程車車頂廣告屏"
            },
            {
                "_id": "taxi-XYZ-5678-rooftop",
                "device_type": "rooftop",
                "description": "計程車車頂廣告屏"
            },
            {
                "_id": "fixed-ximen-joytime-01",
                "device_type": "fixed-outdoor",
                "description": "西門町 Joytime 固定廣告屏"
            },
            {
                "_id": "fixed-taipei101-01",
                "device_type": "fixed-outdoor",
                "description": "台北101 固定廣告屏"
            },
            {
                "_id": "taxi-DEF-9999-rooftop",
                "device_type": "rooftop",
                "description": "高端車隊計程車"
            }
        ]
        devices_collection.insert_many(devices_data)
        logger.info(f"已插入 {len(devices_data)} 個設備")
        
        # 插入廣告數據
        advertisements_data = [
            {
                "_id": "adv-001",
                "name": "一般促銷廣告",
                "video_filename": "normal_promo_30s.mp4",
                "type": "normal"
            },
            {
                "_id": "adv-002",
                "name": "緊急限時搶購廣告",
                "video_filename": "flash_sale_10s.mp4",
                "type": "urgent"
            },
            {
                "_id": "adv-003",
                "name": "重大新聞快訊",
                "video_filename": "breaking_news_15s.mp4",
                "type": "urgent"
            },
            {
                "_id": "adv-004",
                "name": "政府緊急公告",
                "video_filename": "emergency_announcement_20s.mp4",
                "type": "emergency"
            },
            {
                "_id": "adv-005",
                "name": "促銷活動",
                "video_filename": "promotion_25s.mp4",
                "type": "normal"
            }
        ]
        advertisements_collection.insert_many(advertisements_data)
        logger.info(f"已插入 {len(advertisements_data)} 個廣告")
        
        return True
        
    except Exception as e:
        logger.error(f"插入示例數據時出錯: {e}")
        return False


# ============================================================================
# WebSocket 事件處理
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """
    處理客戶端連接事件
    
    當客戶端建立 WebSocket 連接時觸發
    """
    sid = request.sid
    connection_stats['total_connections'] += 1
    
    logger.info(f"新的 WebSocket 連接: SID={sid}")
    
    # 發送歡迎消息
    emit('connection_established', {
        'message': '連接成功！請發送 register 事件註冊您的設備',
        'sid': sid,
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('register')
def handle_register(data):
    """
    處理設備註冊事件
    
    客戶端必須在連接後立即發送此事件來註冊設備 ID
    
    Expected data: { "device_id": "taxi-AAB-1234-rooftop" }
    """
    sid = request.sid
    
    try:
        device_id = data.get('device_id')
        
        if not device_id:
            emit('registration_error', {
                'error': '缺少 device_id 參數'
            })
            logger.warning(f"註冊失敗: 缺少 device_id (SID: {sid})")
            return
        
        # 驗證設備是否存在於數據庫
        device = devices_collection.find_one({"_id": device_id})
        
        if not device:
            emit('registration_error', {
                'error': f'設備 {device_id} 不存在於系統中'
            })
            logger.warning(f"註冊失敗: 設備不存在 {device_id} (SID: {sid})")
            return
        
        # 註冊設備
        register_device(sid, device_id)
        
        # 發送註冊成功確認
        emit('registration_success', {
            'message': f'設備 {device_id} 註冊成功',
            'device_id': device_id,
            'device_type': device.get('device_type'),
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"設備註冊成功: {device_id} (SID: {sid})")
        
    except Exception as e:
        logger.error(f"處理註冊事件時出錯: {e}")
        emit('registration_error', {
            'error': '內部伺服器錯誤'
        })


@socketio.on('disconnect')
def handle_disconnect():
    """
    處理客戶端斷開連接事件
    
    當客戶端斷開 WebSocket 連接時觸發
    清理連接映射，防止向已斷開的客戶端發送消息
    """
    sid = request.sid
    device_id = unregister_device(sid)
    
    if device_id:
        logger.info(f"設備斷開連接: {device_id} (SID: {sid})")
    else:
        logger.info(f"未註冊的連接斷開: SID={sid}")


@socketio.on('heartbeat')
def handle_heartbeat(data):
    """
    處理設備心跳事件（可選）
    
    設備可以定期發送心跳來保持連接活躍
    """
    sid = request.sid
    
    if sid in active_connections:
        active_connections[sid]['last_activity'] = datetime.now().isoformat()
        device_id = active_connections[sid]['device_id']
        
        emit('heartbeat_ack', {
            'device_id': device_id,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.debug(f"收到心跳: {device_id}")
    else:
        emit('error', {
            'error': '設備未註冊，請先發送 register 事件'
        })


# ============================================================================
# HTTP API 端點
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    """根路徑 - 提供服務信息"""
    return jsonify({
        "service": "智能計程車廣告服務 - 實時推送服務",
        "version": "1.0.0",
        "websocket_url": "ws://localhost:5001",
        "endpoints": {
            "init_db": "GET /init_db",
            "admin_override": "POST /api/v1/admin/override",
            "connection_status": "GET /api/v1/admin/connections",
            "health": "GET /health"
        },
        "websocket_events": {
            "client_to_server": ["register", "heartbeat"],
            "server_to_client": ["connection_established", "registration_success", "play_override", "heartbeat_ack"]
        }
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    try:
        client.admin.command('ping')
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "active_connections": connection_stats['active_devices'],
            "total_connections": connection_stats['total_connections']
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 503


@app.route('/init_db', methods=['GET'])
def init_database():
    """初始化數據庫端點"""
    try:
        success = insert_sample_data()
        
        if success:
            return jsonify({
                "status": "success",
                "message": "數據庫初始化成功",
                "details": {
                    "devices": "已插入 5 個設備",
                    "advertisements": "已插入 5 個廣告"
                }
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "數據庫初始化失敗"
            }), 500
            
    except Exception as e:
        logger.error(f"初始化數據庫時出錯: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/v1/admin/connections', methods=['GET'])
def get_connections():
    """
    獲取當前連接狀態
    
    管理員可以查看當前所有活動連接
    """
    active_devices = []
    
    for sid, conn_info in active_connections.items():
        active_devices.append({
            'device_id': conn_info['device_id'],
            'sid': sid,
            'connected_at': conn_info['connected_at'],
            'last_activity': conn_info['last_activity']
        })
    
    return jsonify({
        "status": "success",
        "stats": connection_stats,
        "active_devices": active_devices
    }), 200


@app.route('/api/v1/admin/override', methods=['POST'])
def admin_override():
    """
    管理員推送覆蓋命令端點
    
    允許管理員向特定設備推送緊急廣告覆蓋命令
    
    Request Body:
    {
        "target_device_ids": ["taxi-AAB-1234-rooftop", "fixed-ximen-joytime-01"],
        "advertisement_id": "adv-002"
    }
    
    Response:
    {
        "status": "success",
        "advertisement": {
            "id": "adv-002",
            "name": "緊急限時搶購廣告",
            "video_filename": "flash_sale_10s.mp4"
        },
        "results": {
            "sent": ["taxi-AAB-1234-rooftop"],
            "offline": ["fixed-ximen-joytime-01"]
        }
    }
    """
    try:
        # 1. 解析請求數據
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "請求體不能為空"
            }), 400
        
        target_device_ids = data.get('target_device_ids', [])
        advertisement_id = data.get('advertisement_id')
        
        # 驗證必要欄位
        if not target_device_ids or not advertisement_id:
            return jsonify({
                "status": "error",
                "message": "缺少必要欄位: target_device_ids 和 advertisement_id"
            }), 400
        
        if not isinstance(target_device_ids, list):
            return jsonify({
                "status": "error",
                "message": "target_device_ids 必須是陣列"
            }), 400
        
        logger.info(f"收到管理員推送請求 - 目標設備: {target_device_ids}, 廣告: {advertisement_id}")
        
        # 2. 查找廣告信息
        advertisement = advertisements_collection.find_one({"_id": advertisement_id})
        
        if not advertisement:
            return jsonify({
                "status": "error",
                "message": f"找不到廣告: {advertisement_id}"
            }), 404
        
        video_filename = advertisement.get('video_filename')
        
        if not video_filename:
            return jsonify({
                "status": "error",
                "message": "廣告缺少 video_filename 欄位"
            }), 500
        
        # 3. 構建推送載荷
        payload = {
            "command": "PLAY_VIDEO",
            "video_filename": video_filename,
            "advertisement_id": advertisement_id,
            "advertisement_name": advertisement.get('name', ''),
            "priority": "override",
            "timestamp": datetime.now().isoformat()
        }
        
        # 4. 向每個目標設備推送命令
        sent_to = []
        offline_devices = []
        
        for device_id in target_device_ids:
            sid = get_device_sid(device_id)
            
            if sid:
                try:
                    # 發送覆蓋命令到特定客戶端
                    socketio.emit(
                        'play_override',
                        payload,
                        room=sid
                    )
                    sent_to.append(device_id)
                    connection_stats['messages_sent'] += 1
                    logger.info(f"推送命令已發送到: {device_id} (SID: {sid})")
                except Exception as e:
                    logger.error(f"發送到 {device_id} 時出錯: {e}")
                    offline_devices.append(device_id)
            else:
                offline_devices.append(device_id)
                logger.warning(f"設備離線或未連接: {device_id}")
        
        # 5. 構建並返回響應
        response = {
            "status": "success",
            "advertisement": {
                "id": advertisement_id,
                "name": advertisement.get('name', ''),
                "video_filename": video_filename,
                "type": advertisement.get('type', '')
            },
            "results": {
                "sent": sent_to,
                "offline": offline_devices
            },
            "summary": {
                "total_targets": len(target_device_ids),
                "sent_count": len(sent_to),
                "offline_count": len(offline_devices)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"處理管理員推送請求時出錯: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "內部伺服器錯誤",
            "detail": str(e)
        }), 500


# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == '__main__':
    logger.info("啟動 Flask-SocketIO 推送服務...")
    logger.info("WebSocket 端點: ws://localhost:5001")
    logger.info("HTTP 端點: http://localhost:5001")
    logger.info("請先訪問 http://localhost:5001/init_db 來初始化數據庫")
    
    # 運行應用程序（使用 SocketIO 的 run 方法）
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=True,
        allow_unsafe_werkzeug=True  # 僅用於開發環境
    )

