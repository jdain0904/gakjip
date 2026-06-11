#!/usr/bin/env python3
"""PUBG 보드게임 — 진입점 (맵 선택 포함)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pubg.play import play_game, simulate, clear
from pubg.environment import GameEnv
from pubg.maps import ALL_MAPS, draw_map_selection_screen
from pubg.visualize import set_map

BOLD   = "\033[1m"
YELLOW = "\033[93m"
WHITE  = "\033[97m"
DIM    = "\033[2m"
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


def _pick_map():
    """맵 선택 화면 표시 후 MapConfig 반환."""
    clear()
    print(TITLE)
    draw_map_selection_screen()

    while True:
        raw = input("  맵 선택 [1-4] >> ").strip()
        if raw in ("1", "2", "3", "4"):
            idx = int(raw) - 1
            return ALL_MAPS[idx]
        print(f"  {DIM}1~4 중 하나를 입력하세요.{RESET}")


def main():
    # ── 맵 선택 ──────────────────────────────────────────────────────────────
    selected_map = _pick_map()
    set_map(selected_map)

    # ── 게임 모드 선택 ────────────────────────────────────────────────────────
    clear()
    mc = selected_map
    print(f"\n  {BOLD}{mc.col_title}[ {mc.name_ko}  {mc.name_en} ]{RESET}  {mc.desc}\n")
    print(f"  {BOLD}게임 모드 선택{RESET}")
    print(f"  {WHITE}1. 플레이어 vs AI{RESET}")
    print(f"  {WHITE}2. AI vs AI 시뮬레이션{RESET}")
    print(f"  {DIM}3. 종료{RESET}")

    choice = input("\n  선택 >> ").strip()

    if choice == "1":
        name = input("  플레이어 이름 (Enter=플레이어): ").strip() or "플레이어"
        env  = GameEnv(name, "AI", p1_human=True, p2_human=False,
                       map_config=selected_map)
        play_game(env)

    elif choice == "2":
        n_str = input("  몇 판? [기본 5]: ").strip()
        n     = int(n_str) if n_str.isdigit() else 5
        print(f"\n  {n}판 시뮬레이션 시작...\n")
        res = simulate(n, verbose=True, map_config=selected_map)
        print(f"\n  결과: AI-1 {res['p1']}승  AI-2 {res['p2']}승  무승부 {res['draw']}")
        input("\n  [Enter로 종료]")

    else:
        print("  종료합니다.")


if __name__ == "__main__":
    main()
