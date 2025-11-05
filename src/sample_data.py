"""
示例數據定義
定義所有測試用的示例數據
"""

from models import DeviceModel, AdvertisementModel, CampaignModel


class SampleData:
    """示例數據類"""
    
    @staticmethod
    def get_devices():
        """獲取設備示例數據"""
        return [
            DeviceModel.create(
                device_id="taxi-AAB-1234-rooftop",
                device_type="rooftop",
                longitude=121.5644,
                latitude=25.0340,
                groups=["taipei-taxis", "all-rooftops"]
            ),
            DeviceModel.create(
                device_id="taxi-XYZ-5678-rooftop",
                device_type="rooftop",
                longitude=121.570,
                latitude=25.030,
                groups=["taipei-taxis", "all-rooftops"]
            ),
            DeviceModel.create(
                device_id="taxi-DEF-9999-rooftop",
                device_type="rooftop",
                longitude=121.520,
                latitude=25.050,
                groups=["taipei-taxis", "premium-fleet"]
            )
        ]
    
    @staticmethod
    def get_advertisements():
        """獲取廣告示例數據"""
        return [
            AdvertisementModel.create(
                ad_id="adv-001",
                name="西門影城電影廣告",
                video_filename="movie_ad_15s.mp4"
            ),
            AdvertisementModel.create(
                ad_id="adv-002",
                name="信義商圈購物促銷",
                video_filename="shopping_promo_20s.mp4"
            ),
            AdvertisementModel.create(
                ad_id="adv-003",
                name="台北101觀光廣告",
                video_filename="taipei101_tour_30s.mp4"
            ),
            AdvertisementModel.create(
                ad_id="adv-004",
                name="餐廳美食廣告",
                video_filename="restaurant_ad_25s.mp4"
            )
        ]
    
    @staticmethod
    def get_campaigns():
        """獲取活動示例數據"""
        return [
            CampaignModel.create(
                campaign_id="campaign-001",
                name="信義區晚間促銷",
                advertisement_id="adv-001",
                priority=10,
                target_groups=["taipei-taxis"],
                geo_fence_coordinates=[[
                    [121.56, 25.04],
                    [121.58, 25.04],
                    [121.58, 25.02],
                    [121.56, 25.02],
                    [121.56, 25.04]
                ]]
            ),
            CampaignModel.create(
                campaign_id="campaign-002",
                name="台北101區域廣告",
                advertisement_id="adv-003",
                priority=15,
                target_groups=["taipei-taxis", "all-rooftops"],
                geo_fence_coordinates=[[
                    [121.560, 25.030],
                    [121.570, 25.030],
                    [121.570, 25.037],
                    [121.560, 25.037],
                    [121.560, 25.030]
                ]]
            ),
            CampaignModel.create(
                campaign_id="campaign-003",
                name="西門町區域促銷",
                advertisement_id="adv-002",
                priority=8,
                target_groups=["taipei-taxis"],
                geo_fence_coordinates=[[
                    [121.500, 25.040],
                    [121.510, 25.040],
                    [121.510, 25.048],
                    [121.500, 25.048],
                    [121.500, 25.040]
                ]]
            ),
            CampaignModel.create(
                campaign_id="campaign-004",
                name="高端車隊專屬廣告",
                advertisement_id="adv-004",
                priority=20,
                target_groups=["premium-fleet"],
                geo_fence_coordinates=[[
                    [121.515, 25.045],
                    [121.525, 25.045],
                    [121.525, 25.055],
                    [121.515, 25.055],
                    [121.515, 25.045]
                ]]
            )
        ]

