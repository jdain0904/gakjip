"""
PUBG Miramar 스타일 터미널 UI
- 2D 사막 지형 + 플레이어 위치 표시
- PUBG HUD (HP바, 인벤토리, 자기장 게이지)
- Kill feed 스타일 이벤트 로그
- matplotlib 불필요
"""
import os
import re
import random as _rng

# ── ANSI 색상 ─────────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
BLINK   = "\033[5m"

SAND    = "\033[38;5;214m"   # 모래 (주황)
SAND_D  = "\033[33m"         # 모래 (어두운 황색, fallback)
ROCK    = "\033[38;5;240m"   # 바위 (어두운 회색)
BUILD   = "\033[38;5;252m"   # 건물 (밝은 회색)
ROAD    = "\033[38;5;238m"   # 도로
ZONEC   = "\033[94m"         # 자기장 (파랑)
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
ORANGE  = "\033[38;5;208m"

P1C     = "\033[92;1m"       # 아군: 굵은 초록
P2C     = "\033[91;1m"       # 적:   굵은 빨강

# ── 레이아웃 상수 ──────────────────────────────────────────────────────────────
BOX_W     = 72        # 전체 박스 너비 (테두리 포함)
INNER_W   = BOX_W - 2 # 내부 너비 = 70
TW        = INNER_W   # 지형 너비 = 70
TH        = 9         # 지형 행 수
PROW      = 4         # 플레이어 행 (0-indexed)

