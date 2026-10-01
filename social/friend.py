"""好友社交"""
from dataclasses import dataclass, field
from datetime import date

BASE_FRIEND_LIMIT = 50
VIP_FRIEND_LIMIT_BONUS = 10
DAILY_INTIMACY_CAP = 500

@dataclass
class Player:
    pid: str
    friends: list = field(default_factory=list)
    blocked: list = field(default_factory=list)
    requests: list = field(default_factory=list)
    intimacy: dict = field(default_factory=dict)
    vip_level: int = 0
    intimacy_daily: dict = field(default_factory=dict)

class FriendSystem:
    def __init__(self):
        self.players: dict[str, Player] = {}

    def _ensure(self, pid: str) -> Player:
        if pid not in self.players:
            self.players[pid] = Player(pid)
        return self.players[pid]

    def is_blocked(self, pid: str, target_pid: str) -> bool:
        """任一方向拉黑即屏蔽。聊天/组队邀请/好友请求/公会邀请等所有交互前都应检查。"""
        a = self.players.get(pid)
        b = self.players.get(target_pid)
        return (a is not None and target_pid in a.blocked) or \
               (b is not None and pid in b.blocked)

    def add_friend(self, from_pid: str, to_pid: str) -> bool:
        if from_pid == to_pid or self.is_blocked(from_pid, to_pid):
            return False
        a = self._ensure(from_pid)
        b = self._ensure(to_pid)
        if to_pid in a.friends:
            return True
        if len(a.friends) >= self.get_friend_limit(from_pid):
            return False
        if len(b.friends) >= self.get_friend_limit(to_pid):
            return False
        a.friends.append(to_pid)
        b.friends.append(from_pid)
        return True

    def accept_request(self, from_pid: str, to_pid: str) -> bool:
        a = self._ensure(from_pid)
        b = self._ensure(to_pid)
        if to_pid in a.friends:
            self._clear_requests(a, b)
            return True
        if not self.add_friend(from_pid, to_pid):
            return False
        self._clear_requests(a, b)
        return True

    @staticmethod
    def _clear_requests(a: Player, b: Player) -> None:
        if b.pid in a.requests:
            a.requests.remove(b.pid)
        if a.pid in b.requests:
            b.requests.remove(a.pid)

    def block_player(self, pid: str, target_pid: str) -> bool:
        p = self._ensure(pid)
        t = self._ensure(target_pid)
        if target_pid not in p.blocked:
            p.blocked.append(target_pid)
        self._clear_requests(p, t)
        return True

    def add_intimacy(self, pid: str, friend_pid: str, amount: int) -> bool:
        p = self._ensure(pid)
        today = date.today().isoformat()
        day, gained = p.intimacy_daily.get(friend_pid, (today, 0))
        if day != today:
            gained = 0
        addable = min(amount, DAILY_INTIMACY_CAP - gained)
        if addable <= 0:
            return False
        p.intimacy_daily[friend_pid] = (today, gained + addable)
        p.intimacy[friend_pid] = p.intimacy.get(friend_pid, 0) + addable
        return True

    def get_friend_limit(self, pid: str) -> int:
        p = self.players.get(pid)
        vip = p.vip_level if p else 0
        return BASE_FRIEND_LIMIT + VIP_FRIEND_LIMIT_BONUS * vip
