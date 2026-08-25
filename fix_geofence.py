import math
import os
import sys

# 添加 src 目錄到 path 以便引入
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database import Database
from src.config import MONGODB_URI, DATABASE_NAME

def main():
    print(f"Connecting to MongoDB: {MONGODB_URI} / {DATABASE_NAME}")
    db_client = Database(MONGODB_URI, DATABASE_NAME)
    campaigns_collection = db_client.campaigns
    
    # 查找所有帶有 center_location 的 campaign
    campaigns = campaigns_collection.find({"center_location": {"$exists": True}, "radius_meters": {"$exists": True}})
    
    count = 0
    for campaign in campaigns:
        campaign_id = campaign.get("_id")
        center_location = campaign.get("center_location", {}).get("coordinates")
        radius_meters = campaign.get("radius_meters")
        
        if not center_location or not radius_meters:
            continue
            
        center_longitude, center_latitude = center_location
        radius_km = radius_meters / 1000
        
        # 考慮緯度對經度距離的影響
        lat_rad = math.radians(center_latitude)
        cos_lat = max(math.cos(lat_rad), 0.0001)
        
        # 判斷原來的點數（32或16）
        num_points = 32
        
        points = []
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            dx = radius_km / (111.32 * cos_lat) * math.cos(angle)
            dy = radius_km / 110.574 * math.sin(angle)
            points.append([center_longitude + dx, center_latitude + dy])
        
        # 閉合多邊形
        points.append(points[0])
        
        # 更新
        campaigns_collection.update_one(
            {"_id": campaign_id},
            {"$set": {"geo_fence.coordinates": [points]}}
        )
        count += 1
        print(f"Updated campaign: {campaign_id}")
        
    print(f"Migration completed. Updated {count} campaigns.")

if __name__ == '__main__':
    main()
