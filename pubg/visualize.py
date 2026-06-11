"""
PUBG 멀티맵 터미널 UI
- 4개 맵 테마 (비켄디/에란겔/사녹/미라마)
- MapConfig 기반 색상/기호 동적 적용
- 카드 드로우 애니메이션 (유희왕 마스터듀얼 스타일)
- 현재 턴 플레이어만 인벤토리 공개
"""
import os
import re
import time
import random as _rng

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
BLINK  = "\033[5m"

# 고정 UI 색상 (맵 무관)
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
ORANGE = "\033[38;5;208m"
PURPLE = "\033[38;5;135m"
GOLD   = "\033[38;5;220m"

# 레거시 fallback (Miramar 기본값)
SAND   = "\033[38;5;214m"
SAND_D = "\033[33m"
ROCK   = "\033[38;5;240m"
BUILD  = "\033[38;5;252m"
ZONEC  = "\033[94m"

P1C    = "\033[92;1m"
P2C    = "\033[91;1m"

BOX_W   = 72
INNER_W = BOX_W - 2
TW      = INNER_W
TH      = 9
PROW    = 4

P1_INIT = 4
P2_INIT = TW - 5
TRAVEL  = (TW // 2) - P1_INIT - 3

# ── 현재 선택된 맵 ────────────────────────────────────────────────────────────
_current_map = None   # MapConfig | None


def set_map(config) -> None:
    """현재 활성 맵 설정."""
    global _current_map
    _current_map = config


def _get_map():
    """현재 맵 반환. 미설정 시 MAP_MIRAMAR 기본값."""
    if _current_map is not None:
        return _current_map
    from .maps import MAP_MIRAMAR
    return MAP_MIRAMAR


# ── 지형 생성 (맵별) ──────────────────────────────────────────────────────────
def _build_terrain_for(config) -> list:
    """MapConfig 기반 지형 그리드 생성."""
    rng  = _rng.Random(config.seed)
    grid = [['.'] * TW for _ in range(TH)]
    for r in range(TH):
        for c in range(TW):
            v = rng.random()
            if v < config.density_rough:
                grid[r][c] = '~'
            elif v < config.density_rough + config.density_rock:
                grid[r][c] = '^'

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

    box(0, 2, 3); box(5, 1, 2); box(2, 7, 2)
    box(0, 31, 5); box(6, 29, 4); box(3, 33, 3)
    box(0, 61, 3); box(5, 62, 2); box(2, 55, 2)
    box(1, 17, 2); box(7, 46, 2); box(3, 22, 2); box(6, 14, 2)
    return grid


_TERRAINS = {}   # map_id -> terrain grid (lazy populated)


def _get_terrain(config) -> list:
    """맵 ID 기준 지형 그리드 반환 (캐시)."""
    if config.id not in _TERRAINS:
        _TERRAINS[config.id] = _build_terrain_for(config)
    return _TERRAINS[config.id]


def _ansi_len(s: str) -> int:
    return len(re.sub(r'\033\[[^m]*m', '', s))


def _wcslen(s: str) -> int:
    """한글/이모지 2칸, 나머지 1칸으로 표시 너비 계산."""
    w = 0
    for ch in re.sub(r'\033\[[^m]*m', '', s):
        cp = ord(ch)
        if (0xAC00 <= cp <= 0xD7A3 or 0x3131 <= cp <= 0x318E or
                0x4E00 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F):
            w += 2
        elif cp > 0x1F600:
            w += 2  # emoji heuristic
        else:
            w += 1
    return w


def _pad_to(s: str, width: int, fill: str = ' ') -> str:
    return s + fill * max(0, width - _wcslen(s))


def _color_ch(ch: str, cfg=None) -> str:
    """MapConfig 색상으로 지형 문자 채색."""
    if cfg is None:
        cfg = _get_map()
    if ch in '╔═╗║╚╝':  return f"{cfg.col_build}{ch}{RESET}"
    if ch == ' ':         return ' '
    if ch == '^':         return f"{cfg.col_rock}{cfg.ch_rock}{RESET}"
    if ch == '~':         return f"{cfg.col_terrain}{cfg.ch_rough}{RESET}"
    return f"{DIM}{cfg.col_terrain2}.{RESET}"


# ── 박스 유틸 ─────────────────────────────────────────────────────────────────
def _top(cfg=None) -> str:
    c = (cfg if cfg is not None else _get_map()).col_terrain2
    return f"{c}╔{'═'*(BOX_W-2)}╗{RESET}"


def _bot(cfg=None) -> str:
    c = (cfg if cfg is not None else _get_map()).col_terrain2
    return f"{c}╚{'═'*(BOX_W-2)}╝{RESET}"


def _div(lc='╠', mc='═', rc='╣', cfg=None) -> str:
    c = (cfg if cfg is not None else _get_map()).col_terrain2
    return f"{c}{lc}{mc*(BOX_W-2)}{rc}{RESET}"


def _row(content: str, cfg=None) -> str:
    c   = (cfg if cfg is not None else _get_map()).col_terrain2
    pad = INNER_W - _wcslen(content)
    return f"{c}║{RESET}{content}{' '*max(0,pad)}{c}║{RESET}"


def _split_div(cfg=None) -> str:
    c = (cfg if cfg is not None else _get_map()).col_terrain2
    h = INNER_W // 2
    return f"{c}╠{'═'*h}╦{'═'*(INNER_W-h-1)}╣{RESET}"


def _split_bot(cfg=None) -> str:
    c = (cfg if cfg is not None else _get_map()).col_terrain2
    h = INNER_W // 2
    return f"{c}╠{'═'*h}╩{'═'*(INNER_W-h-1)}╣{RESET}"


def _split_row(left: str, right: str, cfg=None) -> str:
    c     = (cfg if cfg is not None else _get_map()).col_terrain2
    h     = INNER_W // 2
    l_pad = h - _wcslen(left)
    r_pad = INNER_W - h - 1 - _wcslen(right)
    return (f"{c}║{RESET}{left}{' '*max(0,l_pad)}"
            f"{c}║{RESET}{right}{' '*max(0,r_pad)}"
            f"{c}║{RESET}")


def _zone_bar(safe: int, max_safe: int = 50, w: int = 40) -> str:
    ratio  = max(0, safe / max_safe)
    filled = int(ratio * w)
    return f"{ZONEC}{'▰'*filled}{DIM}{'▱'*(w-filled)}{RESET}"


def _log_color(msg: str) -> str:
    if any(k in msg for k in ("💥", "즉사", "HP 0", "승리", "🏆")):
        return f"{RED}{msg}{RESET}"
    if any(k in msg for k in ("💊", "회복", "+", "💉")):
        return f"{GREEN}{msg}{RESET}"
    if any(k in msg for k in ("🔫", "공격", "탄약")):
        return f"{YELLOW}{msg}{RESET}"
    if any(k in msg for k in ("📦", "획득", "개봉", "🔶")):
        return f"{CYAN}{msg}{RESET}"
    if any(k in msg for k in ("🌀", "자기장")):
        return f"{ZONEC}{msg}{RESET}"
    if "💣" in msg:
        return f"{ORANGE}{msg}{RESET}"
    if "🚶" in msg or "이동" in msg:
        return f"{SAND_D}{msg}{RESET}"
    return f"{DIM}{WHITE}{msg}{RESET}"


# ── 지도 렌더 ─────────────────────────────────────────────────────────────────
def _render_map(env) -> list:
    from .environment import INITIAL_DISTANCE
    cfg   = _get_map()
    base  = _get_terrain(cfg)
    dist  = max(0, env.distance)
    ratio = min(1.0, (INITIAL_DISTANCE - dist) / INITIAL_DISTANCE)

    p1c = P1_INIT + int(ratio * TRAVEL)
    p2c = P2_INIT - int(ratio * TRAVEL)
    if p1c >= p2c - 1:
        p1c, p2c = p2c - 2, p2c

    safe    = max(0, 100 - 10 * env.turn)
    in_zone = dist > safe
    z_left  = max(0, int((1 - safe / INITIAL_DISTANCE) * (TW // 2 - 4)))
    z_right = min(TW - 1, TW - 1 - int((1 - safe / INITIAL_DISTANCE) * (TW // 2 - 4)))

    lines = []
    for ri, row in enumerate(base):
        buf = []
        for ci, ch in enumerate(row):
            if in_zone and safe < INITIAL_DISTANCE and (ci == z_left or ci == z_right):
                buf.append(f"{BLINK}{cfg.col_zone}│{RESET}")
                continue
            if ri == PROW:
                if ci == p1c:
                    icon = '◉' if env.p1.is_alive else '✕'
                    buf.append(f"{P1C}{icon}{RESET}")
                    continue
                if ci == p2c:
                    icon = '◎' if env.p2.is_alive else '✕'
                    buf.append(f"{P2C}{icon}{RESET}")
                    continue
            buf.append(_color_ch(ch, cfg))
        lines.append(''.join(buf))
    return lines


# ── HP 바 ─────────────────────────────────────────────────────────────────────
def _hp_bar(hp: int, w: int = 18) -> str:
    pct    = max(0, hp / 100)
    filled = int(pct * w)
    empty  = w - filled
    c      = GREEN if pct > 0.6 else (YELLOW if pct > 0.3 else RED)
    return f"{BOLD}{c}{'█'*filled}{'░'*empty}{RESET} {hp:>3}/100"


# ── 인벤토리 표시 (현재 플레이어 전체 / 상대방 숨김) ─────────────────────────
def _inv_lines_full(p) -> list:
    """현재 플레이어 전체 인벤토리 (2줄)."""
    from .items import Weapon, Supply, Vehicle
    from .cards import HouseCard, SupplyDropCard

    # 무기 슬롯
    pistol_am = p.ammo.get(p.pistol.caliber, 0)
    w_parts   = [f"{CYAN}P18C{RESET}({pistol_am})"]
    for w in p.weapon_slots:
        am = p.ammo.get(w.caliber, 0) if w.caliber else "∞"
        star = "★" if w.is_special_ammo else ""
        w_parts.append(f"{YELLOW}{w.name}{star}{RESET}({am}발)")
    line1 = f" 🔫 {' '.join(w_parts)}"

    # 기타 인벤
    i_parts = []
    for item in p.inventory:
        if isinstance(item, SupplyDropCard):
            i_parts.append(f"{GOLD}★보급[{item.roll}]{RESET}")
        elif isinstance(item, HouseCard):
            i_parts.append(f"🏠[{item.roll}]")
        elif isinstance(item, Supply):
            i_parts.append(f"💊{item.name}")
        elif isinstance(item, Vehicle):
            i_parts.append(f"🚗{item.name}")
        elif isinstance(item, Weapon):
            i_parts.append(f"💥{item.name}")
    line2 = f" 🎒 {' '.join(i_parts)}" if i_parts else f" 🎒 {DIM}(없음){RESET}"
    return [line1, line2]


def _inv_hidden() -> list:
    return [
        f" {DIM}🔒 ????{RESET}",
        f" {DIM}🔒 ????{RESET}",
    ]


# ── 메인 render_state ─────────────────────────────────────────────────────────
def render_state(env):
    clear()
    from .environment import INITIAL_DISTANCE

    cfg     = _get_map()
    dist    = env.distance
    turn    = env.turn
    safe    = max(0, 100 - 10 * turn)
    danger  = dist > safe
    cur_pid = env.cur_pid

    map_label = f"{cfg.name_ko}  {cfg.name_en}"
    title  = f" {BOLD}{cfg.col_title}{map_label}{RESET}  {DIM}Battle Royale{RESET}"
    tinfo  = (f"{cfg.col_terrain2}턴:{RESET}{BOLD}{turn}{RESET}"
              f"  {cfg.col_terrain2}거리:{RESET}{BOLD}{CYAN}{dist}{RESET}")
    zinfo  = (f"{RED}{BLINK}⚠ 자기장!{RESET}  " if danger else "") + \
             f"{cfg.col_zone}안전:{safe}칸{RESET}"

    print(_top(cfg))
    print(_row(f" {title}  {tinfo}  {zinfo}", cfg))
    zone_bar = _zone_bar(safe)
    print(_row(f" {cfg.col_zone}ZONE{RESET} {zone_bar} {BOLD}{safe:>3}{RESET}m ", cfg))
    print(_div(cfg=cfg))

    # 지도
    map_lines = _render_map(env)
    legend    = [
        f"{P1C}◉{RESET}={env.p1.name}  {P2C}◎{RESET}={env.p2.name}",
        f"{cfg.col_terrain}{cfg.ch_rough}{RESET}지형 "
        f"{cfg.col_rock}{cfg.ch_rock}{RESET}언덕 "
        f"{cfg.col_build}╔╗{RESET}건물",
    ]
    for li, line in enumerate(map_lines):
        if li < len(legend):
            leg_str   = f" {legend[li]}"
            available = INNER_W - _wcslen(leg_str)
            if _ansi_len(line) <= available:
                line = _pad_to(line, available) + leg_str
        pad = INNER_W - _ansi_len(line)
        bc  = cfg.col_terrain2
        print(f"{bc}║{RESET}{line}{' '*max(0,pad)}{bc}║{RESET}")

    print(_div(cfg=cfg))

    # HUD 두 플레이어
    def p_header(p) -> str:
        c   = P1C if p.pid == 0 else P2C
        tag = "🧍" if p.is_human else "🤖"
        dead = f" {RED}[사망]{RESET}" if not p.is_alive else ""
        return f" {tag} {c}{BOLD}{p.name}{RESET}{dead}"

    def p_hp(p) -> str:
        c = P1C if p.pid == 0 else P2C
        return f" {c}❤{RESET}  {_hp_bar(p.hp)}"

    def p_eff(p) -> str:
        effs  = ", ".join(e.kind for e in p.effects)
        color = YELLOW if effs else DIM
        return f" ✨ {color}{effs or '없음'}{RESET}"

    print(_split_div(cfg))
    print(_split_row(p_header(env.p1), p_header(env.p2), cfg))
    print(_split_row(p_hp(env.p1),    p_hp(env.p2), cfg))

    # 인벤토리: 현재 플레이어만 공개
    p1_lines = _inv_lines_full(env.p1) if cur_pid == 0 else _inv_hidden()
    p2_lines = _inv_lines_full(env.p2) if cur_pid == 1 else _inv_hidden()
    for i in range(2):
        print(_split_row(p1_lines[i], p2_lines[i], cfg))

    print(_split_row(p_eff(env.p1), p_eff(env.p2), cfg))
    print(_split_bot(cfg))

    # Kill feed
    print(_row(f" {BOLD}[ KILL FEED ]{RESET}", cfg))
    recent = env.log[-4:] if env.log else []
    if not recent:
        print(_row(f"  {DIM}(없음){RESET}", cfg))
    for msg in recent:
        truncated = msg[:INNER_W - 4] + ("…" if len(msg) > INNER_W - 4 else "")
        print(_row(f"  ▶ {_log_color(truncated)}", cfg))
    print(_bot(cfg))


# ── 카드 드로우 애니메이션 ─────────────────────────────────────────────────────

CW  = 20   # 카드 외부 너비 (터미널 컬럼)
CIW = 18   # 카드 내부 너비
CH  = 9    # 카드 높이 (행 수)


def _card_line(text: str) -> str:
    """카드 내부 한 줄 (CIW 폭 맞춤)."""
    pad = CIW - _wcslen(text)
    return f"║{text}{' '*max(0,pad)}║"


def _card_back_lines() -> list:
    return [
        f"{SAND_D}╔{'═'*CIW}╗{RESET}",
        f"{SAND_D}║{RESET}{DIM}{'░'*CIW}{RESET}{SAND_D}║{RESET}",
        f"{SAND_D}║ ┌{'─'*(CIW-4)}┐ ║{RESET}",
        f"{SAND_D}║ │{RESET}{YELLOW}  ✦  PUBG  ✦  {RESET}{SAND_D}│ ║{RESET}",
        f"{SAND_D}║ │{RESET}{WHITE}   ◈  ◆  ◈   {RESET}{SAND_D}│ ║{RESET}",
        f"{SAND_D}║ │{RESET}{DIM}  LOOT  BOX  {RESET}{SAND_D}│ ║{RESET}",
        f"{SAND_D}║ └{'─'*(CIW-4)}┘ ║{RESET}",
        f"{SAND_D}║{RESET}{DIM}{'░'*CIW}{RESET}{SAND_D}║{RESET}",
        f"{SAND_D}╚{'═'*CIW}╝{RESET}",
    ]


def _card_flip_lines() -> list:
    """플립 중 (세로 줄)."""
    mid = CW // 2
    lines = []
    for i in range(CH):
        inner = f"{YELLOW}{'│' * mid}{RESET}"
        lines.append(inner)
    return lines


def _item_card_lines(item, is_supply: bool = False) -> list:
    """아이템 카드 앞면."""
    from .items import Weapon, Supply, Vehicle, Ammo

    border_c = GOLD if is_supply else CYAN

    if isinstance(item, Weapon):
        cat      = item.category
        star     = "★" if item.is_special_ammo else ""
        ammo_str = f"{item.caliber}{star}" if item.caliber else "근접/투척"
        lines = [
            f"{border_c}╔{'═'*CIW}╗{RESET}",
            _card_line(f"{border_c} 【{cat}】{RESET}"),
            f"{border_c}║{'─'*CIW}║{RESET}",
            _card_line(f" {BOLD}{WHITE}{item.name}{RESET}"),
            _card_line(f" 구경 {YELLOW}{ammo_str}{RESET}"),
            _card_line(f" 사거리 {item.attack_range}"),
            _card_line(f" 탄약  {item.starter_ammo}발" if item.is_firearm else " 단회사용"),
            _card_line(f" 피해  {item.damage_desc()}"),
            f"{border_c}╚{'═'*CIW}╝{RESET}",
        ]
    elif isinstance(item, Ammo):
        star  = "★" if item.is_special else ""
        lines = [
            f"{border_c}╔{'═'*CIW}╗{RESET}",
            _card_line(f"{border_c} 【탄약】{RESET}"),
            f"{border_c}║{'─'*CIW}║{RESET}",
            _card_line(f" {BOLD}{YELLOW}{item.caliber}{star}{RESET}"),
            _card_line(f" ×{item.count}발"),
            _card_line(""),
            _card_line(""),
            _card_line(f" {'특수탄 ★' if item.is_special else '일반탄'}"),
            f"{border_c}╚{'═'*CIW}╝{RESET}",
        ]
    elif isinstance(item, Supply):
        lines = [
            f"{border_c}╔{'═'*CIW}╗{RESET}",
            _card_line(f"{border_c} 【지원품】{RESET}"),
            f"{border_c}║{'─'*CIW}║{RESET}",
            _card_line(f" {BOLD}{GREEN}{item.name}{RESET}"),
            _card_line(f" {item.description}"),
            _card_line(""),
            _card_line(""),
            _card_line(""),
            f"{border_c}╚{'═'*CIW}╝{RESET}",
        ]
    elif isinstance(item, Vehicle):
        lines = [
            f"{border_c}╔{'═'*CIW}╗{RESET}",
            _card_line(f"{border_c} 【이동수단】{RESET}"),
            f"{border_c}║{'─'*CIW}║{RESET}",
            _card_line(f" {BOLD}{WHITE}{item.name}{RESET}"),
            _card_line(f" 속도 +{item.speed}칸"),
            _card_line(f" {item.special or ''}"),
            _card_line(""),
            _card_line(""),
            f"{border_c}╚{'═'*CIW}╝{RESET}",
        ]
    else:
        lines = ([f"{border_c}╔{'═'*CIW}╗{RESET}"] +
                 [_card_line("") for _ in range(CH-2)] +
                 [f"{border_c}╚{'═'*CIW}╝{RESET}"])
    return lines


def _print_card_frame(cards_list: list, header: str, msg: str):
    """카드들을 나란히 출력."""
    clear()
    print()
    print(f"  {BOLD}{YELLOW}{'═'*44}{RESET}")
    print(f"  {BOLD}  {header}{RESET}")
    print(f"  {BOLD}{YELLOW}{'═'*44}{RESET}")
    if msg:
        print(f"  {msg}")
    print()
    for row_i in range(CH):
        line = "  "
        for card in cards_list:
            if row_i < len(card):
                line += card[row_i] + "   "
        print(line)
    print()


def show_card_draw_animation(items: list, is_supply: bool, player_name: str,
                             quick: bool = False):
    """유희왕 마스터듀얼 스타일 카드 드로우 애니메이션."""
    if not items:
        return

    d_back  = 0.1 if quick else 0.35
    d_flip  = 0.05 if quick else 0.15
    d_front = 0.3 if quick else 0.9

    label  = "★ 보급 드롭 ★" if is_supply else "📦 보급품 발견"
    header = f"{player_name}  {label}"

    backs  = [_card_back_lines() for _ in items]
    fronts = [_item_card_lines(item, is_supply) for item in items]

    # Phase 1: 카드 뒷면 (드로우)
    _print_card_frame(backs, header, f"{DIM}카드 드로우...{RESET}")
    time.sleep(d_back)

    # Phase 2: 플립 (좁아지는 효과)
    for _ in range(2):
        _print_card_frame(backs, header, f"{BLINK}{YELLOW}◀▶ FLIP ◀▶{RESET}")
        time.sleep(d_flip)
        _print_card_frame(
            [[f"{YELLOW}{'│'*(CW//2)}{RESET}"] * CH for _ in items],
            header, f"{BLINK}{YELLOW}◀▶ FLIP ◀▶{RESET}"
        )
        time.sleep(d_flip)

    # Phase 3: 카드 앞면 공개
    acquired = f"  {BOLD}{GREEN}획득!  총 {len(items)}개 아이템{RESET}"
    _print_card_frame(fronts, header, acquired)
    time.sleep(d_front)


# ── 공개 유틸 ─────────────────────────────────────────────────────────────────
def clear():
    os.system("clear" if os.name == "posix" else "cls")


def print_log(lines: list):
    for msg in lines:
        print(f"  {_log_color(msg)}")


def print_actions(actions: list):
    cfg = _get_map()
    print(f"\n  {BOLD}[ 행동 선택 ]{RESET}  {DIM}(0=패스){RESET}")
    print(f"  {cfg.col_terrain2}{'─'*(BOX_W-4)}{RESET}")
    for i, act in enumerate(actions):
        usable = act.get("usable", True)
        if usable is False:
            label = f"{DIM}{act['label']}{RESET}  {RED}❌{RESET}"
        else:
            label = f"{WHITE}{act['label']}{RESET}"
        print(f"  [{i+1}] {label}")
    print(f"  {cfg.col_terrain2}{'─'*(BOX_W-4)}{RESET}")


def show_winner(env):
    clear()
    cfg = _get_map()
    w   = env.winner
    print(_top(cfg))
    if w:
        c   = P1C if w.pid == 0 else P2C
        msg = f"  {BOLD}{'🏆'*3}  {c}{w.name} 승리!{RESET} {'🏆'*3}"
    else:
        msg = f"  {DIM}무승부{RESET}"
    print(_row(msg, cfg))
    print(_div(cfg=cfg))
    print(_row(f"  {DIM}총 {env.turn}턴 진행{RESET}", cfg))
    for p in [env.p1, env.p2]:
        c     = P1C if p.pid == 0 else P2C
        alive = f"{GREEN}생존{RESET}" if p.is_alive else f"{RED}사망{RESET}"
        print(_row(f"  {c}{BOLD}{p.name:12s}{RESET}  HP: {p.hp:>3}  [{alive}]", cfg))
    print(_bot(cfg))
