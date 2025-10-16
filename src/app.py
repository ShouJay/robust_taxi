"""
智能計程車廣告服務後端應用程序
使用 Flask + MongoDB 實現廣告決策引擎

安裝依賴：
pip install flask pymongo

運行應用程序：
1. 確保 MongoDB 正在運行（本地或遠程）
2. 根據需要修改 config.py 中的配置
3. 運行：python app.py
4. 首次運行時，訪問 http://localhost:5000/init_db 來初始化數據庫和示例數據
5. 使用 POST 請求測試 /api/v1/device/heartbeat 端點

測試範例（使用 curl）：
curl -X POST http://localhost:5000/api/v1/device/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"device_id": "taxi-AAB-1234-rooftop", "location": {"longitude": 121.567, "latitude": 25.035}}'
"""

from flask import Flask, request, jsonify
import logging

# 導入配置和模組
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, LOG_LEVEL, MONGODB_URI, DATABASE_NAME
from database import Database
from services import AdDecisionService
from models import HeartbeatRequest, HeartbeatResponse
from sample_data import SampleData

# ============================================================================
# 應用程序設置
# ============================================================================

app = Flask(__name__)

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
    
    logger.info("應用程序初始化完成")
except Exception as e:
    logger.error(f"應用程序初始化失敗: {e}")
    raise


# ============================================================================
# API 端點
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    """
    根路徑 - 提供 API 信息
    """
    return jsonify({
        "service": "智能計程車廣告服務",
        "version": "2.0.0",
        "architecture": "分層架構",
        "endpoints": {
            "heartbeat": "POST /api/v1/device/heartbeat",
            "init_db": "GET /init_db",
            "health": "GET /health"
        },
        "modules": {
            "config": "配置管理",
            "models": "數據模型",
            "database": "數據庫連接",
            "services": "業務邏輯",
            "sample_data": "示例數據"
        }
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """
    健康檢查端點
    """
    try:
        # 測試數據庫連接
        is_healthy = db.health_check()
        
        if is_healthy:
            return jsonify({
                "status": "healthy",
                "database": "connected"
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
    """
    初始化數據庫端點
    
    訪問此端點來創建索引和插入示例數據。
    通常只需要在首次設置時調用一次。
    """
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
    設備心跳端點 - 廣告決策引擎核心
    
    接收設備的位置信息，根據地理圍欄和其他規則決定播放哪個廣告。
    
    Request Body:
    {
        "device_id": "taxi-AAB-1234-rooftop",
        "location": {
            "longitude": 121.567,
            "latitude": 25.035
        }
    }
    
    Response:
    {
        "command": "PLAY_VIDEO",
        "video_filename": "movie_ad_15s.mp4"
    }
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
        
        logger.info(
            f"收到心跳請求 - 設備: {device_id}, "
            f"位置: ({longitude}, {latitude})"
        )
        
        # 2. 執行廣告決策
        video_filename = ad_service.decide_ad(device_id, longitude, latitude)
        
        # 3. 處理設備不存在的情況
        if video_filename is None:
            return jsonify(HeartbeatResponse.error(
                f"找不到設備: {device_id}",
                404
            ))
        
        # 4. 構建並返回響應
        response = HeartbeatResponse.success(video_filename)
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"處理心跳請求時出錯: {e}", exc_info=True)
        return jsonify(HeartbeatResponse.error(
            "內部伺服器錯誤",
            500,
            str(e)
        ))


# ============================================================================
# 應用程序錯誤處理
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """處理 404 錯誤"""
    return jsonify({
        "status": "error",
        "message": "找不到請求的資源"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """處理 500 錯誤"""
    logger.error(f"內部伺服器錯誤: {error}")
    return jsonify({
        "status": "error",
        "message": "內部伺服器錯誤"
    }), 500


# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == '__main__':
    logger.info("啟動 Flask 應用程序...")
    logger.info(f"配置: Host={FLASK_HOST}, Port={FLASK_PORT}, Debug={FLASK_DEBUG}")
    logger.info("請先訪問 http://localhost:5000/init_db 來初始化數據庫")
    
    # 運行應用程序
    try:
        app.run(
            host=FLASK_HOST,
            port=FLASK_PORT,
            debug=FLASK_DEBUG
        )
    finally:
        # 關閉數據庫連接
        db.close()
        logger.info("應用程序已停止")
