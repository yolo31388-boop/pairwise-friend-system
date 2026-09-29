"""好友系统 - 6个bug已修复"""
import time
from dataclasses import dataclass, field

# 亲密度合法来源：组队/送礼/聊天/副本
INTIMACY_SOURCES = ("party", "gift", "chat", "dungeon")
# 每日亲密度上限
DAILY_INTIMACY_CAP = 200
# 删除好友后的可恢复冷却期（秒）
RESTORE_COOLDOWN = 7 * 24 * 3600
# 好友上限按VIP等级配置
VIP_FRIEND_LIMITS = {0: 100, 1: 150, 2: 200, 3: 300, 4: 500}

@dataclass
class Friend:
    pid: str
    name: str
    group: str = "default"
    intimacy: int = 0

class FriendSystem:
    def __init__(self, daily_cap=DAILY_INTIMACY_CAP, restore_cooldown=RESTORE_COOLDOWN,
                 vip_limits=None):
        self.friends: dict[str, list[Friend]] = {}
        self.pending: dict[str, list] = {}
        self.blacklist: dict[str, set] = {}
        # 分组是纯显示属性，与关系数据分离
        self.groups: dict[str, dict[str, str]] = {}
        # 每日亲密度累计: {(pid, friend_pid): (date, amount)}
        self._daily_intimacy: dict[tuple, list] = {}
        self.daily_cap = daily_cap
        # 已删除待恢复: {pid: {friend_pid: (Friend, deleted_ts)}}
        self._removed: dict[str, dict[str, tuple]] = {}
        self.restore_cooldown = restore_cooldown
        self.vip_limits = dict(VIP_FRIEND_LIMITS if vip_limits is None else vip_limits)
        self.vip_levels: dict[str, int] = {}

    # ---- bug5: 上限按VIP等级 ----
    def set_vip_level(self, pid, level):
        self.vip_levels[pid] = level

    def friend_limit(self, pid):
        level = self.vip_levels.get(pid, 0)
        return self.vip_limits.get(level, self.vip_limits.get(0, 100))

    def _is_friend(self, pid, friend_pid):
        return any(f.pid == friend_pid for f in self.friends.get(pid, []))

    def _get_friend(self, pid, friend_pid):
        for f in self.friends.get(pid, []):
            if f.pid == friend_pid:
                return f
        return None

    # ---- bug6: 双向屏蔽判断 ----
    def is_blocked(self, pid, other_pid):
        return (other_pid in self.blacklist.get(pid, set())
                or pid in self.blacklist.get(other_pid, set()))

    def can_see_online(self, viewer_pid, target_pid):
        return not self.is_blocked(viewer_pid, target_pid)

    # ---- bug1: 添加好友需双向确认 ----
    def add_friend(self, from_pid, to_pid):
        if from_pid == to_pid or self.is_blocked(from_pid, to_pid):
            return False
        if self._is_friend(from_pid, to_pid):
            return False
        if from_pid in self.pending.get(to_pid, []):
            return True  # 已申请过，等待对方确认
        # 对方已向我发过申请 -> 直接互相确认
        if to_pid in self.pending.get(from_pid, []):
            return self.accept_friend(from_pid, to_pid)
        if len(self.friends.get(from_pid, [])) >= self.friend_limit(from_pid):
            return False
        self.pending.setdefault(to_pid, []).append(from_pid)
        return True

    def accept_friend(self, pid, from_pid):
        """pid 同意 from_pid 的好友申请，双方成为好友"""
        if from_pid not in self.pending.get(pid, []):
            return False
        if self.is_blocked(pid, from_pid):
            return False
        if (len(self.friends.get(pid, [])) >= self.friend_limit(pid)
                or len(self.friends.get(from_pid, [])) >= self.friend_limit(from_pid)):
            return False
        self.pending[pid].remove(from_pid)
        self.friends.setdefault(pid, []).append(Friend(from_pid, from_pid))
        self.friends.setdefault(from_pid, []).append(Friend(pid, pid))
        return True

    def reject_friend(self, pid, from_pid):
        if from_pid in self.pending.get(pid, []):
            self.pending[pid].remove(from_pid)
            return True
        return False

    # ---- bug2: 分组是纯显示属性，不改动关系数据 ----
    def move_group(self, pid, friend_pid, new_group):
        if not self._is_friend(pid, friend_pid):
            return False
        self.groups.setdefault(pid, {})[friend_pid] = new_group
        return True

    def get_group(self, pid, friend_pid):
        return self.groups.get(pid, {}).get(friend_pid, "default")

    # ---- bug3: 亲密度多来源 + 每日上限 ----
    def add_intimacy(self, pid, friend_pid, source, amount):
        if source not in INTIMACY_SOURCES or amount <= 0:
            return False
        f = self._get_friend(pid, friend_pid)
        if f is None:
            return False
        today = time.strftime("%Y-%m-%d")
        key = (pid, friend_pid)
        date, gained = self._daily_intimacy.get(key, (today, 0))
        if date != today:
            gained = 0
        room = max(0, self.daily_cap - gained)
        added = min(amount, room)
        if added == 0:
            return False
        f.intimacy += added
        self._daily_intimacy[key] = (today, gained + added)
        return True

    # ---- bug4: 删除需确认 + 冷却期内可恢复 ----
    def remove_friend(self, pid, friend_pid, confirm=False):
        if not confirm:
            return False
        f = self._get_friend(pid, friend_pid)
        if f is None:
            return False
        self.friends[pid] = [x for x in self.friends[pid] if x.pid != friend_pid]
        self._removed.setdefault(pid, {})[friend_pid] = (f, time.time())
        # 双向解除关系，对方那边也移除（亲密度各自保留在待恢复区）
        other = self._get_friend(friend_pid, pid)
        if other is not None:
            self.friends[friend_pid] = [x for x in self.friends[friend_pid] if x.pid != pid]
            self._removed.setdefault(friend_pid, {})[pid] = (other, time.time())
        return True

    def restore_friend(self, pid, friend_pid):
        entry = self._removed.get(pid, {}).get(friend_pid)
        if entry is None:
            return False
        f, ts = entry
        if time.time() - ts > self.restore_cooldown:
            return False  # 超过冷却期，亲密度无法恢复
        del self._removed[pid][friend_pid]
        if not self._is_friend(pid, friend_pid):
            self.friends.setdefault(pid, []).append(f)
        other_entry = self._removed.get(friend_pid, {}).pop(pid, None)
        if other_entry is not None and not self._is_friend(friend_pid, pid):
            self.friends.setdefault(friend_pid, []).append(other_entry[0])
        return True

    # ---- bug6: 拉黑自动移出好友列表并双向屏蔽 ----
    def block(self, pid, blocked_pid):
        self.blacklist.setdefault(pid, set()).add(blocked_pid)
        # 自动从双方好友列表移除
        if self._is_friend(pid, blocked_pid):
            self.remove_friend(pid, blocked_pid, confirm=True)
        # 清理未处理的申请
        if blocked_pid in self.pending.get(pid, []):
            self.pending[pid].remove(blocked_pid)
        if pid in self.pending.get(blocked_pid, []):
            self.pending[blocked_pid].remove(pid)
        return True

    def unblock(self, pid, blocked_pid):
        self.blacklist.get(pid, set()).discard(blocked_pid)
        return True
