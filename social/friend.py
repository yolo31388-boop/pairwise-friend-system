"""好友社交 - 含5个bug"""
from dataclasses import dataclass, field

@dataclass
class Player:
    pid: str
    friends: list = field(default_factory=list)
    blocked: list = field(default_factory=list)
    requests: list = field(default_factory=list)
    intimacy: dict = field(default_factory=dict)
    vip_level: int = 0

class FriendSystem:
    def __init__(self):
        self.players: dict[str, Player] = {}

    def add_friend(self, from_pid: str, to_pid: str) -> bool:
        # bug1: 只加发起方，不加对方
        if from_pid not in self.players:
            self.players[from_pid] = Player(from_pid)
        if to_pid not in self.players[from_pid].friends:
            self.players[from_pid].friends.append(to_pid)
        return True

    def accept_request(self, from_pid: str, to_pid: str) -> bool:
        # bug2: 不删除请求记录，重复接受
        self.add_friend(from_pid, to_pid)
        return True

    def block_player(self, pid: str, target_pid: str) -> bool:
        # bug3: 只屏蔽聊天
        if pid not in self.players:
            self.players[pid] = Player(pid)
        if target_pid not in self.players[pid].blocked:
            self.players[pid].blocked.append(target_pid)
        return True

    def add_intimacy(self, pid: str, friend_pid: str, amount: int) -> bool:
        # bug4: 无每日上限
        if pid not in self.players:
            self.players[pid] = Player(pid)
        current = self.players[pid].intimacy.get(friend_pid, 0)
        self.players[pid].intimacy[friend_pid] = current + amount
        return True

    def get_friend_limit(self, pid: str) -> int:
        # bug5: VIP不生效
        return 50
