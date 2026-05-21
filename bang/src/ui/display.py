"""터미널 UI — 인스크립션+서부 테마."""
import os
import time
import random
from typing import List, Optional

from ..cards.card import Card, CardType, RoleType
from ..game.player import Player
from ..game.game_state import GameState
from .ascii_art import (
    TITLE, SALOON_DIVIDER, BULLET_FULL, BULLET_EMPTY,
    CARD_ICONS, ROLE_ART, INTRO_LINES, DEATH_LINES,
    WINNER_SHERIFF, WINNER_OUTLAW, WINNER_RENEGADE,
)

# ── ANSI 색상 ──────────────────────────────────────────────
RESET  = "\033[0m"
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
DIM    = "\033[2m"
BOLD   = "\033[1m"
GRAY   = "\033[90m"


def clear():
    os.system("clear" if os.name == "posix" else "cls")


def pause(msg: str = "  [Enter 키를 누르세요...]"):
    input(f"{DIM}{msg}{RESET}")


def slow_print(text: str, delay: float = 0.03):
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()


def show_title():
    clear()
    print(f"{YELLOW}{TITLE}{RESET}")
    time.sleep(0.5)
    slow_print(f"  {random.choice(INTRO_LINES)}", delay=0.04)
    print()


def show_events(events: List[str]):
    for e in events:
        _print_event(e)
    if events:
        time.sleep(0.3)


def _print_event(msg: str):
    if "☠️" in msg or "사망" in msg or "황천" in msg:
        print(f"  {RED}{msg}{RESET}")
    elif "💥" in msg or "피해" in msg or "폭발" in msg:
        print(f"  {RED}{msg}{RESET}")
    elif "💨" in msg or "피했다" in msg:
        print(f"  {CYAN}{msg}{RESET}")
    elif "🔫" in msg or "BANG!" in msg:
        print(f"  {YELLOW}{msg}{RESET}")
    elif "🍺" in msg or "맥주" in msg or "HP" in msg:
        print(f"  {GREEN}{msg}{RESET}")
    else:
        print(f"  {WHITE}{msg}{RESET}")


# ── 게임 보드 출력 ─────────────────────────────────────────
def show_board(state: GameState, human: Player):
    clear()
    print(f"{YELLOW}  ☠  DEAD MAN'S SALOON — 턴 {state.turn_number}  ☠{RESET}")
    print(f"  {DIM}덱:{len(state.deck)} 장{RESET}")
    print()

    alive = state.alive_players()
    for p in alive:
        _show_player_status(p, is_current=(p == state.current_player), is_human=(p == human))

    print()
    print(SALOON_DIVIDER)
    print()


def _show_player_status(p: Player, is_current: bool, is_human: bool):
    # HP 바
    hp_bar = (BULLET_FULL * p.hp) + (BULLET_EMPTY * (p.max_hp - p.hp))

    # 역할 공개 조건: 셰리프는 항상 공개, 자기 자신은 공개
    reveal = p.is_sheriff or is_human
    role_str  = f"{ROLE_ART.get(p.role_type.value if p.role_type else '?', '?')} {p.role}" if reveal else "? [미공개]"
    char_str  = f"{p.character.name}" if p.character else "?"

    # 장비
    equip_icons = " ".join(CARD_ICONS.get(e.card_type.value, "?") for e in p.equipment)

    # 감옥/죽음 상태
    status = ""
    if not p.is_alive:
        status = f" {RED}[사망]{RESET}"
    elif p.in_jail:
        status = f" ⛓️ [감옥]"

    tag = f"{CYAN}► {RESET}" if is_current else "  "
    you = f"{GREEN}(YOU){RESET}" if is_human else ""

    print(f"{tag}{BOLD}{p.name}{RESET} {you}{status}")
    print(f"     {role_str}  |  {char_str}")
    print(f"     {RED}{hp_bar}{RESET} ({p.hp}/{p.max_hp}HP)  {equip_icons}")
    print()


