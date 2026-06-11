#!/usr/bin/env python3
"""PUBG 보드게임 — 진입점."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pubg.play import play_game, simulate, clear
from pubg.environment import GameEnv
from pubg.maps import ALL_MAPS, draw_map_selection_screen
from pubg.visualize import set_map

BOLD   = "\033[1m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
DIM    = "\033[2m"
RESET  = "\033[0m"
RED    = "\033[91m"

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


def select_map():
    """맵 선택 화면. 선택된 MapConfig 반환."""
    while True:
        draw_map_selection_screen()
        raw = input(f"  {BOLD}맵 선택 [1~4] >> {RESET}").strip()
        if raw in ("1", "2", "3", "4"):
            chosen = ALL_MAPS[int(raw) - 1]
            print(f"\n  {chosen.col_title}{BOLD}▶ {chosen.name_ko}  {chosen.name_en}{RESET}  선택됨")
            return chosen
        print(f"  {RED}1~4 중에서 선택하세요.{RESET}")


def main():
    clear()
    print(TITLE)

    # ── 맵 선택 ───────────────────────────────────────────────────────────────
    selected_map = select_map()
    set_map(selected_map)

    # ── 게임 모드 선택 ────────────────────────────────────────────────────────
    clear()
    c = selected_map.col_title
    print(f"\n  {BOLD}{c}{selected_map.name_ko}  {selected_map.name_en}{RESET}  {DIM}{selected_map.desc}{RESET}\n")
    print(f"  {BOLD}1.{RESET} 플레이어 vs AI")
    print(f"  {BOLD}2.{RESET} AI vs AI 시뮬레이션")
    print(f"  {BOLD}3.{RESET} 맵 다시 선택")
    print(f"  {BOLD}4.{RESET} 종료")
    choice = input(f"\n  {BOLD}선택 >> {RESET}").strip()

    if choice == "1":
        name = input("  플레이어 이름 (Enter=플레이어): ").strip() or "플레이어"
        env  = GameEnv(name, "AI", p1_human=True, p2_human=False,
                       map_config=selected_map)
        play_game(env)

    elif choice == "2":
        n_str = input("  몇 판? [기본 5]: ").strip()
        n     = int(n_str) if n_str.isdigit() else 5
        print(f"\n  {n}판 시뮬레이션 시작 ({selected_map.name_ko})...\n")
        res = simulate(n, verbose=True, map_config=selected_map)
        print(f"\n  결과: AI-1 {res['p1']}승  AI-2 {res['p2']}승  무승부 {res['draw']}")
        input("\n  [Enter로 종료]")

    elif choice == "3":
        main()

    else:
        print("  종료합니다.")


if __name__ == "__main__":
    main()
