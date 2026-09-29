"""好友系统 - 带6个bug"""
from dataclasses import dataclass, field

@dataclass
class Friend:
    pid: str
    name: str
    group: str = "default"
    intimacy: int = 0

class FriendSystem:
    def __init__(self):
        self.friends: dict[str, list[Friend]] = {}
        self.pending: dict[str, list] = {}
        self.blacklist: dict[str, set] = {}
        self.friend_limit = 100  # bug5: 硬编码

    def add_friend(self, from_pid, to_pid):
        # bug1: 无双向确认
        self.friends.setdefault(from_pid, []).append(Friend(to_pid, to_pid))
        self.friends.setdefault(to_pid, []).append(Friend(from_pid, from_pid))
        return True

    def move_group(self, pid, friend_pid, new_group):
        for f in self.friends.get(pid, []):
            if f.pid == friend_pid:
                f.group = new_group
                # bug2: 分组影响关系数据
                return True
        return False

    def add_intimacy(self, pid, friend_pid, source, amount):
        # bug3: 只看组队
        if source == "party":
            for f in self.friends.get(pid, []):
                if f.pid == friend_pid:
                    f.intimacy += amount
        return True

    def remove_friend(self, pid, friend_pid):
        # bug4: 无确认无恢复
        self.friends[pid] = [f for f in self.friends[pid] if f.pid != friend_pid]
        return True

    def block(self, pid, blocked_pid):
        # bug6: 不同步从好友移除
        self.blacklist.setdefault(pid, set()).add(blocked_pid)
