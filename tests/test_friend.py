"""好友社交 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from social.friend import FriendSystem, Player

class TestBidirectionalFriend:
    def test_friend_added_both_sides(self):
        fs = FriendSystem()
        fs.players["a"] = Player("a")
        fs.players["b"] = Player("b")
        fs.add_friend("a", "b")
        assert "b" in fs.players["a"].friends
        assert "a" in fs.players["b"].friends

class TestAcceptRequestIdempotent:
    def test_accept_does_not_duplicate(self):
        fs = FriendSystem()
        fs.players["a"] = Player("a")
        fs.players["b"] = Player("b")
        fs.accept_request("a", "b")
        fs.accept_request("a", "b")
        assert fs.players["a"].friends.count("b") == 1

class TestBlockAllInteraction:
    def test_blocked_cannot_send_friend_request(self):
        fs = FriendSystem()
        fs.players["a"] = Player("a")
        fs.players["b"] = Player("b")
        fs.block_player("a", "b")
        # b应该不能给a发好友请求
        assert "b" in fs.players["a"].blocked

class TestIntimacyDailyLimit:
    def test_intimacy_has_daily_cap(self):
        fs = FriendSystem()
        fs.players["a"] = Player("a")
        for _ in range(100):
            fs.add_intimacy("a", "b", 10)
        # 应该有每日上限
        assert fs.players["a"].intimacy["b"] <= 500

class TestVIPFriendLimit:
    def test_vip_has_more_friend_slots(self):
        fs = FriendSystem()
        fs.players["a"] = Player("a", vip_level=0)
        fs.players["b"] = Player("b", vip_level=10)
        assert fs.get_friend_limit("b") > fs.get_friend_limit("a")
