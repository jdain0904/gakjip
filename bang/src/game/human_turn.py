"""인간 플레이어 턴 처리."""
from typing import List, Optional

from ..cards.card import Card, CardType, RoleType
from .player import Player
from .game_state import GameState
from .game_engine import GameEngine
from ..ui import display as ui


class HumanTurn:
    def __init__(self, engine: GameEngine):
        self.engine = engine
        self.state  = engine.state

    def play_phase(self, actor: Player) -> List[str]:
        """인간 플레이어의 플레이 페이즈. 패스 선택까지 반복."""
        all_events: List[str] = []

        while True:
            if self.state.game_over:
                break

            ui.show_board(self.state, actor)
            ui.show_hand(actor)
            ui.show_equipment(actor)
            print(f"  HP: {actor.hp}/{actor.max_hp}  |  패: {len(actor.hand)}장")
            print()

            card = ui.choose_card(actor, "사용할 카드 (0=턴 종료):")
            if card is None:
                break

            ct = card.card_type

            # 대상이 필요한 카드
            target: Optional[Player] = None
            if ct in (CardType.BANG, CardType.DUEL, CardType.PANIC,
                      CardType.CAT_BALOU, CardType.JAIL):
                candidates = self._get_candidates(actor, ct)
                if not candidates:
                    print(f"  사용 가능한 대상이 없습니다.")
                    ui.pause()
                    continue
                target = ui.choose_target(candidates)
                if target is None:
                    continue

            ok, msg = self.engine.play_card(actor, card, target)
            evts = self.engine.flush_events()
            all_events.extend(evts)
            ui.show_events(evts)

            if not ok:
                print(f"  {msg}")
                ui.pause()
            else:
                ui.pause()

        # 패 제한 초과 → 버리기
        self._discard_to_limit(actor, all_events)
        return all_events

    def _get_candidates(self, actor: Player, ct: CardType) -> List[Player]:
        alive = self.state.alive_players()
        others = [p for p in alive if p != actor]

        if ct == CardType.BANG:
            return self.state.targets_in_range(actor)
        elif ct == CardType.DUEL:
            return others
        elif ct == CardType.PANIC:
            return [p for p in others if self.state.distance(actor, p) <= 1]
        elif ct == CardType.CAT_BALOU:
            return others
        elif ct == CardType.JAIL:
            return [p for p in others if not p.is_sheriff and not p.in_jail]
        return others

    def _discard_to_limit(self, actor: Player, all_events: List[str]):
        while len(actor.hand) > actor.hp:
            print(f"\n  패 제한 초과! {len(actor.hand)}장 → {actor.hp}장으로 줄여야 합니다.")
            ui.show_hand(actor)
            card = ui.choose_card(actor, "버릴 카드:")
            if card:
                actor.remove_card(card)
                self.state.deck.discard(card)
                msg = f"  {actor.name}이(가) {card} 버림."
                self.engine.log(msg)
                all_events.append(msg)
