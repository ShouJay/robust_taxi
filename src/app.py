"""
智能計程車廣告服務 - 整合版
結合廣告決策和實時推送功能

功能特點：
1. 設備定期發送位置數據
2. 服務器進行廣告決策
3. 通過 WebSocket 實時推送廣告
4. 支持管理員主動插播
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
import logging
from datetime import datetime

# 導入配置和模組
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, LOG_LEVEL, MONGODB_URI, DATABASE_NAME
from database import Database
from services import AdDecisionService
from models import HeartbeatRequest, HeartbeatResponse
from sample_data import SampleData
from admin_api import init_admin_api

# ============================================================================
# 應用程序設置
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

# 設置日誌
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 數據庫和服務初始化
# ============================================================================

try:
    # 初始化數據庫連接
    db = Database(MONGODB_URI, DATABASE_NAME)
    
    # 初始化廣告決策服務
    ad_service = AdDecisionService(db)
    
    logger.info("整合應用程序初始化完成")
except Exception as e:
    logger.error(f"應用程序初始化失敗: {e}")
    raise

# ============================================================================
# WebSocket 連接管理
# ============================================================================

# 映射: session_id (sid) -> device_id
active_connections = {}

# 映射: device_id -> session_id (sid) - 用於快速查找
device_to_sid = {}

# 連接統計
connection_stats = {
    "total_connections": 0,
    "active_devices": 0,
    "messages_sent": 0,
    "location_updates": 0
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
# WebSocket 事件處理
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """處理客戶端連接事件"""
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
    """處理設備註冊事件"""
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
        device = db.devices.find_one({"_id": device_id})
        
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


@socketio.on('location_update')
def handle_location_update(data):
    """
    處理設備位置更新事件 - 核心功能！
    
    設備發送位置數據，服務器進行廣告決策並實時推送
    """
    sid = request.sid
    
    try:
        device_id = data.get('device_id')
        longitude = data.get('longitude')
        latitude = data.get('latitude')
        
        # 驗證數據
        if not device_id or longitude is None or latitude is None:
            emit('location_error', {
                'error': '缺少必要欄位: device_id, longitude, latitude'
            })
            return
        
        # 驗證經緯度範圍
        if not (-180 <= longitude <= 180) or not (-90 <= latitude <= 90):
            emit('location_error', {
                'error': '經緯度範圍無效'
            })
            return
        
        # 檢查設備是否已註冊
        if sid not in active_connections:
            emit('location_error', {
                'error': '設備未註冊，請先發送 register 事件'
            })
            return
        
        logger.info(f"收到位置更新: {device_id} -> ({longitude}, {latitude})")
        
        # 執行廣告決策
        video_filename = ad_service.decide_ad(device_id, longitude, latitude)
        
        if video_filename:
            # 構建推送載荷
            payload = {
                "command": "PLAY_VIDEO",
                "video_filename": video_filename,
                "trigger": "location_based",  # 標記觸發原因
                "device_id": device_id,
                "location": {
                    "longitude": longitude,
                    "latitude": latitude
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # 實時推送廣告到設備
            emit('play_ad', payload)
            connection_stats['messages_sent'] += 1
            connection_stats['location_updates'] += 1
            
            logger.info(f"已推送廣告到 {device_id}: {video_filename}")
            
            # 發送確認消息
            emit('location_ack', {
                'message': '位置更新已處理，廣告已推送',
                'video_filename': video_filename,
                'timestamp': datetime.now().isoformat()
            })
        else:
            emit('location_ack', {
                'message': '位置更新已處理，無匹配廣告',
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"處理位置更新時出錯: {e}")
        emit('location_error', {
            'error': '處理位置更新時發生錯誤'
        })


@socketio.on('disconnect')
def handle_disconnect():
    """處理客戶端斷開連接事件"""
    sid = request.sid
    device_id = unregister_device(sid)
    
    if device_id:
        logger.info(f"設備斷開連接: {device_id} (SID: {sid})")
    else:
        logger.info(f"未註冊的連接斷開: SID={sid}")


@socketio.on('heartbeat')
def handle_heartbeat(data):
    """處理設備心跳事件"""
    sid = request.sid
    
    if sid in active_connections:
        active_connections[sid]['last_activity'] = datetime.now().isoformat()
        device_id = active_connections[sid]['device_id']
        
        emit('heartbeat_ack', {
            'device_id': device_id,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.debug(f"收到心跳: {device_id}")


# ============================================================================
# HTTP API 端點
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    """根路徑 - 提供服務信息"""
    return jsonify({
        "service": "智能計程車廣告服務 - 整合版",
        "version": "2.0.0",
        "features": [
            "基於位置的廣告決策",
            "WebSocket 實時推送",
            "管理員主動插播",
            "設備位置追蹤"
        ],
        "endpoints": {
            "heartbeat": "POST /api/v1/device/heartbeat (傳統 HTTP)",
            "location_update": "WebSocket event (推薦)",
            "admin_override": "POST /api/v1/admin/override",
            "init_db": "GET /init_db",
            "health": "GET /health",
            "connections": "GET /api/v1/admin/connections"
        },
        "websocket_url": "ws://localhost:8080",
        "websocket_events": {
            "client_to_server": ["register", "location_update", "heartbeat"],
            "server_to_client": ["play_ad", "location_ack", "connection_established", "registration_success"]
        }
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    try:
        is_healthy = db.health_check()
        
        if is_healthy:
            return jsonify({
                "status": "healthy",
                "database": "connected",
                "active_connections": connection_stats['active_devices'],
                "total_connections": connection_stats['total_connections'],
                "messages_sent": connection_stats['messages_sent'],
                "location_updates": connection_stats['location_updates']
            }), 200
        else:
            return jsonify({
                "status": "unhealthy",
                "database": "disconnected"
            }), 503
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
        # 創建地理空間索引
        index_success = db.create_indexes()
        
        # 獲取示例數據
        devices_data = SampleData.get_devices()
        advertisements_data = SampleData.get_advertisements()
        campaigns_data = SampleData.get_campaigns()
        
        # 插入示例數據
        data_success = db.insert_sample_data(
            devices_data,
            advertisements_data,
            campaigns_data
        )
        
        if index_success and data_success:
            return jsonify({
                "status": "success",
                "message": "數據庫初始化成功",
                "details": {
                    "indexes": "已創建 2dsphere 索引",
                    "devices": f"已插入 {len(devices_data)} 個設備",
                    "advertisements": f"已插入 {len(advertisements_data)} 個廣告",
                    "campaigns": f"已插入 {len(campaigns_data)} 個活動"
                }
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "數據庫初始化過程中出現問題"
            }), 500
            
    except Exception as e:
        logger.error(f"初始化數據庫時出錯: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/v1/device/heartbeat', methods=['POST'])
def device_heartbeat():
    """
    傳統 HTTP 心跳端點（向後兼容）
    
    建議使用 WebSocket location_update 事件
    """
    try:
        # 1. 獲取並驗證請求數據
        data = request.get_json()
        
        is_valid, error_msg, parsed_data = HeartbeatRequest.validate(data)
        
        if not is_valid:
            return jsonify(HeartbeatResponse.error(error_msg))
        
        device_id = parsed_data['device_id']
        longitude = parsed_data['longitude']
        latitude = parsed_data['latitude']
        
        logger.info(f"收到 HTTP 心跳請求 - 設備: {device_id}, 位置: ({longitude}, {latitude})")
        
        # 2. 執行廣告決策
        video_filename = ad_service.decide_ad(device_id, longitude, latitude)
        
        # 3. 處理設備不存在的情況
        if video_filename is None:
            return jsonify(HeartbeatResponse.error(
                f"找不到設備: {device_id}",
                404
            ))
        
        # 4. 嘗試通過 WebSocket 推送（如果設備在線）
        sid = get_device_sid(device_id)
        if sid:
            payload = {
                "command": "PLAY_VIDEO",
                "video_filename": video_filename,
                "trigger": "http_heartbeat",
                "device_id": device_id,
                "location": {
                    "longitude": longitude,
                    "latitude": latitude
                },
                "timestamp": datetime.now().isoformat()
            }
            
            socketio.emit('play_ad', payload, room=sid)
            connection_stats['messages_sent'] += 1
            
            logger.info(f"已通過 WebSocket 推送廣告到 {device_id}: {video_filename}")
        
        # 5. 返回 HTTP 響應（向後兼容）
        response = HeartbeatResponse.success(video_filename)
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"處理心跳請求時出錯: {e}", exc_info=True)
        return jsonify(HeartbeatResponse.error(
            "內部伺服器錯誤",
            500,
            str(e)
        ))


@app.route('/api/v1/admin/override', methods=['POST'])
def admin_override():
    """
    管理員推送覆蓋命令端點
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
        advertisement = db.advertisements.find_one({"_id": advertisement_id})
        
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
            "trigger": "admin_override",
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
                    socketio.emit('play_ad', payload, room=sid)
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
# 註冊前端管理 API Blueprint
# ============================================================================

# 初始化並註冊管理 API
admin_blueprint = init_admin_api(
    db=db,
    socketio=socketio,
    device_to_sid=device_to_sid,
    connection_stats=connection_stats,
    active_connections=active_connections
)
app.register_blueprint(admin_blueprint)

logger.info("前端管理 API 已註冊")


# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == '__main__':
    logger.info("啟動整合版智能計程車廣告服務...")
    logger.info(f"WebSocket 端點: ws://localhost:{FLASK_PORT}")
    logger.info(f"HTTP 端點: http://localhost:{FLASK_PORT}")
    logger.info("請先訪問 http://localhost:{}/init_db 來初始化數據庫".format(FLASK_PORT))
    
    # 運行應用程序（使用 SocketIO 的 run 方法）
    socketio.run(
        app,
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG,
        allow_unsafe_werkzeug=True  # 僅用於開發環境
    )
