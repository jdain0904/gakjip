#!/usr/bin/env python3
"""PUBG 보드게임 — 진입점."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pubg.play import play_game, simulate, clear
from pubg.environment import GameEnv

BOLD   = "\033[1m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

TITLE = f"""
{YELLOW}
  ██████╗ ██╗   ██╗██████╗  ██████╗
  ██╔══██╗██║   ██║██╔══██╗██╔════╝
  ██████╔╝██║   ██║██████╔╝██║  ███╗
  ██╔═══╝ ██║   ██║██╔══██╗██║   ██║
  ██║     ╚██████╔╝██████╔╝╚██████╔╝
  ╚═╝      ╚═════╝ ╚═════╝  ╚═════╝
  ─────────────────────────────────
  보드게임 배틀로얄
  초기 거리 50  |  HP 100  |  자기장 적용
{RESET}"""


def main():
    clear()
    print(TITLE)
    print("  1. 플레이어 vs AI")
    print("  2. AI vs AI 시뮬레이션")
    print("  3. 종료")
    choice = input("\n  선택 >> ").strip()

    if choice == "1":
        name   = input("  플레이어 이름 (Enter=플레이어): ").strip() or "플레이어"
        env    = GameEnv(name, "AI", p1_human=True, p2_human=False)
        play_game(env)
    elif choice == "2":
        n_str  = input("  몇 판? [기본 5]: ").strip()
        n      = int(n_str) if n_str.isdigit() else 5
        print(f"\n  {n}판 시뮬레이션 시작...\n")
        res    = simulate(n, verbose=True)
        print(f"\n  결과: AI-1 {res['p1']}승  AI-2 {res['p2']}승  무승부 {res['draw']}")
        input("\n  [Enter로 종료]")
    else:
        print("  종료합니다.")


if __name__ == "__main__":
    main()
