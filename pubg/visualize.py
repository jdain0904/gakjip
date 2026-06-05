"""텍스트 기반 게임 시각화 (matplotlib 불필요)."""
from __future__ import annotations
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .environment import GameEnv

RESET  = "\033[0m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GRAY   = "\033[90m"


def clear():
    os.system("clear" if os.name == "posix" else "cls")


def hp_bar(hp: int, max_hp: int = 100, width: int = 20) -> str:
    filled = max(0, int(hp / max_hp * width))
    color  = RED if hp < 30 else (YELLOW if hp < 60 else GREEN)
    return f"{color}{'█' * filled}{'░' * (width - filled)}{RESET} {hp}/{max_hp}"


def distance_bar(distance: int, max_dist: int = 50, width: int = 40) -> str:
    """두 플레이어의 위치를 가로 막대로 표시."""
    ratio = min(1.0, distance / max_dist)
    p2_pos = int(ratio * (width - 2))
    bar = list("·" * width)
    bar[0]      = "P"   # P1
    bar[p2_pos] = "E"   # P2(적)
    return f"[{''.join(bar)}]"


def render_state(env: "GameEnv"):
    clear()
    t      = env.turn
    dist   = env.distance
    safe   = max(0, 100 - 10 * t)
    zone_w = RED if dist > safe else GREEN

    print(f"{YELLOW}{BOLD}  ━━━ PUBG 보드게임 ━━━  턴 {t}{RESET}")
    print(f"  거리: {CYAN}{dist}{RESET}  |  자기장 안전거리: {zone_w}{safe}{RESET}")
    print(f"  {distance_bar(dist)}")
    print()

    for p in [env.p1, env.p2]:
        tag    = f"{GREEN}◀ 행동 중{RESET}" if p.pid == env.cur_pid else ""
        print(f"  {BOLD}{p.name}{RESET} {tag}")
        print(f"  HP  {hp_bar(p.hp)}")
        effs = ", ".join(e.kind for e in p.effects) if p.effects else "없음"
        print(f"  효과: {DIM}{effs}{RESET}")
        _print_inventory(p)
        print()

    print(f"  {DIM}{'─'*50}{RESET}")


def _print_inventory(p):
    inv = p.inventory
    if not inv:
        print(f"  인벤토리: (없음)")
        return
    print(f"  인벤토리 ({len(inv)}개):")
    for i, item in enumerate(inv):
        print(f"    [{i+1}] {item}")


def print_log(lines: list[str]):
    if not lines:
        return
    print()
    for line in lines:
        if any(k in line for k in ("💥", "즉사", "사망", "HP 0")):
            print(f"  {RED}{line}{RESET}")
        elif any(k in line for k in ("💊", "회복", "+", "HP")):
            print(f"  {GREEN}{line}{RESET}")
        elif any(k in line for k in ("🔫", "공격", "사격")):
            print(f"  {YELLOW}{line}{RESET}")
        elif any(k in line for k in ("📦", "획득")):
            print(f"  {CYAN}{line}{RESET}")
        elif "🏆" in line:
            print(f"  {BOLD}{GREEN}{line}{RESET}")
        else:
            print(f"  {WHITE}{line}{RESET}")


def print_actions(actions: list[dict]) -> None:
    print(f"\n  {BOLD}[ 행동 선택 ]{RESET}")
    for i, act in enumerate(actions):
        usable  = act.get("usable", True)
        color   = DIM if usable is False else WHITE
        blocked = f" {RED}(사거리 부족){RESET}" if usable is False else ""
        print(f"  {color}[{i+1}] {act['label']}{RESET}{blocked}")
    print(f"  [0] 패스 / 종료")


def show_winner(env: "GameEnv"):
    clear()
    w = env.winner
    print(f"\n  {BOLD}{YELLOW}{'━'*45}{RESET}")
    if w:
        print(f"  🏆  {BOLD}{GREEN}{w.name} 승리!{RESET}")
    else:
        print(f"  무승부")
    print(f"  {BOLD}{YELLOW}{'━'*45}{RESET}\n")
    print(f"  총 {env.turn}턴")
    for p in [env.p1, env.p2]:
        alive = "생존" if p.is_alive else "사망"
        print(f"  {p.name}: HP {p.hp}  [{alive}]")
    print()
