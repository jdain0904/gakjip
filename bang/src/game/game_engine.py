"""핵심 게임 규칙 엔진."""
import random
from typing import List, Optional, Callable, Tuple

from ..cards.card import Card, CardType, RoleType
from ..cards.deck import Deck
from .player import Player
from .game_state import GameState


# ── 콜백 타입 ──────────────────────────────────────────────
# 인터페이스: game_engine은 UI를 직접 호출하지 않고
# 이벤트를 GameEngine.event_log 리스트에 쌓는다.

class GameEngine:
    def __init__(self, state: GameState):
        self.state  = state
        self.events: List[str] = []   # UI가 소비할 이벤트 메시지

    # ── 이벤트 로그 ──────────────────────────────────────────
    def log(self, msg: str):
        self.state.add_log(msg)
        self.events.append(msg)

    def flush_events(self) -> List[str]:
        evts        = self.events[:]
        self.events = []
        return evts

    # ── 턴 구조 ──────────────────────────────────────────────
    def start_turn(self) -> List[str]:
        """턴 시작 처리: 다이너마이트→감옥→드로우."""
        self.events = []
        p = self.state.current_player

        # 다이너마이트
        if p.has_equipment(CardType.DYNAMITE):
            self._resolve_dynamite(p)
            if p.is_dead():
                self._on_player_death(p, killer=None)
                return self.flush_events()

        if not p.is_alive:
            return self.flush_events()

        # 감옥
        if p.in_jail:
            escaped = self._resolve_jail(p)
            p.in_jail = False
            if not escaped:
                self.log(f"🔒 {p.name}은(는) 감옥에서 벗어나지 못했다. 턴 종료.")
                return self.flush_events()

        # 드로우
        self._draw_phase(p)
        return self.flush_events()

    def end_turn(self, player: Player) -> List[str]:
        """턴 종료 처리: 패 제한(hp 이하) 초과 시 버리기."""
        self.events = []
        player.bang_played_this_turn = 0

        # 패 제한 초과분은 caller(UI/AI)가 이미 버렸다고 가정
        # 여기서는 다이너마이트 전달 처리
        self._pass_dynamite_if_needed(player)

        self.state.advance_turn()
        return self.flush_events()

    # ── 드로우 페이즈 ─────────────────────────────────────────
    def _draw_phase(self, p: Player):
        ability = p.ability

        if ability == "kit_carlson":
            top3 = [self.state.deck.pop_top() for _ in range(3) if self.state.deck.peek_top()]
            self.log(f"🎴 Kit Carlson: 덱 상위 3장 공개 → {', '.join(str(c) for c in top3)}")
            # AI/Human이 선택 — 여기서는 그냥 상위 2장 드로우, 나머지 1장 복귀
            chosen = top3[:2]
            returned = top3[2:3]
            p.add_cards(chosen)
            for c in reversed(returned):
                self.state.deck._draw.append(c)  # 상단에 복귀
            self.log(f"  → {', '.join(str(c) for c in chosen)} 선택")
        elif ability == "black_jack":
            c1 = self.state.deck.pop_top()
            c2 = self.state.deck.pop_top()
            p.add_card(c1)
            extra = c2 is not None and c2.draw_check_is_hit()
            p.add_card(c2)
            if extra:
                c3 = self.state.deck.pop_top()
                if c3:
                    p.add_card(c3)
                    self.log(f"♦/♥ Black Jack: {c2} 공개 → 추가 드로우 {c3}")
                else:
                    self.log(f"♦/♥ Black Jack: {c2} 공개 → 추가 드로우 없음")
        elif ability == "pedro_ramirez":
            disc = self.state.deck.pop_top_discard()
            if disc:
                p.add_card(disc)
                self.log(f"♻️  Pedro Ramirez: 버린 더미에서 {disc} 획득")
            c2 = self.state.deck.pop_top()
            if c2:
                p.add_card(c2)
        else:
            cards = self.state.deck.draw_n(2)
            p.add_cards(cards)
            self.log(f"🃏 {p.name}이(가) 카드 2장 드로우")

    # ── 카드 사용 ─────────────────────────────────────────────
    def play_card(self, actor: Player, card: Card,
                  target: Optional[Player] = None,
                  extra_card: Optional[Card] = None) -> Tuple[bool, str]:
        """
        카드 사용 시도. 성공 여부와 메시지 반환.
        extra_card: Duel 등에서 추가 카드 쌍을 처리할 때 사용.
        """
        ct = card.card_type

        # Willy the Kid는 BANG! 무제한
        if ct == CardType.BANG:
            if actor.ability != "willy_the_kid" and actor.bang_played_this_turn >= 1:
                return False, "이미 이번 턴에 BANG!을 사용했습니다."
            if target is None:
                return False, "대상을 지정해야 합니다."
            if not self.state.in_range(actor, target):
                return False, f"{target.name}은(는) 사거리 밖입니다."

        # 카드를 패에서 제거
        actor.remove_card(card)

        if ct == CardType.BANG:
            self._resolve_bang(actor, target, card)
        elif ct == CardType.BEER:
            if self.state.alive_count() == 2:
                actor.hand.append(card)  # 반환
                return False, "맥주는 마지막 2인에겐 효과가 없습니다."
            actor.gain_hp(1)
            self.log(f"🍺 {actor.name}이(가) 맥주를 마셨다. HP +1 ({actor.hp}/{actor.max_hp})")
        elif ct == CardType.SALOON:
            for p in self.state.alive_players():
                p.gain_hp(1)
            self.log(f"🍻 {actor.name}이(가) 술집 라운드를 샀다. 모두 HP +1")
        elif ct == CardType.GATLING:
            self._resolve_gatling(actor, card)
        elif ct == CardType.INDIANS:
            self._resolve_indians(actor, card)
        elif ct == CardType.DUEL:
            if target is None:
                actor.hand.append(card); return False, "결투 대상을 지정해야 합니다."
            self._resolve_duel(actor, target, card)
        elif ct == CardType.GENERAL_STORE:
            self._resolve_general_store(actor, card)
        elif ct == CardType.PANIC:
            if target is None:
                actor.hand.append(card); return False, "대상을 지정해야 합니다."
            if self.state.distance(actor, target) > 1:
                actor.hand.append(card); return False, "Panic!은 거리 1 이내 대상에게만."
            self._resolve_panic(actor, target, card)
        elif ct == CardType.CAT_BALOU:
            if target is None:
                actor.hand.append(card); return False, "대상을 지정해야 합니다."
            self._resolve_cat_balou(actor, target, card)
        elif ct == CardType.STAGECOACH:
            cards = self.state.deck.draw_n(2)
            actor.add_cards(cards)
            self.log(f"🚌 {actor.name}이(가) 역마차를 탔다. 카드 2장 드로우.")
            self.state.deck.discard(card)
        elif ct == CardType.WELLS_FARGO:
            cards = self.state.deck.draw_n(3)
            actor.add_cards(cards)
            self.log(f"🏦 {actor.name}이(가) 웰스 파고에서 인출. 카드 3장 드로우.")
            self.state.deck.discard(card)
        elif ct in (CardType.BARREL, CardType.SCOPE, CardType.MUSTANG):
            if actor.has_equipment(ct):
                actor.hand.append(card)
                return False, f"이미 {ct.value}를 장착하고 있습니다."
            actor.equip(card)
            self.log(f"🔧 {actor.name}이(가) {ct.value} 장착.")
        elif ct == CardType.DYNAMITE:
            if actor.has_equipment(CardType.DYNAMITE):
                actor.hand.append(card)
                return False, "이미 다이너마이트를 가지고 있습니다."
            actor.equip(card)
            self.log(f"💣 {actor.name}이(가) 다이너마이트를 붙였다...")
        elif ct == CardType.JAIL:
            if target is None:
                actor.hand.append(card); return False, "감옥 대상을 지정해야 합니다."
            if target.is_sheriff:
                actor.hand.append(card); return False, "셰리프를 감옥에 넣을 수 없습니다."
            if target.in_jail:
                actor.hand.append(card); return False, f"{target.name}은(는) 이미 감옥입니다."
            target.in_jail = True
            self.log(f"⛓️  {actor.name}이(가) {target.name}을(를) 감옥에 집어넣었다.")
            self.state.deck.discard(card)
        else:
            actor.hand.append(card)
            return False, f"사용 불가: {card}"

        # 캐릭터 능력 트리거
        self._check_suzy_lafayette(actor)
        return True, ""

    # ── BANG! 해결 ────────────────────────────────────────────
    def _resolve_bang(self, actor: Player, target: Player, bang_card: Card):
        actor.bang_played_this_turn += 1
        self.log(f"🔫 {actor.name}이(가) {target.name}에게 BANG!")
        self.state.deck.discard(bang_card)

        needed_misses = 2 if actor.ability == "slab_the_killer" else 1

        # 배럴 체크
        barrel_hit = self._barrel_check(target)
        if barrel_hit:
            self.log(f"  🛢️  배럴이 총알을 막았다!")
            needed_misses -= 1

        if needed_misses <= 0:
            return  # 완전히 막힘

        # Missed! 카드로 회피 (AI/Human 결정은 엔진 외부에서)
        # 여기서는 단순: Calamity Janet or 패에 Missed!
        missed_cards = self._collect_missed(target, needed_misses)
        if len(missed_cards) >= needed_misses:
            self.log(f"  💨 {target.name}이(가) 피했다!")
            for mc in missed_cards:
                self.state.deck.discard(mc)
        else:
            # 미스 부족 → 피해
            for mc in missed_cards:
                self.state.deck.discard(mc)
            self._apply_damage(actor, target, 1)

    def _collect_missed(self, target: Player, needed: int) -> List[Card]:
        """Missed! or Calamity Janet BANG! 수집."""
        collected = []
        for _ in range(needed):
            miss = self._find_missed_card(target)
            if miss is None:
                break
            target.remove_card(miss)
            collected.append(miss)
        return collected

    def _find_missed_card(self, target: Player) -> Optional[Card]:
        # 먼저 Missed! 찾기
        for c in target.hand:
            if c.card_type == CardType.MISSED:
                return c
        # Calamity Janet은 BANG!으로 Missed! 대신 사용
        if target.ability == "calamity_janet":
            for c in target.hand:
                if c.card_type == CardType.BANG:
                    return c
        return None

    def _barrel_check(self, target: Player) -> bool:
        """배럴 장착 or Jourdonnais: ♥ 뒤집으면 막음."""
        has_barrel = target.has_equipment(CardType.BARREL) or target.ability == "jourdonnais"
        if not has_barrel:
            return False
        card = self.state.deck.pop_top()
        if card is None:
            return False
        self.log(f"  🛢️  배럴 판정: {card} → {'♥/♦ 히트!' if card.draw_check_is_hit() else '빗나감'}")
        self.state.deck.discard(card)
        if target.ability == "lucky_duke":
            # 2장 뒤집어 유리한 것
            card2 = self.state.deck.pop_top()
            if card2:
                self.log(f"  🎲 Lucky Duke 추가 판정: {card2}")
                self.state.deck.discard(card2)
                return card.draw_check_is_hit() or card2.draw_check_is_hit()
        return card.draw_check_is_hit()

    # ── 피해 적용 ─────────────────────────────────────────────
    def _apply_damage(self, killer: Optional[Player], victim: Player, amount: int):
        self.log(f"  💥 {victim.name}이(가) {amount} 피해를 받았다! ({victim.hp} → {victim.hp - amount})")
        victim.lose_hp(amount)

        # Bart Cassidy: 피격 시 드로우
        if victim.is_alive and victim.ability == "bart_cassidy":
            card = self.state.deck.pop_top()
            if card:
                victim.add_card(card)
                self.log(f"  🃏 Bart Cassidy: 피격 드로우 {card}")

        # El Gringo: 공격자에서 카드 강탈
        if victim.is_alive and victim.ability == "el_gringo" and killer and killer.hand:
            stolen = random.choice(killer.hand)
            killer.remove_card(stolen)
            victim.add_card(stolen)
            self.log(f"  🖐️  El Gringo: {killer.name}에게서 {stolen} 강탈!")

        if victim.is_dead():
            self._on_player_death(victim, killer)

    def _on_player_death(self, victim: Player, killer: Optional[Player]):
        self.log(f"  ☠️  {victim.name}이(가) 황천길을 떠났다...")

        # 아웃로 처치 시 보상
        if killer and victim.role_type == RoleType.OUTLAW:
            cards = self.state.deck.draw_n(3)
            killer.add_cards(cards)
            self.log(f"  🎁 {killer.name}이(가) 현상금 카드 3장을 챙겼다.")

        # 셰리프가 부관을 처치 → 패 전체 버리기 패널티
        if killer and killer.is_sheriff and victim.role_type == RoleType.DEPUTY:
            self.log(f"  ⚠️  셰리프가 부관을 죽였다! 패 전체를 잃는다...")
            self.state.deck.discard_many(killer.hand)
            self.state.deck.discard_many(killer.equipment)
            killer.hand.clear()
            killer.equipment.clear()

        # Vulture Sam: 죽은 플레이어 패·장비 수거
        for p in self.state.alive_players():
            if p.ability == "vulture_sam" and p != victim:
                p.add_cards(victim.hand[:])
                p.add_cards(victim.equipment[:])
                self.log(f"  🦅 Vulture Sam {p.name}이(가) {victim.name}의 모든 카드를 챙겼다.")
                break

        victim.hand.clear()
        victim.equipment.clear()
        self.state.check_win()

    # ── Gatling ───────────────────────────────────────────────
    def _resolve_gatling(self, actor: Player, card: Card):
        self.log(f"💥 {actor.name}이(가) 개틀링을 발사! 모두를 향해...")
        self.state.deck.discard(card)
        for target in self.state.alive_players():
            if target == actor:
                continue
            self.log(f"  🎯 → {target.name}")
            missed = self._find_missed_card(target)
            barrel = self._barrel_check(target)
            if barrel:
                self.log(f"    🛢️  배럴이 막았다!")
                continue
            if missed:
                target.remove_card(missed)
                self.state.deck.discard(missed)
                self.log(f"    💨 {target.name}이(가) 피했다!")
            else:
                self._apply_damage(actor, target, 1)
                if self.state.game_over:
                    return

    # ── Indians! ─────────────────────────────────────────────
    def _resolve_indians(self, actor: Player, card: Card):
        self.log(f"🏹 {actor.name}이(가) 인디언을 소환! 모두 BANG! 혹은 피해.")
        self.state.deck.discard(card)
        for target in self.state.alive_players():
            if target == actor:
                continue
            bang = self._find_bang_card(target)
            if bang:
                target.remove_card(bang)
                self.state.deck.discard(bang)
                self.log(f"  🔫 {target.name}이(가) 총을 쏴 인디언을 쫓았다.")
            else:
                self._apply_damage(actor, target, 1)
                if self.state.game_over:
                    return

    def _find_bang_card(self, p: Player) -> Optional[Card]:
        for c in p.hand:
            if c.card_type == CardType.BANG:
                return c
        if p.ability == "calamity_janet":
            for c in p.hand:
                if c.card_type == CardType.MISSED:
                    return c
        return None

    # ── Duel ─────────────────────────────────────────────────
    def _resolve_duel(self, actor: Player, target: Player, card: Card):
        self.log(f"⚔️  {actor.name}이(가) {target.name}에게 결투를 신청했다!")
        self.state.deck.discard(card)
        current_responder = target
        current_challenger = actor
        while True:
            bang = self._find_bang_card(current_responder)
            if bang:
                current_responder.remove_card(bang)
                self.state.deck.discard(bang)
                self.log(f"  🔫 {current_responder.name}이(가) BANG!으로 응수!")
                current_responder, current_challenger = current_challenger, current_responder
            else:
                self.log(f"  💥 {current_responder.name}이(가) 더 이상 쏠 수 없다!")
                self._apply_damage(current_challenger, current_responder, 1)
                return

    # ── General Store ─────────────────────────────────────────
    def _resolve_general_store(self, actor: Player, card: Card):
        alive = self.state.alive_players()
        n = len(alive)
        self.log(f"🏪 {actor.name}이(가) 잡화점을 열었다!")
        self.state.deck.discard(card)
        offered = [self.state.deck.pop_top() for _ in range(n) if self.state.deck.peek_top()]
        offered = [c for c in offered if c is not None]
        self.log(f"  진열된 카드: {', '.join(str(c) for c in offered)}")

        # 셰리프부터 순서대로 선택 (AI는 첫 번째 카드 선택)
        idx = alive.index(actor)
        for i in range(n):
            p = alive[(idx + i) % n]
            if offered:
                chosen = offered.pop(0)  # AI는 순서대로 첫 카드
                p.add_card(chosen)
                self.log(f"  {p.name} → {chosen}")

    # ── Panic! / Cat Balou ────────────────────────────────────
    def _resolve_panic(self, actor: Player, target: Player, card: Card):
        self.state.deck.discard(card)
        stolen = self._pick_random_card_from(target)
        if stolen:
            actor.add_card(stolen)
            self.log(f"  🖐️  Panic!: {actor.name}이(가) {target.name}에게서 {stolen} 강탈!")
        else:
            self.log(f"  {target.name}에게 뺏을 카드가 없다.")

    def _resolve_cat_balou(self, actor: Player, target: Player, card: Card):
        self.state.deck.discard(card)
        discarded = self._pick_random_card_from(target)
        if discarded:
            self.state.deck.discard(discarded)
            self.log(f"  🐱 Cat Balou: {target.name}의 {discarded} 버리기!")
        else:
            self.log(f"  {target.name}에게 버릴 카드가 없다.")

    def _pick_random_card_from(self, target: Player) -> Optional[Card]:
        all_cards = target.hand + target.equipment
        if not all_cards:
            return None
        chosen = random.choice(all_cards)
        if chosen in target.hand:
            target.remove_card(chosen)
        else:
            target.unequip(chosen)
        return chosen

    # ── Dynamite ─────────────────────────────────────────────
    def _resolve_dynamite(self, p: Player):
        dyn = p.get_equipment(CardType.DYNAMITE)
        if not dyn:
            return
        card = self.state.deck.pop_top()
        if card is None:
            return
        self.state.deck.discard(card)
        self.log(f"💣 다이너마이트 판정: {card}")
        # 폭발 조건: 스페이드 2~9
        from ..cards.card import CardSuit, CardValue
        explodes = (
            card.suit == CardSuit.SPADES
            and card.value.numeric <= 9
            and card.value.numeric >= 2
        )
        if explodes:
            p.unequip(dyn)
            self.state.deck.discard(dyn)
            self.log(f"💥💥💥 폭발!! {p.name}이(가) 3 피해를 받았다!!")
            self._apply_damage(None, p, 3)
        else:
            # 다음 플레이어에게 전달 (end_turn에서 처리)
            self.log(f"  불발. 다이너마이트가 계속 돈다...")
            p.unequip(dyn)
            next_idx = self.state.next_player_index(self.state.players.index(p))
            next_p   = self.state.players[next_idx]
            next_p.equip(dyn)
            self.log(f"  💣 다이너마이트가 {next_p.name}에게 전달되었다.")

    def _pass_dynamite_if_needed(self, player: Player):
        pass  # 다이너마이트 전달은 _resolve_dynamite에서 처리

    # ── Jail ─────────────────────────────────────────────────
    def _resolve_jail(self, p: Player) -> bool:
        """감옥 탈출 판정. ♥ 뒤집으면 탈출."""
        card = self.state.deck.pop_top()
        if card is None:
            return True
        self.state.deck.discard(card)
        escaped = card.draw_check_is_hit()
        self.log(f"⛓️  {p.name} 감옥 탈출 판정: {card} → {'탈출!' if escaped else '실패...'}")

        if p.ability == "lucky_duke":
            card2 = self.state.deck.pop_top()
            if card2:
                self.state.deck.discard(card2)
                self.log(f"  🎲 Lucky Duke: {card2}")
                escaped = escaped or card2.draw_check_is_hit()

        # 감옥 카드 버리기
        jail_card = p.get_equipment(CardType.JAIL) if p.in_jail else None
        if jail_card:
            p.unequip(jail_card)
            self.state.deck.discard(jail_card)

        return escaped

    # ── Suzy Lafayette 트리거 ────────────────────────────────
    def _check_suzy_lafayette(self, p: Player):
        if p.ability == "suzy_lafayette" and len(p.hand) == 0:
            card = self.state.deck.pop_top()
            if card:
                p.add_card(card)
                self.log(f"  🃏 Suzy Lafayette: 패가 비어 자동 드로우 {card}")

    # ── Sid Ketchum 능력 (능동 사용) ─────────────────────────
    def use_sid_ketchum(self, p: Player, c1: Card, c2: Card) -> bool:
        if p.ability != "sid_ketchum":
            return False
        if c1 not in p.hand or c2 not in p.hand:
            return False
        p.remove_card(c1)
        p.remove_card(c2)
        self.state.deck.discard(c1)
        self.state.deck.discard(c2)
        p.gain_hp(1)
        self.log(f"💉 Sid Ketchum: {p.name}이(가) 카드 2장을 버려 HP 회복 ({p.hp}/{p.max_hp})")
        return True
