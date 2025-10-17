"""
前端管理介面 API
提供給 Web 管理後台使用的 RESTful API
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 創建 Blueprint
admin_api = Blueprint('admin_api', __name__, url_prefix='/api/v1/admin')


def init_admin_api(db, socketio, device_to_sid, connection_stats, active_connections):
    """
    初始化管理 API
    
    Args:
        db: Database 實例
        socketio: SocketIO 實例
        device_to_sid: 設備到 SID 的映射
        connection_stats: 連接統計數據
        active_connections: 活動連接映射
    """
    
    # ========================================================================
    # 連接與設備管理 API
    # ========================================================================
    
    @admin_api.route('/connections', methods=['GET'])
    def get_connections():
        """
        獲取當前連接狀態
        
        前端用途：
        - 儀表板顯示在線設備
        - 設備監控頁面
        - 實時統計數據
        
        Returns:
            {
                "status": "success",
                "stats": {...},
                "active_devices": [...]
            }
        """
        try:
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
        except Exception as e:
            logger.error(f"獲取連接狀態失敗: {e}")
            return jsonify({
                "status": "error",
                "message": "獲取連接狀態失敗"
            }), 500
    
    
    @admin_api.route('/devices', methods=['GET'])
    def get_devices():
        """
        獲取所有設備列表
        
        前端用途：
        - 設備管理頁面
        - 設備選擇器
        
        Query Parameters:
            status: 過濾狀態 (active/inactive)
            type: 過濾設備類型
        
        Returns:
            {
                "status": "success",
                "total": 5,
                "devices": [...]
            }
        """
        try:
            # 獲取查詢參數
            status_filter = request.args.get('status')
            type_filter = request.args.get('type')
            
            # 構建查詢條件
            query = {}
            if status_filter:
                query['status'] = status_filter
            if type_filter:
                query['device_type'] = type_filter
            
            # 查詢設備
            devices = list(db.devices.find(query))
            
            # 轉換 ObjectId 為字符串
            for device in devices:
                if '_id' in device:
                    device['device_id'] = device.pop('_id')
                
                # 添加在線狀態
                device['is_online'] = device.get('device_id', device.get('_id')) in device_to_sid
            
            return jsonify({
                "status": "success",
                "total": len(devices),
                "devices": devices
            }), 200
            
        except Exception as e:
            logger.error(f"獲取設備列表失敗: {e}")
            return jsonify({
                "status": "error",
                "message": "獲取設備列表失敗"
            }), 500
    
    
    @admin_api.route('/devices/<device_id>', methods=['GET'])
    def get_device_detail(device_id):
        """
        獲取設備詳情
        
        前端用途：
        - 設備詳情頁面
        - 設備信息顯示
        
        Returns:
            {
                "status": "success",
                "device": {...}
            }
        """
        try:
            device = db.devices.find_one({"_id": device_id})
            
            if not device:
                return jsonify({
                    "status": "error",
                    "message": f"設備 {device_id} 不存在"
                }), 404
            
            # 轉換 _id
            device['device_id'] = device.pop('_id')
            
            # 添加在線狀態和連接信息
            device['is_online'] = device_id in device_to_sid
            if device['is_online']:
                sid = device_to_sid[device_id]
                if sid in active_connections:
                    device['connection_info'] = active_connections[sid]
            
            return jsonify({
                "status": "success",
                "device": device
            }), 200
            
        except Exception as e:
            logger.error(f"獲取設備詳情失敗: {e}")
            return jsonify({
                "status": "error",
                "message": "獲取設備詳情失敗"
            }), 500
    
    
    # ========================================================================
    # 廣告管理 API
    # ========================================================================
    
    @admin_api.route('/advertisements', methods=['GET'])
    def get_advertisements():
        """
        獲取廣告列表
        
        前端用途：
        - 廣告管理頁面
        - 廣告選擇器（推送時使用）
        
        Query Parameters:
            status: 過濾狀態 (active/inactive)
            type: 過濾類型
        
        Returns:
            {
                "status": "success",
                "total": 5,
                "advertisements": [...]
            }
        """
        try:
            # 獲取查詢參數
            status_filter = request.args.get('status')
            type_filter = request.args.get('type')
            
            # 構建查詢條件
            query = {}
            if status_filter:
                query['status'] = status_filter
            if type_filter:
                query['type'] = type_filter
            
            # 查詢廣告
            ads = list(db.advertisements.find(query))
            
            # 轉換 ObjectId
            for ad in ads:
                if '_id' in ad:
                    ad['advertisement_id'] = ad.pop('_id')
            
            return jsonify({
                "status": "success",
                "total": len(ads),
                "advertisements": ads
            }), 200
            
        except Exception as e:
            logger.error(f"獲取廣告列表失敗: {e}")
            return jsonify({
                "status": "error",
                "message": "獲取廣告列表失敗"
            }), 500
    
    
    @admin_api.route('/advertisements/<ad_id>', methods=['GET'])
    def get_advertisement_detail(ad_id):
        """
        獲取廣告詳情
        
        前端用途：
        - 廣告詳情頁面
        - 廣告預覽
        
        Returns:
            {
                "status": "success",
                "advertisement": {...}
            }
        """
        try:
            ad = db.advertisements.find_one({"_id": ad_id})
            
            if not ad:
                return jsonify({
                    "status": "error",
                    "message": f"廣告 {ad_id} 不存在"
                }), 404
            
            # 轉換 _id
            ad['advertisement_id'] = ad.pop('_id')
            
            return jsonify({
                "status": "success",
                "advertisement": ad
            }), 200
            
        except Exception as e:
            logger.error(f"獲取廣告詳情失敗: {e}")
            return jsonify({
                "status": "error",
                "message": "獲取廣告詳情失敗"
            }), 500
    
    
    # ========================================================================
    # 活動管理 API
    # ========================================================================
    
    @admin_api.route('/campaigns', methods=['GET'])
    def get_campaigns():
        """
        獲取活動列表
        
        前端用途：
        - 活動管理頁面
        - 活動列表展示
        
        Query Parameters:
            status: 過濾狀態 (active/inactive)
        
        Returns:
            {
                "status": "success",
                "total": 5,
                "campaigns": [...]
            }
        """
        try:
            # 獲取查詢參數
            status_filter = request.args.get('status')
            
            # 構建查詢條件
            query = {}
            if status_filter:
                query['status'] = status_filter
            
            # 查詢活動
            campaigns = list(db.campaigns.find(query))
            
            # 轉換 ObjectId 並關聯廣告信息
            for campaign in campaigns:
                if '_id' in campaign:
                    campaign['campaign_id'] = campaign.pop('_id')
                
                # 獲取關聯的廣告信息
                if 'advertisement_id' in campaign:
                    ad = db.advertisements.find_one({"_id": campaign['advertisement_id']})
                    if ad:
                        campaign['advertisement_name'] = ad.get('name', '')
                        campaign['advertisement_video'] = ad.get('video_filename', '')
            
            return jsonify({
                "status": "success",
                "total": len(campaigns),
                "campaigns": campaigns
            }), 200
            
        except Exception as e:
            logger.error(f"獲取活動列表失敗: {e}")
            return jsonify({
                "status": "error",
                "message": "獲取活動列表失敗"
            }), 500
    
    
    @admin_api.route('/campaigns/<campaign_id>', methods=['GET'])
    def get_campaign_detail(campaign_id):
        """
        獲取活動詳情
        
        前端用途：
        - 活動詳情頁面
        - 活動編輯表單
        
        Returns:
            {
                "status": "success",
                "campaign": {...}
            }
        """
        try:
            campaign = db.campaigns.find_one({"_id": campaign_id})
            
            if not campaign:
                return jsonify({
                    "status": "error",
                    "message": f"活動 {campaign_id} 不存在"
                }), 404
            
            # 轉換 _id
            campaign['campaign_id'] = campaign.pop('_id')
            
            # 獲取關聯的廣告詳細信息
            if 'advertisement_id' in campaign:
                ad = db.advertisements.find_one({"_id": campaign['advertisement_id']})
                if ad:
                    ad['advertisement_id'] = ad.pop('_id')
                    campaign['advertisement'] = ad
            
            return jsonify({
                "status": "success",
                "campaign": campaign
            }), 200
            
        except Exception as e:
            logger.error(f"獲取活動詳情失敗: {e}")
            return jsonify({
                "status": "error",
                "message": "獲取活動詳情失敗"
            }), 500
    
    
    # ========================================================================
    # 推送控制 API（已存在，但在這裡列出供參考）
    # ========================================================================
    
    @admin_api.route('/override', methods=['POST'])
    def admin_override():
        """
        管理員推送覆蓋命令
        
        前端用途：
        - 即時推送頁面
        - 批量推送功能
        
        Request Body:
            {
                "target_device_ids": ["taxi-AAB-1234-rooftop"],
                "advertisement_id": "adv-002"
            }
        
        Returns:
            {
                "status": "success",
                "advertisement": {...},
                "results": {...},
                "summary": {...}
            }
        """
        try:
            # 解析請求數據
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
            
            # 查找廣告信息
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
            
            # 構建推送載荷
            payload = {
                "command": "PLAY_VIDEO",
                "video_filename": video_filename,
                "advertisement_id": advertisement_id,
                "advertisement_name": advertisement.get('name', ''),
                "trigger": "admin_override",
                "priority": "override",
                "timestamp": datetime.now().isoformat()
            }
            
            # 向每個目標設備推送命令
            sent_to = []
            offline_devices = []
            
            for device_id in target_device_ids:
                sid = device_to_sid.get(device_id)
                
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
            
            # 構建並返回響應
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
    
    
    # ========================================================================
    # 統計數據 API
    # ========================================================================
    
    @admin_api.route('/stats/overview', methods=['GET'])
    def get_stats_overview():
        """
        獲取統計總覽
        
        前端用途：
        - 儀表板統計卡片
        - 數據總覽
        
        Returns:
            {
                "status": "success",
                "stats": {...}
            }
        """
        try:
            # 獲取設備總數
            total_devices = db.devices.count_documents({})
            
            # 獲取廣告總數
            total_ads = db.advertisements.count_documents({})
            active_ads = db.advertisements.count_documents({"status": "active"})
            
            # 獲取活動總數
            total_campaigns = db.campaigns.count_documents({})
            active_campaigns = db.campaigns.count_documents({"status": "active"})
            
            stats = {
                "devices": {
                    "total": total_devices,
                    "online": connection_stats['active_devices'],
                    "offline": total_devices - connection_stats['active_devices']
                },
                "advertisements": {
                    "total": total_ads,
                    "active": active_ads,
                    "inactive": total_ads - active_ads
                },
                "campaigns": {
                    "total": total_campaigns,
                    "active": active_campaigns,
                    "inactive": total_campaigns - active_campaigns
                },
                "connections": connection_stats
            }
            
            return jsonify({
                "status": "success",
                "stats": stats
            }), 200
            
        except Exception as e:
            logger.error(f"獲取統計數據失敗: {e}")
            return jsonify({
                "status": "error",
                "message": "獲取統計數據失敗"
            }), 500
    
    
    return admin_api

