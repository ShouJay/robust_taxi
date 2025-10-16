"""
數據模型定義
定義所有 MongoDB 集合的數據結構
"""

class DeviceModel:
    """設備數據模型"""
    
    @staticmethod
    def create(device_id, device_type, longitude, latitude, groups):
        """創建設備文檔"""
        return {
            "_id": device_id,
            "device_type": device_type,
            "last_location": {
                "type": "Point",
                "coordinates": [longitude, latitude]  # [經度, 緯度]
            },
            "groups": groups
        }
    
    @staticmethod
    def update_location(longitude, latitude):
        """更新位置數據"""
        return {
            "type": "Point",
            "coordinates": [longitude, latitude]
        }


class AdvertisementModel:
    """廣告數據模型"""
    
    @staticmethod
    def create(ad_id, name, video_filename):
        """創建廣告文檔"""
        return {
            "_id": ad_id,
            "name": name,
            "video_filename": video_filename
        }


class CampaignModel:
    """活動數據模型"""
    
    @staticmethod
    def create(campaign_id, name, advertisement_id, priority, target_groups, geo_fence_coordinates):
        """
        創建活動文檔
        
        Args:
            campaign_id: 活動 ID
            name: 活動名稱
            advertisement_id: 關聯的廣告 ID
            priority: 優先級（數值越大優先級越高）
            target_groups: 目標分組列表
            geo_fence_coordinates: 地理圍欄坐標（多邊形）
                格式: [[[lon1, lat1], [lon2, lat2], [lon3, lat3], [lon1, lat1]]]
        """
        return {
            "_id": campaign_id,
            "name": name,
            "advertisement_id": advertisement_id,
            "priority": priority,
            "target_groups": target_groups,
            "geo_fence": {
                "type": "Polygon",
                "coordinates": geo_fence_coordinates
            }
        }
    
    @staticmethod
    def create_point_query(longitude, latitude):
        """創建地理空間查詢的 Point 對象"""
        return {
            "type": "Point",
            "coordinates": [longitude, latitude]
        }


class HeartbeatRequest:
    """心跳請求模型"""
    
    @staticmethod
    def validate(data):
        """
        驗證心跳請求數據
        
        Returns:
            tuple: (is_valid, error_message, parsed_data)
        """
        if not data:
            return False, "請求體不能為空", None
        
        device_id = data.get('device_id')
        location = data.get('location')
        
        if not device_id or not location:
            return False, "缺少必要欄位: device_id 和 location", None
        
        longitude = location.get('longitude')
        latitude = location.get('latitude')
        
        if longitude is None or latitude is None:
            return False, "location 必須包含 longitude 和 latitude", None
        
        # 驗證經緯度範圍
        if not (-180 <= longitude <= 180):
            return False, "longitude 必須在 -180 到 180 之間", None
        
        if not (-90 <= latitude <= 90):
            return False, "latitude 必須在 -90 到 90 之間", None
        
        parsed_data = {
            'device_id': device_id,
            'longitude': longitude,
            'latitude': latitude
        }
        
        return True, None, parsed_data


class HeartbeatResponse:
    """心跳響應模型"""
    
    @staticmethod
    def success(video_filename):
        """創建成功響應"""
        return {
            "command": "PLAY_VIDEO",
            "video_filename": video_filename
        }
    
    @staticmethod
    def error(message, status_code=400, detail=None):
        """創建錯誤響應"""
        response = {
            "status": "error",
            "message": message
        }
        if detail:
            response["detail"] = detail
        return response, status_code

