import random
from typing import List, Optional, Tuple
from ..cards.card import RoleType, RoleCard, CardType
from ..cards.definitions import ALL_CHARACTERS
from ..cards.deck import Deck
from .player import Player

# 플레이어 수에 따른 역할 구성
ROLE_SETUP = {
    4: [RoleType.SHERIFF, RoleType.OUTLAW, RoleType.OUTLAW, RoleType.RENEGADE],
    5: [RoleType.SHERIFF, RoleType.DEPUTY, RoleType.OUTLAW, RoleType.OUTLAW, RoleType.RENEGADE],
    6: [RoleType.SHERIFF, RoleType.DEPUTY, RoleType.OUTLAW, RoleType.OUTLAW, RoleType.OUTLAW, RoleType.RENEGADE],
    7: [RoleType.SHERIFF, RoleType.DEPUTY, RoleType.DEPUTY, RoleType.OUTLAW, RoleType.OUTLAW, RoleType.OUTLAW, RoleType.RENEGADE],
}


class GameState:
    def __init__(self, players: List[Player]):
        assert 4 <= len(players) <= 7, "플레이어 수는 4~7명이어야 합니다."
        self.players       = players
        self.deck          = Deck()
        self.current_index = 0      # 현재 턴 플레이어 인덱스
        self.turn_number   = 0
        self.game_over     = False
        self.winner_team: Optional[str] = None
        self.log: List[str] = []

        self._setup()

    # ── 초기 설정 ────────────────────────────────────────────
    def _setup(self):
        self._assign_roles()
        self._assign_characters()
        self._deal_starting_hands()

    def _assign_roles(self):
        n = len(self.players)
        roles = [RoleCard(r) for r in ROLE_SETUP[n]]
        random.shuffle(roles)

        # 셰리프를 찾아 플레이어 0번에 배치하도록 순환
        sheriff_idx = next(i for i, r in enumerate(roles) if r.role == RoleType.SHERIFF)
        roles = roles[sheriff_idx:] + roles[:sheriff_idx]

        for p, r in zip(self.players, roles):
            p.role = r
            if r.role == RoleType.SHERIFF:
                p.is_sheriff = True

    def _assign_characters(self):
        chars = random.sample(ALL_CHARACTERS, len(self.players))
        for p, c in zip(self.players, chars):
            p.character  = c
            bonus_hp     = 1 if p.is_sheriff else 0
            p.max_hp     = c.base_hp + bonus_hp
            p.hp         = p.max_hp

    def _deal_starting_hands(self):
        for p in self.players:
            cards = self.deck.draw_n(p.max_hp)
            p.add_cards(cards)

    # ── 플레이어 순서 헬퍼 ───────────────────────────────────
    @property
    def current_player(self) -> Player:
        return self.players[self.current_index]

    def alive_players(self) -> List[Player]:
        return [p for p in self.players if p.is_alive]

    def alive_count(self) -> int:
        return sum(1 for p in self.players if p.is_alive)

    def next_player_index(self, from_index: int) -> int:
        n = len(self.players)
        idx = (from_index + 1) % n
        while not self.players[idx].is_alive:
            idx = (idx + 1) % n
        return idx

    def advance_turn(self):
        self.current_index = self.next_player_index(self.current_index)
        self.turn_number  += 1

    # ── 거리 계산 ────────────────────────────────────────────
    def distance(self, attacker: Player, target: Player) -> int:
        """살아있는 플레이어 기준 원형 거리."""
        alive = [p for p in self.players if p.is_alive]
        if attacker not in alive or target not in alive:
            return 999
        ai = alive.index(attacker)
        ti = alive.index(target)
        n  = len(alive)
        raw = min(abs(ai - ti), n - abs(ai - ti))
        return raw + target.effective_range_defense()

    def in_range(self, attacker: Player, target: Player) -> bool:
        return self.distance(attacker, target) <= attacker.effective_range_attack()

    def targets_in_range(self, attacker: Player) -> List[Player]:
        return [p for p in self.alive_players() if p != attacker and self.in_range(attacker, p)]

    # ── 승리 조건 체크 ──────────────────────────────────────
    def check_win(self) -> bool:
        alive = self.alive_players()
        sheriff_alive = any(p.is_sheriff for p in alive)

        outlaws_alive   = any(p.role_type == RoleType.OUTLAW    for p in alive)
        renegade_alive  = any(p.role_type == RoleType.RENEGADE  for p in alive)
        deputies_alive  = any(p.role_type == RoleType.DEPUTY    for p in alive)

        # 셰리프 사망 → 아웃로 승리 or 레네게이드 단독 생존 시 레네게이드 승리
        if not sheriff_alive:
            if len(alive) == 1 and renegade_alive:
                self.winner_team = "RENEGADE"
            else:
                self.winner_team = "OUTLAW"
            self.game_over = True
            return True

        # 아웃로와 레네게이드 모두 제거 → 셰리프+부관 승리
        if not outlaws_alive and not renegade_alive:
            self.winner_team = "SHERIFF"
            self.game_over = True
            return True

        return False

    # ── 로그 ────────────────────────────────────────────────
    def add_log(self, msg: str):
        self.log.append(msg)
        if len(self.log) > 200:
            self.log = self.log[-200:]
