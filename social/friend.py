"""好友社交系统：双向好友、请求状态机、全交互拉黑、每日亲密度上限、VIP好友上限。"""
from dataclasses import dataclass, field
from datetime import date

BASE_FRIEND_LIMIT = 50
VIP_FRIEND_BONUS = 5
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

    def _get(self, pid: str) -> Player | None:
        return self.players.get(pid)

    def _is_blocked(self, pid: str, other_pid: str) -> bool:
        a, b = self._get(pid), self._get(other_pid)
        if a is None or b is None:
            return False
        return other_pid in a.blocked or pid in b.blocked

    def add_friend(self, from_pid: str, to_pid: str) -> bool:
        if from_pid == to_pid:
            return False
        a = self._ensure(from_pid)
        b = self._ensure(to_pid)
        if to_pid in a.friends and from_pid in b.friends:
            return True
        if self._is_blocked(from_pid, to_pid):
            return False
        if len(a.friends) >= self.get_friend_limit(from_pid):
            return False
        if len(b.friends) >= self.get_friend_limit(to_pid):
            return False
        if to_pid not in a.friends:
            a.friends.append(to_pid)
        if from_pid not in b.friends:
            b.friends.append(from_pid)
        return True

    def send_request(self, from_pid: str, to_pid: str) -> bool:
        if from_pid == to_pid:
            return False
        a, b = self._get(from_pid), self._get(to_pid)
        if a is None or b is None:
            return False
        if self._is_blocked(from_pid, to_pid):
            return False
        if to_pid in a.friends:
            return False
        if from_pid in b.requests:
            return False
        b.requests.append(from_pid)
        return True

    def accept_request(self, from_pid: str, to_pid: str) -> bool:
        a, b = self._get(from_pid), self._get(to_pid)
        if a is None or b is None:
            return False
        if to_pid in a.requests:
            a.requests.remove(to_pid)
        if from_pid in b.requests:
            b.requests.remove(from_pid)
        if to_pid in a.friends and from_pid in b.friends:
            return True
        return self.add_friend(from_pid, to_pid)

    def reject_request(self, from_pid: str, to_pid: str) -> bool:
        a, b = self._get(from_pid), self._get(to_pid)
        if a is None or b is None:
            return False
        removed = False
        if to_pid in a.requests:
            a.requests.remove(to_pid)
            removed = True
        if from_pid in b.requests:
            b.requests.remove(from_pid)
            removed = True
        return removed

    def block_player(self, pid: str, target_pid: str) -> bool:
        p = self._ensure(pid)
        if target_pid not in p.blocked:
            p.blocked.append(target_pid)
        return True

    def unblock_player(self, pid: str, target_pid: str) -> bool:
        p = self._get(pid)
        if p is None or target_pid not in p.blocked:
            return False
        p.blocked.remove(target_pid)
        return True

    def send_message(self, from_pid: str, to_pid: str, content: str = "") -> bool:
        if self._is_blocked(from_pid, to_pid):
            return False
        return True

    def invite_team(self, from_pid: str, to_pid: str) -> bool:
        if self._is_blocked(from_pid, to_pid):
            return False
        return True

    def invite_guild(self, from_pid: str, to_pid: str) -> bool:
        if self._is_blocked(from_pid, to_pid):
            return False
        return True

    send_chat = send_message
    send_team_invite = invite_team
    send_guild_invite = invite_guild

    def add_intimacy(self, pid: str, friend_pid: str, amount: int,
                     day: date | None = None) -> bool:
        if amount <= 0:
            return False
        p = self._ensure(pid)
        day = day or date.today()
        gained = p.intimacy_daily.get(friend_pid, (None, 0))
        used = gained[1] if gained[0] == day else 0
        if used >= DAILY_INTIMACY_CAP:
            return False
        allowed = min(amount, DAILY_INTIMACY_CAP - used)
        p.intimacy_daily[friend_pid] = (day, used + allowed)
        p.intimacy[friend_pid] = p.intimacy.get(friend_pid, 0) + allowed
        return True

    def calculate_intimacy(self, pid: str, friend_pid: str) -> int:
        p = self._get(pid)
        if p is None:
            return 0
        return p.intimacy.get(friend_pid, 0)

    def get_friend_limit(self, pid: str) -> int:
        p = self._get(pid)
        vip = p.vip_level if p is not None else 0
        return BASE_FRIEND_LIMIT + vip * VIP_FRIEND_BONUS
