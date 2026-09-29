"""好友系统 - 6个bug已修复"""
import time
from dataclasses import dataclass, field

# 亲密度来源权重（组队/送礼/聊天/副本）
INTIMACY_SOURCES = {"party", "gift", "chat", "dungeon"}

@dataclass
class Friend:
    pid: str
    name: str
    group: str = "default"
    intimacy: int = 0

class FriendSystem:
    def __init__(self, config=None):
        config = config or {}
        self.friends: dict[str, list[Friend]] = {}
        self.pending: dict[str, list] = {}
        self.blacklist: dict[str, set] = {}
        # 分组是纯显示属性，与关系数据分离存储
        self.groups: dict[str, dict[str, str]] = {}
        # 删除缓冲：冷却期内可恢复（含亲密度）
        self.removed: dict[str, dict[str, tuple[Friend, float]]] = {}
        # 每日亲密度获取记录 {(pid, friend_pid): (date, gained)}
        self._daily_intimacy: dict[tuple, tuple[str, int]] = {}
        self.daily_intimacy_cap = config.get("daily_intimacy_cap", 200)
        self.delete_cooldown = config.get("delete_cooldown", 7 * 24 * 3600)
        # 好友上限按VIP等级配置
        self.vip_levels: dict[str, int] = {}
        self.friend_limits = config.get(
            "friend_limits", {0: 100, 1: 150, 2: 200, 3: 300})

    def set_vip(self, pid, level):
        self.vip_levels[pid] = level

    def friend_limit(self, pid):
        level = self.vip_levels.get(pid, 0)
        return self.friend_limits.get(level, self.friend_limits[0])

    def _is_friend(self, pid, friend_pid):
        return any(f.pid == friend_pid for f in self.friends.get(pid, []))

    def _blocked(self, pid, other_pid):
        return (other_pid in self.blacklist.get(pid, set())
                or pid in self.blacklist.get(other_pid, set()))

    def add_friend(self, from_pid, to_pid):
        # fix1: 双向确认，同意前为"待确认"状态
        if self._blocked(from_pid, to_pid):
            return False
        if self._is_friend(from_pid, to_pid):
            return False
        if len(self.friends.get(from_pid, [])) >= self.friend_limit(from_pid):
            return False
        pend = self.pending.setdefault(to_pid, [])
        if from_pid not in pend:
            pend.append(from_pid)
        return True

    def confirm_friend(self, to_pid, from_pid):
        # 对方同意后双向建立好友关系
        if from_pid not in self.pending.get(to_pid, []):
            return False
        if self._blocked(from_pid, to_pid):
            return False
        for pid in (from_pid, to_pid):
            if len(self.friends.get(pid, [])) >= self.friend_limit(pid):
                return False
        self.pending[to_pid].remove(from_pid)
        self.friends.setdefault(from_pid, []).append(Friend(to_pid, to_pid))
        self.friends.setdefault(to_pid, []).append(Friend(from_pid, from_pid))
        return True

    def reject_friend(self, to_pid, from_pid):
        if from_pid in self.pending.get(to_pid, []):
            self.pending[to_pid].remove(from_pid)
            return True
        return False

    def move_group(self, pid, friend_pid, new_group):
        # fix2: 分组只改显示映射，不动Friend关系数据
        if not self._is_friend(pid, friend_pid):
            return False
        self.groups.setdefault(pid, {})[friend_pid] = new_group
        return True

    def get_group(self, pid, friend_pid):
        return self.groups.get(pid, {}).get(friend_pid, "default")

    def add_intimacy(self, pid, friend_pid, source, amount):
        # fix3: 多来源（组队/送礼/聊天/副本）+ 每日上限
        if source not in INTIMACY_SOURCES:
            return False
        if amount <= 0:
            return False
        today = time.strftime("%Y-%m-%d")
        key = (pid, friend_pid)
        date, gained = self._daily_intimacy.get(key, (today, 0))
        if date != today:
            gained = 0
        room = self.daily_intimacy_cap - gained
        if room <= 0:
            return False
        amount = min(amount, room)
        for f in self.friends.get(pid, []):
            if f.pid == friend_pid:
                f.intimacy += amount
                self._daily_intimacy[key] = (today, gained + amount)
                return True
        return False

    def remove_friend(self, pid, friend_pid, confirm=False):
        # fix4: 需二次确认；冷却期内可恢复（亲密度保留）
        if not confirm:
            return False
        target = None
        rest = []
        for f in self.friends.get(pid, []):
            if f.pid == friend_pid:
                target = f
            else:
                rest.append(f)
        if target is None:
            return False
        self.friends[pid] = rest
        self.removed.setdefault(pid, {})[friend_pid] = (target, time.time())
        return True

    def restore_friend(self, pid, friend_pid):
        entry = self.removed.get(pid, {}).get(friend_pid)
        if entry is None:
            return False
        friend, deleted_at = entry
        if time.time() - deleted_at > self.delete_cooldown:
            del self.removed[pid][friend_pid]
            return False
        self.friends.setdefault(pid, []).append(friend)
        del self.removed[pid][friend_pid]
        return True

    def block(self, pid, blocked_pid):
        # fix6: 拉黑自动双向移出好友列表并双向屏蔽
        self.blacklist.setdefault(pid, set()).add(blocked_pid)
        self.blacklist.setdefault(blocked_pid, set()).add(pid)
        for a, b in ((pid, blocked_pid), (blocked_pid, pid)):
            if a in self.friends:
                self.friends[a] = [f for f in self.friends[a] if f.pid != b]
            if b in self.pending.get(a, []):
                self.pending[a].remove(b)
        return True
