"""好友测试"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.engine import FriendSystem, Friend

class TestAdd:
    def test_add_requires_confirmation(self):
        fs = FriendSystem()
        fs.add_friend("p1", "p2")
        # p2应该在pending而不是直接成为好友
        assert "p2" not in [f.pid for f in fs.friends.get("p1", [])] or "p1" in fs.pending.get("p2", []), "添加好友无确认"

class TestIntimacy:
    def test_intimacy_multiple_sources(self):
        fs = FriendSystem()
        fs.friends["p1"] = [Friend("p2", "p2")]
        fs.add_intimacy("p1", "p2", "gift", 50)
        fs.add_intimacy("p1", "p2", "chat", 10)
        assert fs.friends["p1"][0].intimacy > 0, "非组队来源不加亲密度"
