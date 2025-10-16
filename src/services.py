"""
業務邏輯服務層
實現廣告決策引擎的核心業務邏輯
"""

import logging
from models import DeviceModel, CampaignModel, HeartbeatResponse
from config import DEFAULT_VIDEO

logger = logging.getLogger(__name__)


class AdDecisionService:
    """廣告決策服務"""
    
    def __init__(self, database):
        """
        初始化廣告決策服務
        
        Args:
            database: Database 實例
        """
        self.db = database
    
    def decide_ad(self, device_id, longitude, latitude):
        """
        執行廣告決策邏輯
        
        Args:
            device_id: 設備 ID
            longitude: 經度
            latitude: 緯度
        
        Returns:
            str: 應播放的視頻文件名
        """
        try:
            # 1. 查找設備信息
            device = self.db.devices.find_one({"_id": device_id})
            
            if not device:
                logger.warning(f"找不到設備: {device_id}")
                return None
            
            device_groups = device.get('groups', [])
            logger.info(f"設備 {device_id} 的分組: {device_groups}")
            
            # 2. 更新設備的最後位置
            self.db.devices.update_one(
                {"_id": device_id},
                {
                    "$set": {
                        "last_location": DeviceModel.update_location(longitude, latitude)
                    }
                }
            )
            
            # 3. 構建地理空間查詢
            point = CampaignModel.create_point_query(longitude, latitude)
            
            # 4. 查找所有與設備位置相交的地理圍欄
            matching_campaigns = self.db.campaigns.find({
                "geo_fence": {
                    "$geoIntersects": {
                        "$geometry": point
                    }
                }
            })
            
            # 5. 過濾符合目標分組的活動
            eligible_campaigns = []
            for campaign in matching_campaigns:
                target_groups = campaign.get('target_groups', [])
                
                # 檢查設備的任一分組是否在活動的目標分組中
                if any(group in target_groups for group in device_groups):
                    eligible_campaigns.append(campaign)
                    logger.info(
                        f"找到符合條件的活動: {campaign['_id']} "
                        f"(優先級: {campaign.get('priority', 0)})"
                    )
            
            # 6. 選擇優先級最高的活動
            if not eligible_campaigns:
                logger.info("沒有找到符合條件的活動，使用預設視頻")
                return DEFAULT_VIDEO
            
            selected_campaign = max(
                eligible_campaigns,
                key=lambda c: c.get('priority', 0)
            )
            logger.info(f"選中活動: {selected_campaign['_id']}")
            
            # 7. 獲取對應的廣告視頻文件名
            advertisement_id = selected_campaign.get('advertisement_id')
            
            if not advertisement_id:
                logger.warning("活動中沒有 advertisement_id，使用預設視頻")
                return DEFAULT_VIDEO
            
            advertisement = self.db.advertisements.find_one({"_id": advertisement_id})
            
            if not advertisement:
                logger.warning(f"找不到廣告: {advertisement_id}，使用預設視頻")
                return DEFAULT_VIDEO
            
            video_filename = advertisement.get('video_filename', DEFAULT_VIDEO)
            logger.info(f"決定播放廣告視頻: {video_filename}")
            
            return video_filename
            
        except Exception as e:
            logger.error(f"廣告決策過程出錯: {e}", exc_info=True)
            return DEFAULT_VIDEO

