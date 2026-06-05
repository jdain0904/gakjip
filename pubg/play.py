"""PUBG 보드게임 — 플레이어 대 AI (or AI vs AI 시뮬레이션)."""
from __future__ import annotations
import time

from .environment import GameEnv, ACTION_MOVE, ACTION_USE_CARD, ACTION_PASS
from .visualize import (
    render_state, print_log, print_actions, show_winner, clear
)
from . import ai as ai_module

RESET  = "\033[0m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"


def pause(msg: str = "  [Enter 키를 누르세요...]"):
    input(f"{msg}")


# ── 인간 입력 ─────────────────────────────────────────────────────────────────

def human_pick_action(env: GameEnv) -> dict:
    actions = env.get_valid_actions()
    render_state(env)
    print_actions(actions)

    while True:
        raw = input(f"\n  >> ").strip()
        if raw == "0":
            return {"type": ACTION_PASS, "label": "패스"}
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(actions):
                act = actions[idx]
                if act.get("usable") is False:
                    print(f"  {RED}사거리가 부족합니다. 먼저 접근하세요.{RESET}")
                    continue
                return act
        except ValueError:
            pass
        print(f"  1~{len(actions)} 또는 0(패스)을 입력하세요.")


# ── 게임 루프 ─────────────────────────────────────────────────────────────────

def play_game(env: GameEnv, ai_delay: float = 0.6) -> None:
    """메인 게임 루프."""
    env.reset()

    while not env.done:
        p = env.current_player()

        if p.is_human:
            action = human_pick_action(env)
        else:
            render_state(env)
            print(f"\n  {YELLOW}[{p.name} AI 행동 중...]{RESET}")
            time.sleep(ai_delay)
            action = ai_module.choose_action(env)
            print(f"  선택: {action['label']}")
            time.sleep(ai_delay * 0.8)

        state, done = env.step(action)

        # 로그 출력
        lines = env.flush_log()
        render_state(env)
        print_log(lines)

        if not done:
            if p.is_human:
                pause()
            else:
                time.sleep(ai_delay)

    show_winner(env)
    pause("  [Enter로 종료]")


# ── AI vs AI 시뮬레이션 ───────────────────────────────────────────────────────

def simulate(n: int = 5, verbose: bool = True) -> dict:
    """AI vs AI n판 시뮬레이션. 통계 반환."""
    results = {"p1": 0, "p2": 0, "draw": 0}

    for game_num in range(1, n + 1):
        env = GameEnv("AI-1", "AI-2", p1_human=False, p2_human=False)
        env.reset()

        while not env.done:
            action = ai_module.choose_action(env)
            env.step(action)

        if env.winner:
            if env.winner.pid == 0:
                results["p1"] += 1
            else:
                results["p2"] += 1
        else:
            results["draw"] += 1

        if verbose:
            w = env.winner.name if env.winner else "무승부"
            print(f"게임 {game_num:3d}: 승자={w:10s}  턴={env.turn}")

    return results


# ── 진입점 ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    clear()
    print(f"\n  {BOLD}=== PUBG 보드게임 ==={RESET}")
    print("  1. 플레이어 vs AI")
    print("  2. AI vs AI 시뮬레이션 (5판)")
    choice = input("  선택 [1/2]: ").strip()

    if choice == "2":
        print("\n  AI vs AI 시뮬레이션 시작...\n")
        res = simulate(5, verbose=True)
        print(f"\n  결과: AI-1 {res['p1']}승  AI-2 {res['p2']}승  무승부 {res['draw']}")
    else:
        env = GameEnv("플레이어", "AI", p1_human=True, p2_human=False)
        play_game(env)
