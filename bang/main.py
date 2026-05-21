#!/usr/bin/env python3
"""Bang! — Dead Man's Saloon 진입점."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.game.player import Player
from src.game.game_state import GameState
from src.game.game_engine import GameEngine
from src.game.ai import AI
from src.game.human_turn import HumanTurn
from src.ui import display as ui

AI_NAMES = [
    "Doc Holliday", "Jesse James", "Billy the Kid",
    "Wyatt Earp",   "Belle Starr",  "Calamity Jane",
]


def setup_game(num_players: int) -> tuple:
    """플레이어 생성 및 게임 상태 초기화."""
    human = Player(0, "You", is_human=True)
    ai_players = [
        Player(i + 1, AI_NAMES[i], is_human=False)
        for i in range(num_players - 1)
    ]
    players = [human] + ai_players
    state   = GameState(players)
    return human, state


def run_game(state: GameState, human: Player):
    engine     = GameEngine(state)
    ai         = AI(engine)
    human_turn = HumanTurn(engine)

    ui.show_game_start(state.players, human)

    while not state.game_over:
        current = state.current_player

        # ── 턴 시작 (다이너마이트, 감옥, 드로우) ─────────────
        evts = engine.start_turn()
        ui.show_events(evts)

        if state.game_over:
            break

        if not current.is_alive:
            state.advance_turn()
            continue

        # ── 플레이 페이즈 ──────────────────────────────────────
        if current.is_human:
            evts = human_turn.play_phase(current)
        else:
            ui.show_board(state, human)
            print(f"\n  {ui.YELLOW}[{current.name}의 턴]{ui.RESET}")
            evts = ai.take_turn(current)
            ui.show_events(evts)
            ui.pause(f"  [{current.name}의 턴 종료 — Enter]")

        if state.game_over:
            break

        # ── 턴 종료 ────────────────────────────────────────────
        evts = engine.end_turn(current)
        ui.show_events(evts)

    # ── 게임 종료 ──────────────────────────────────────────────
    ui.show_winner(state.winner_team or "UNKNOWN", state.players)
    ui.pause("  [Enter로 종료]")


def ask_player_count() -> int:
    print(f"\n  {ui.YELLOW}몇 명이 황야에 모일까요? (4~7명){ui.RESET}")
    while True:
        raw = input("  >> ").strip()
        try:
            n = int(raw)
            if 4 <= n <= 7:
                return n
        except ValueError:
            pass
        print("  4~7 사이 숫자를 입력하세요.")


def main():
    ui.show_title()
    num_players = ask_player_count()
    human, state = setup_game(num_players)
    run_game(state, human)


if __name__ == "__main__":
    main()
