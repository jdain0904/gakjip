"""AI 플레이어 의사결정 모듈."""
import random
from typing import List, Optional, Tuple

from ..cards.card import Card, CardType, RoleType
from .player import Player
from .game_state import GameState
from .game_engine import GameEngine


class AIDecision:
    """AI가 한 턴에 실행할 행동 목록."""
    def __init__(self):
        self.actions: List[Tuple[Card, Optional[Player], Optional[Card]]] = []
        # (사용할 카드, 대상 플레이어 or None, 추가 카드 or None)

    def add(self, card: Card, target: Optional[Player] = None, extra: Optional[Card] = None):
        self.actions.append((card, target, extra))


class AI:
    """우선순위 기반 AI."""

    def __init__(self, engine: GameEngine):
        self.engine = engine
        self.state  = engine.state

    # ── 턴 실행 ──────────────────────────────────────────────
    def take_turn(self, actor: Player) -> List[str]:
        """AI가 자신의 플레이 페이즈 전체를 실행. 이벤트 메시지 반환."""
        decision = self._decide(actor)
        for card, target, extra in decision.actions:
            ok, msg = self.engine.play_card(actor, card, target, extra)
            if not ok and msg:
                self.engine.log(f"[AI] {actor.name} 카드 실패: {msg}")
            if self.state.game_over:
                break

        # 패 제한 초과 → 무작위 버리기
        self._discard_excess(actor)
        return self.engine.flush_events()

    def _decide(self, actor: Player) -> AIDecision:
        d = AIDecision()

        # 1. Beer: HP 위험 시 우선 사용
        if actor.hp == 1 and self.state.alive_count() > 2:
            for card in actor.get_cards_of_type(CardType.BEER):
                d.add(card)
                break

        # 2. BANG! 사용
        targets = self._prioritize_targets(actor)
        for card in actor.get_cards_of_type(CardType.BANG):
            if actor.bang_played_this_turn >= 1 and actor.ability != "willy_the_kid":
                break
            if targets:
                d.add(card, targets[0])

        # Calamity Janet: Missed!를 BANG!으로
        if actor.ability == "calamity_janet":
            for card in actor.get_cards_of_type(CardType.MISSED):
                if actor.bang_played_this_turn >= 1:
                    break
                if targets:
                    d.add(card, targets[0])

        # 3. 장비 설치
        for ct in (CardType.BARREL, CardType.SCOPE, CardType.MUSTANG):
            if not actor.has_equipment(ct):
                for card in actor.get_cards_of_type(ct):
                    d.add(card)
                    break

        # 4. Dynamite: 낮은 HP면 오히려 위험 — HP >= 4 일 때만
        if actor.hp >= 4 and not actor.has_equipment(CardType.DYNAMITE):
            for card in actor.get_cards_of_type(CardType.DYNAMITE):
                d.add(card)
                break

        # 5. Duel: 우선 대상에게
        duel_targets = [p for p in self.state.alive_players()
                        if p != actor and self._is_enemy(actor, p)]
        for card in actor.get_cards_of_type(CardType.DUEL):
            if duel_targets:
                d.add(card, duel_targets[0])
                break

        # 6. Indians!
        for card in actor.get_cards_of_type(CardType.INDIANS):
            d.add(card)
            break

        # 7. Gatling (전체 공격 — 아군 피해 고려)
        enemies = [p for p in self.state.alive_players()
                   if p != actor and self._is_enemy(actor, p)]
        friends = [p for p in self.state.alive_players()
                   if p != actor and not self._is_enemy(actor, p)]
        if enemies and len(enemies) >= len(friends):
            for card in actor.get_cards_of_type(CardType.GATLING):
                d.add(card)
                break

        # 8. Panic! / Cat Balou: 가까운 적 카드 처리
        range1_enemies = [p for p in self.state.alive_players()
                          if p != actor
                          and self.state.distance(actor, p) <= 1
                          and self._is_enemy(actor, p)]
        for card in actor.get_cards_of_type(CardType.PANIC):
            if range1_enemies:
                d.add(card, range1_enemies[0])
                break
        for card in actor.get_cards_of_type(CardType.CAT_BALOU):
            if self.state.alive_players():
                t = range1_enemies[0] if range1_enemies else random.choice(
                    [p for p in self.state.alive_players() if p != actor] or [None]
                )
                if t:
                    d.add(card, t)
                    break

        # 9. Jail: 셰리프가 아닌 적에게
        jail_targets = [p for p in self.state.alive_players()
                        if p != actor and not p.is_sheriff and self._is_enemy(actor, p)
                        and not p.in_jail]
        for card in actor.get_cards_of_type(CardType.JAIL):
            if jail_targets:
                d.add(card, jail_targets[0])
                break

        # 10. Stagecoach / Wells Fargo
        for card in actor.get_cards_of_type(CardType.STAGECOACH):
            d.add(card)
            break
        for card in actor.get_cards_of_type(CardType.WELLS_FARGO):
            d.add(card)
            break

        # 11. Saloon: 아군 HP 낮을 때
        low_hp_friends = [p for p in self.state.alive_players() if p.hp < p.max_hp]
        if len(low_hp_friends) >= 2:
            for card in actor.get_cards_of_type(CardType.SALOON):
                d.add(card)
                break

        # 12. General Store
        for card in actor.get_cards_of_type(CardType.GENERAL_STORE):
            d.add(card)
            break

        return d

    # ── 대상 우선순위 ─────────────────────────────────────────
    def _prioritize_targets(self, actor: Player) -> List[Player]:
        in_range = self.state.targets_in_range(actor)
        enemies  = [p for p in in_range if self._is_enemy(actor, p)]
        # 낮은 HP 순 정렬
        enemies.sort(key=lambda p: p.hp)
        others   = [p for p in in_range if p not in enemies]
        return enemies + others

    def _is_enemy(self, actor: Player, target: Player) -> bool:
        """행위자 입장에서 target이 적인지 판단."""
        a_role = actor.role_type
        t_role = target.role_type

        if a_role == RoleType.SHERIFF:
            return t_role in (RoleType.OUTLAW, RoleType.RENEGADE)
        if a_role == RoleType.DEPUTY:
            return t_role in (RoleType.OUTLAW, RoleType.RENEGADE)
        if a_role == RoleType.OUTLAW:
            return t_role in (RoleType.SHERIFF, RoleType.DEPUTY)
        if a_role == RoleType.RENEGADE:
            # 레네게이드: 단독 생존 목표 → 셰리프를 마지막에 처치
            alive = self.state.alive_players()
            non_sheriff = [p for p in alive if not p.is_sheriff and p != actor]
            if non_sheriff:
                return not target.is_sheriff
            else:
                return target.is_sheriff
        return False

    # ── 패 제한 ───────────────────────────────────────────────
    def _discard_excess(self, actor: Player):
        while len(actor.hand) > actor.hp:
            # 우선순위: Missed! → 나머지 무작위
            to_discard = None
            for c in actor.hand:
                if c.card_type == CardType.MISSED:
                    to_discard = c
                    break
            if to_discard is None:
                to_discard = actor.hand[-1]
            actor.remove_card(to_discard)
            self.state.deck.discard(to_discard)
            self.engine.log(f"  [AI] {actor.name}이(가) {to_discard} 버림 (패 제한)")
