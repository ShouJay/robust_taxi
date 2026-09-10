import unittest

from src.services import AdDecisionService


class _Devices:
    def __init__(self, groups):
        self.document = {"_id": "device-1", "groups": groups}

    def find_one(self, _query):
        return self.document

    def update_one(self, *_args, **_kwargs):
        return None


class _Campaigns:
    def __init__(self, regional=None, global_campaigns=None):
        self.regional = regional or []
        self.global_campaigns = global_campaigns or []

    def find(self, query):
        if query.get("geo_scope") == "all":
            return list(self.global_campaigns)
        return list(self.regional)


class _Database:
    def __init__(self, groups, regional=None, global_campaigns=None):
        self.devices = _Devices(groups)
        self.campaigns = _Campaigns(regional, global_campaigns)


class CampaignTargetingTests(unittest.TestCase):
    def test_empty_target_groups_apply_to_every_device(self):
        campaign = {"_id": "all", "target_groups": [], "priority": 1}
        service = AdDecisionService(_Database(["school"], global_campaigns=[campaign]))

        _device, selected = service._get_eligible_campaign("device-1", 121.5, 25.0)

        self.assertEqual(selected["_id"], "all")

    def test_group_intersection_is_required_when_campaign_has_groups(self):
        school = {"_id": "school", "target_groups": ["school"], "priority": 5}
        club = {"_id": "club", "target_groups": ["club"], "priority": 9}
        service = AdDecisionService(_Database(["school"], regional=[school, club]))

        _device, selected = service._get_eligible_campaign("device-1", 121.5, 25.0)

        self.assertEqual(selected["_id"], "school")

    def test_priority_selects_between_eligible_campaigns(self):
        low = {"_id": "low", "target_groups": [], "priority": 2}
        high = {"_id": "high", "target_groups": ["school"], "priority": 5}
        service = AdDecisionService(_Database(["school"], regional=[low, high]))

        _device, selected = service._get_eligible_campaign("device-1", 121.5, 25.0)

        self.assertEqual(selected["_id"], "high")


if __name__ == "__main__":
    unittest.main()