# ── 인간 플레이어 핸드 출력 ──────────────────────────────────
def show_hand(player: Player):
    print(f"  {BOLD}[ 당신의 패 ]{RESET}")
    if not player.hand:
        print(f"  {DIM}(없음){RESET}")
    for i, card in enumerate(player.hand):
        icon = CARD_ICONS.get(card.card_type.value, "  ")
        is_blue = card.card_type.is_blue()
        color   = CYAN if is_blue else WHITE
        print(f"  {color}[{i+1}] {icon} {card}{RESET}")
    print()


def show_equipment(player: Player):
    if player.equipment:
        print(f"  {BOLD}[ 장비 ]{RESET}")
        for e in player.equipment:
            icon = CARD_ICONS.get(e.card_type.value, "  ")
            print(f"  {CYAN}{icon} {e}{RESET}")
        print()


# ── 메뉴 입력 헬퍼 ────────────────────────────────────────
def prompt_int(msg: str, lo: int, hi: int, allow_zero: bool = False) -> int:
    while True:
        raw = input(f"  {YELLOW}{msg}{RESET} ").strip()
        if allow_zero and raw == "0":
            return 0
        try:
            n = int(raw)
            if lo <= n <= hi:
                return n
        except ValueError:
            pass
        print(f"  {RED}잘못된 입력입니다. {lo}~{hi} 사이 숫자를 입력하세요.{RESET}")


def choose_card(player: Player, prompt: str = "사용할 카드 번호 (0=패스):") -> Optional[Card]:
    if not player.hand:
        return None
    show_hand(player)
    idx = prompt_int(prompt, 0, len(player.hand), allow_zero=True)
    if idx == 0:
        return None
    return player.hand[idx - 1]


def choose_target(targets: List[Player], prompt: str = "대상 번호:") -> Optional[Player]:
    if not targets:
        return None
    print(f"  {BOLD}[ 대상 선택 ]{RESET}")
    for i, p in enumerate(targets):
        hp_bar = BULLET_FULL * p.hp + BULLET_EMPTY * (p.max_hp - p.hp)
        print(f"  [{i+1}] {p.name}  {RED}{hp_bar}{RESET}")
    print(f"  [0] 취소")
    idx = prompt_int(prompt, 0, len(targets), allow_zero=True)
    if idx == 0:
        return None
    return targets[idx - 1]


# ── 승리 화면 ─────────────────────────────────────────────
def show_winner(winner_team: str, players: List[Player]):
    clear()
    if winner_team == "SHERIFF":
        print(f"{GREEN}{WINNER_SHERIFF}{RESET}")
    elif winner_team == "OUTLAW":
        print(f"{RED}{WINNER_OUTLAW}{RESET}")
    elif winner_team == "RENEGADE":
        print(f"{YELLOW}{WINNER_RENEGADE}{RESET}")

    print(f"  {BOLD}[ 최후 결과 ]{RESET}")
    for p in players:
        status = "생존" if p.is_alive else "사망"
        role   = p.role.role.value if p.role else "?"
        icon   = ROLE_ART.get(role, "?")
        print(f"  {icon} {p.name:12s} [{role}] — {status}")
    print()


# ── 캐릭터 카드 정보 표시 ─────────────────────────────────
def show_character_info(player: Player):
    if not player.character:
        return
    c = player.character
    print(f"  {CYAN}캐릭터: {BOLD}{c.name}{RESET}  HP: {c.base_hp}")
    print(f"  {DIM}{c.description}{RESET}")
    print()


# ── 게임 시작 화면 ────────────────────────────────────────
def show_game_start(players: List[Player], human: Player):
    clear()
    print(f"{YELLOW}  ═══ 게임 시작 ═══{RESET}\n")
    print(f"  {len(players)}명이 황야에 모였다...\n")
    for p in players:
        reveal = p == human or p.is_sheriff
        role_str = f"{p.role}" if reveal else "????"
        print(f"  {p.name:12s}  역할: {role_str:12s}  캐릭터: {p.character}")
    print()
    show_character_info(human)
    pause("  준비됐으면 Enter를 누르세요...")