# 플레이어 초기 위치 & 이동 범위
P1_INIT   = 4
P2_INIT   = TW - 5    # = 65
TRAVEL    = (TW // 2) - P1_INIT - 3   # ≈ 28

# ── 지형 생성 (고정 시드 → 항상 같은 Miramar) ─────────────────────────────────
def _build_terrain() -> list[list[str]]:
    rng = _rng.Random(7777)
    grid = [['.'] * TW for _ in range(TH)]

    for r in range(TH):
        for c in range(TW):
            v = rng.random()
            if v < 0.15:   grid[r][c] = '~'   # 거친 모래
            elif v < 0.20: grid[r][c] = '^'   # 언덕

    def box(r, c, iw, ih=3):
        ew = iw + 2
        for dr in range(ih):
            for dc in range(ew):
                nr, nc = r + dr, c + dc
                if 0 <= nr < TH and 0 <= nc < TW:
                    if dr == 0:
                        grid[nr][nc] = '╔' if dc == 0 else ('╗' if dc == ew-1 else '═')
                    elif dr == ih - 1:
                        grid[nr][nc] = '╚' if dc == 0 else ('╝' if dc == ew-1 else '═')
                    else:
                        grid[nr][nc] = '║' if dc in (0, ew-1) else ' '

    # El Pozo 구역 (좌)
    box(0, 2,  3); box(5, 1, 2); box(2, 7, 2)
    # Los Leones 구역 (중앙)
    box(0, 31, 5); box(6, 29, 4); box(3, 33, 3)
    # Pecado 구역 (우)
    box(0, 61, 3); box(5, 62, 2); box(2, 55, 2)
    # 소형 건물
    box(1, 17, 2); box(7, 46, 2); box(3, 22, 2); box(6, 14, 2)

    return grid


_BASE = _build_terrain()


def _ansi_len(s: str) -> int:
    return len(re.sub(r'\033\[[^m]*m', '', s))


def _pad_to(s: str, width: int, fill: str = ' ') -> str:
    return s + fill * max(0, width - _ansi_len(s))


def _color_ch(ch: str) -> str:
    if ch in '╔═╗║╚╝':
        return f"{BUILD}{ch}{RESET}"
    if ch == ' ':
        return ' '
    if ch == '^':
        return f"{ROCK}▲{RESET}"
    if ch == '~':
        return f"{SAND}≈{RESET}"
    return f"{DIM}{SAND_D}.{RESET}"


# ── 지형 + 플레이어 렌더 ──────────────────────────────────────────────────────
def _render_map(env) -> list[str]:
    from .environment import INITIAL_DISTANCE
    dist  = max(0, env.distance)
    ratio = min(1.0, (INITIAL_DISTANCE - dist) / INITIAL_DISTANCE)

    p1c = P1_INIT + int(ratio * TRAVEL)
    p2c = P2_INIT - int(ratio * TRAVEL)
    if p1c >= p2c - 1:   # 충돌 방지
        p1c, p2c = p2c - 2, p2c

    # 자기장 경계 열
    safe = max(0, 100 - 10 * env.turn)
    in_zone = dist > safe
    z_left  = max(0, int((1 - safe / INITIAL_DISTANCE) * (TW // 2 - 4)))
    z_right = min(TW - 1, TW - 1 - int((1 - safe / INITIAL_DISTANCE) * (TW // 2 - 4)))

    lines = []
    for ri, row in enumerate(_BASE):
        buf = []
        for ci, ch in enumerate(row):
            # 자기장 경계 세로선
            if in_zone and safe < INITIAL_DISTANCE and (ci == z_left or ci == z_right):
                buf.append(f"{BLINK}{ZONEC}│{RESET}")
                continue
            # 플레이어 마커
            if ri == PROW:
                if ci == p1c:
                    icon = '◉' if env.p1.is_alive else '✕'
                    buf.append(f"{P1C}{icon}{RESET}")
                    continue
                if ci == p2c:
                    icon = '◎' if env.p2.is_alive else '✕'
                    buf.append(f"{P2C}{icon}{RESET}")
                    continue
            buf.append(_color_ch(ch))
        lines.append(''.join(buf))
    return lines


# ── HP 바 ─────────────────────────────────────────────────────────────────────
def _hp_bar(hp: int, w: int = 18) -> str:
    pct    = max(0, hp / 100)
    filled = int(pct * w)
    empty  = w - filled
    c      = GREEN if pct > 0.6 else (YELLOW if pct > 0.3 else RED)
    bar    = f"{BOLD}{c}{'█' * filled}{'░' * empty}{RESET}"
    return f"{bar} {hp:>3}/100"


# ── 인벤토리 한 줄 요약 ───────────────────────────────────────────────────────
def _inv_line(player, max_w: int = 32) -> str:
    from .items   import Weapon, Supply, Vehicle
    from .cards   import HouseCard, SupplyDropCard
    parts = []
    for item in player.inventory:
        if isinstance(item, Weapon):
            parts.append(f"🔫{item.name}")
        elif isinstance(item, SupplyDropCard):
            parts.append(f"★보급[{item.roll}]")
        elif isinstance(item, HouseCard):
            parts.append(f"🏠[{item.roll}]")
        elif isinstance(item, Supply):
            parts.append(f"💊{item.name}")
        elif isinstance(item, Vehicle):
            parts.append(f"🚗{item.name}")
    joined = " ".join(parts) if parts else "(없음)"
    # 텍스트 길이 제한 (ANSI 없으므로 그냥 자름)
    if len(joined) > max_w:
        joined = joined[:max_w-1] + "…"
    return joined


# ── 박스 유틸 ─────────────────────────────────────────────────────────────────
def _top() -> str:
    return f"{SAND_D}╔{'═' * (BOX_W-2)}╗{RESET}"

def _bot() -> str:
    return f"{SAND_D}╚{'═' * (BOX_W-2)}╝{RESET}"

def _div(lc='╠', mc='═', rc='╣') -> str:
    return f"{SAND_D}{lc}{mc * (BOX_W-2)}{rc}{RESET}"

def _row(content: str) -> str:
    pad = INNER_W - _ansi_len(content)
    return f"{SAND_D}║{RESET}{content}{' ' * max(0, pad)}{SAND_D}║{RESET}"

def _split_div() -> str:
    h = INNER_W // 2
    return f"{SAND_D}╠{'═'*h}╦{'═'*(INNER_W-h-1)}╣{RESET}"

def _split_bot() -> str:
    h = INNER_W // 2
    return f"{SAND_D}╠{'═'*h}╩{'═'*(INNER_W-h-1)}╣{RESET}"

def _split_row(left: str, right: str) -> str:
    h = INNER_W // 2
    l_pad = h       - _ansi_len(left)
    r_pad = INNER_W - h - 1 - _ansi_len(right)
    return (f"{SAND_D}║{RESET}{left}{' '*max(0,l_pad)}"
            f"{SAND_D}║{RESET}{right}{' '*max(0,r_pad)}"
            f"{SAND_D}║{RESET}")


# ── 자기장 게이지 바 ──────────────────────────────────────────────────────────
def _zone_bar(safe: int, max_safe: int = 50, w: int = 40) -> str:
    ratio  = max(0, safe / max_safe)
    filled = int(ratio * w)
    empty  = w - filled
    return (f"{ZONEC}{'▰' * filled}{DIM}{'▱' * empty}{RESET}")


# ── 이벤트 로그 한 줄 색상 ──────────────────────────────────────────────────
def _log_color(msg: str) -> str:
    if any(k in msg for k in ("💥","즉사","사망","HP 0","승리","🏆")):
        return f"{RED}{msg}{RESET}"
    if any(k in msg for k in ("💊","회복","heal","+")):
        return f"{GREEN}{msg}{RESET}"
    if any(k in msg for k in ("🔫","공격","발사")):
        return f"{YELLOW}{msg}{RESET}"
    if any(k in msg for k in ("📦","획득","개봉")):
        return f"{CYAN}{msg}{RESET}"
    if any(k in msg for k in ("🌀","자기장")):
        return f"{ZONEC}{msg}{RESET}"
    if "💣" in msg:
        return f"{ORANGE}{msg}{RESET}"
    if "🚶" in msg or "이동" in msg:
        return f"{SAND_D}{msg}{RESET}"
    return f"{DIM}{WHITE}{msg}{RESET}"


# ── 메인 render_state ─────────────────────────────────────────────────────────
def render_state(env):
    clear()
    from .environment import INITIAL_DISTANCE

    dist   = env.distance
    turn   = env.turn
    safe   = max(0, 100 - 10 * turn)
    danger = dist > safe

    # ── 타이틀 바 ──────────────────────────────────────────────────────────
    title  = f" {BOLD}{ORANGE}🏜  M I R A M A R{RESET}  {DIM}Battle Royale{RESET}"
    tinfo  = f"{SAND_D}턴:{RESET}{BOLD}{turn}{RESET}  {SAND_D}거리:{RESET}{BOLD}{CYAN}{dist}{RESET}"
    zinfo  = (f"{RED}{BLINK}⚠ 자기장!{RESET}  " if danger else "") + \
             f"{ZONEC}안전:{safe}칸{RESET}"
    header = f"{title}  {tinfo}  {zinfo}"

    print(_top())
    print(_row(f" {header}"))

    # ── 자기장 게이지 ───────────────────────────────────────────────────────
    zone_bar   = _zone_bar(safe)
    zone_label = f" {ZONEC}ZONE{RESET} {zone_bar} {BOLD}{safe:>3}{RESET}m "
    print(_row(zone_label))
    print(_div())

    # ── 지도 ───────────────────────────────────────────────────────────────
    map_lines = _render_map(env)

    # 범례 (지도 오른쪽 위 2줄에 오버레이)
    legend = [
        f"{P1C}◉{RESET}={env.p1.name}  {P2C}◎{RESET}={env.p2.name}",
        f"{SAND}≈{RESET}모래 {ROCK}▲{RESET}언덕 {BUILD}╔╗{RESET}건물",
    ]
    for li, line in enumerate(map_lines):
        leg = ""
        if li < len(legend):
            leg_str  = f" {legend[li]}"
            line_len = _ansi_len(line)
            leg_len  = _ansi_len(leg_str)
            # 범례를 오른쪽에 붙이기 위해 line을 앞부분만 사용
            available = INNER_W - leg_len
            if line_len <= available:
                line = _pad_to(line, available) + leg_str
            # 아니면 line 그대로
        pad = INNER_W - _ansi_len(line)
        print(f"{SAND_D}║{RESET}{line}{' '*max(0,pad)}{SAND_D}║{RESET}")

    print(_div())

    # ── HUD: 두 플레이어 나란히 ────────────────────────────────────────────
    def p_header(p) -> str:
        c    = P1C if p.pid == 0 else P2C
        tag  = "🧍" if p.is_human else "🤖"
        dead = f" {RED}[사망]{RESET}" if not p.is_alive else ""
        return f" {tag} {c}{BOLD}{p.name}{RESET}{dead}"

    def p_hp(p) -> str:
        c = P1C if p.pid == 0 else P2C
        return f" {c}❤{RESET}  {_hp_bar(p.hp)}"

    def p_inv(p) -> str:
        return f" 🎒 {_inv_line(p, max_w=28)}"

    def p_eff(p) -> str:
        effs = ", ".join(e.kind for e in p.effects)
        color = YELLOW if effs else DIM
        return f" ✨ {color}{effs or '없음'}{RESET}"

    print(_split_div())
    for row_fn in [p_header, p_hp, p_inv, p_eff]:
        print(_split_row(row_fn(env.p1), row_fn(env.p2)))
    print(_split_bot())

    # ── Kill Feed / 이벤트 로그 ─────────────────────────────────────────────
    log_hdr = f" {BOLD}[ KILL FEED / 이벤트 ]{RESET}"
    print(_row(log_hdr))

    recent = env.log[-4:] if env.log else []
    if not recent:
        print(_row(f"  {DIM}(없음){RESET}"))
    for msg in recent:
        truncated = msg[:INNER_W - 4] + ("…" if len(msg) > INNER_W - 4 else "")
        print(_row(f"  ▶ {_log_color(truncated)}"))

    print(_bot())


# ── 공개 유틸 ─────────────────────────────────────────────────────────────────
def clear():
    os.system("clear" if os.name == "posix" else "cls")


def print_log(lines: list[str]):
    if not lines:
        return
    for msg in lines:
        print(f"  {_log_color(msg)}")


def print_actions(actions: list[dict]):
    h = INNER_W // 2
    print(f"\n  {BOLD}[ 행동 선택 ]{RESET}  {DIM}(0=패스){RESET}")
    print(f"  {SAND_D}{'─'*(BOX_W-4)}{RESET}")
    for i, act in enumerate(actions):
        usable = act.get("usable", True)
        if usable is False:
            label = f"{DIM}{act['label']}{RESET}  {RED}❌사거리부족{RESET}"
        else:
            label = f"{WHITE}{act['label']}{RESET}"
        print(f"  [{i+1}] {label}")
    print(f"  {SAND_D}{'─'*(BOX_W-4)}{RESET}")


def show_winner(env):
    clear()
    w = env.winner
    print(_top())

    if w:
        c   = P1C if w.pid == 0 else P2C
        msg = f"  {BOLD}{'🏆'*3}  {c}{w.name} 승리! {RESET}{'🏆'*3}"
    else:
        msg = f"  {DIM}무승부{RESET}"

    print(_row(msg))
    print(_div())
    print(_row(f"  {DIM}총 {env.turn}턴 진행{RESET}"))

    for p in [env.p1, env.p2]:
        c     = P1C if p.pid == 0 else P2C
        alive = f"{GREEN}생존{RESET}" if p.is_alive else f"{RED}사망{RESET}"
        print(_row(f"  {c}{BOLD}{p.name:12s}{RESET}  HP: {p.hp:>3}  [{alive}]"))

    print(_bot())
