"""
PUBG 맵 설정 시스템
- 4개 맵: 비켄디, 에란겔, 사녹, 미라마
- 맵별 색상 테마, 지형 시드, 밀도
- 이미지 프리뷰 (PIL) 또는 ASCII 아트 프리뷰
"""
from __future__ import annotations
from dataclasses import dataclass, field
import os
import re

try:
    from PIL import Image as _PILImage
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

PREVIEW_W = 30   # terminal columns per preview
PREVIEW_H = 10   # terminal lines per preview (each = 2 pixel rows with ▀)

RESET = "\033[0m"
DIM   = "\033[2m"


@dataclass
class MapConfig:
    id: str
    name_ko: str       # Korean name
    name_en: str       # English name
    desc: str          # Korean description
    seed: int          # terrain RNG seed
    # ANSI color strings
    col_terrain: str   # main terrain color
    col_terrain2: str  # secondary/dim terrain
    col_rock: str      # rock/hill color
    col_build: str     # building walls color
    col_zone: str      # blue zone color
    col_title: str     # title/header accent color
    col_water: str     # water/special terrain
    # terrain symbol replacements
    ch_rough: str      # replaces '~' in terrain grid
    ch_rock: str       # replaces '^' in terrain grid
    # terrain density
    density_rough: float
    density_rock: float


# ── 맵 정의 ───────────────────────────────────────────────────────────────────

MAP_VIKENDI = MapConfig(
    id="vikendi",
    name_ko="비켄디",
    name_en="Vikendi",
    desc="❄ 눈 덮인 겨울 섬",
    seed=1111,
    col_terrain="\033[97m",
    col_terrain2="\033[38;5;253m",
    col_rock="\033[38;5;248m",
    col_build="\033[38;5;195m",
    col_zone="\033[96m",
    col_title="\033[97;1m",
    col_water="\033[38;5;117m",
    ch_rough="≋",
    ch_rock="▲",
    density_rough=0.10,
    density_rock=0.22,
)

MAP_ERANGEL = MapConfig(
    id="erangel",
    name_ko="에란겔",
    name_en="Erangel",
    desc="🌾 광활한 초원과 농장",
    seed=2222,
    col_terrain="\033[32m",
    col_terrain2="\033[38;5;34m",
    col_rock="\033[38;5;136m",
    col_build="\033[38;5;187m",
    col_zone="\033[94m",
    col_title="\033[32;1m",
    col_water="\033[38;5;74m",
    ch_rough="♣",
    ch_rock="♣",
    density_rough=0.20,
    density_rock=0.12,
)

MAP_SANHOK = MapConfig(
    id="sanhok",
    name_ko="사녹",
    name_en="Sanhok",
    desc="🌿 빽빽한 열대 밀림",
    seed=3333,
    col_terrain="\033[38;5;22m",
    col_terrain2="\033[38;5;28m",
    col_rock="\033[38;5;94m",
    col_build="\033[38;5;130m",
    col_zone="\033[32m",
    col_title="\033[38;5;46;1m",
    col_water="\033[38;5;30m",
    ch_rough="♦",
    ch_rock="♣",
    density_rough=0.28,
    density_rock=0.18,
)

MAP_MIRAMAR = MapConfig(
    id="miramar",
    name_ko="미라마",
    name_en="Miramar",
    desc="🏜 황량한 사막 지대",
    seed=7777,
    col_terrain="\033[38;5;214m",
    col_terrain2="\033[33m",
    col_rock="\033[38;5;240m",
    col_build="\033[38;5;252m",
    col_zone="\033[94m",
    col_title="\033[38;5;214;1m",
    col_water="\033[38;5;24m",
    ch_rough="≈",
    ch_rock="▲",
    density_rough=0.15,
    density_rock=0.20,
)

ALL_MAPS = [MAP_VIKENDI, MAP_ERANGEL, MAP_SANHOK, MAP_MIRAMAR]


# ── 이미지 프리뷰 ─────────────────────────────────────────────────────────────

def load_image_preview(map_config: MapConfig) -> list[str] | None:
    """PIL로 이미지를 불러와 반블록 기법으로 터미널 프리뷰 생성."""
    if not _PIL_OK:
        return None
    try:
        img_path = None
        for ext in (".jpg", ".png", ".jpeg"):
            candidate = os.path.join(ASSETS_DIR, f"{map_config.id}{ext}")
            if os.path.isfile(candidate):
                img_path = candidate
                break
        if img_path is None:
            return None

        img = _PILImage.open(img_path)
        img = img.resize((PREVIEW_W, PREVIEW_H * 2), _PILImage.LANCZOS)
        img = img.convert("RGB")
        pixels = img.load()

        lines = []
        for row in range(PREVIEW_H):
            line = ""
            for col in range(PREVIEW_W):
                r1, g1, b1 = pixels[col, row * 2]
                r2, g2, b2 = pixels[col, row * 2 + 1]
                line += (f"\033[38;2;{r1};{g1};{b1}m"
                         f"\033[48;2;{r2};{g2};{b2}m▀\033[0m")
            lines.append(line)
        return lines
    except Exception:
        return None


# ── ASCII 아트 프리뷰 ─────────────────────────────────────────────────────────

def _wcslen_raw(s: str) -> int:
    """ANSI 제거 후 표시 너비 계산."""
    clean = re.sub(r'\033\[[^m]*m', '', s)
    w = 0
    for ch in clean:
        cp = ord(ch)
        if (0xAC00 <= cp <= 0xD7A3 or 0x3131 <= cp <= 0x318E or
                0x4E00 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F):
            w += 2
        elif cp > 0x1F600:
            w += 2
        else:
            w += 1
    return w


def _pad_line(s: str, width: int) -> str:
    """표시 너비 기준으로 공백 패딩."""
    current = _wcslen_raw(s)
    return s + ' ' * max(0, width - current)


def ascii_preview(config: MapConfig) -> list[str]:
    """맵별 분위기 ASCII 아트 (PREVIEW_H 줄 × PREVIEW_W 컬럼)."""
    T  = config.col_terrain
    T2 = config.col_terrain2
    R  = config.col_rock
    B  = config.col_build
    W  = config.col_water
    Z  = config.col_zone
    X  = RESET
    D  = DIM

    if config.id == "vikendi":
        # 비켄디: 눈 덮인 겨울 섬 — 흰색/하늘색 테마
        raw = [
            f"{T}  *  * ❄  *   *  ❄  *   *  {X}",
            f"{T2}≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋{X}",
            f"{T} * {R}▲▲{T}  *  ❄  *  {R}▲{T}  *  ❄  * {X}",
            f"{T}  {R}▲▲▲{T} * ❄ *   {R}▲▲▲{T}  ❄ *  *  {X}",
            f"{B}╔══╗{T} *  *  ❄ *  *   {B}╔═╗{T} ❄  * {X}",
            f"{B}║  ║{T}  ❄  *  *  ❄ * {B}║ ║{T}  *  *  {X}",
            f"{B}╚══╝{T} *  ❄  *   *  * {B}╚═╝{T}  ❄  * {X}",
            f"{W}≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋{X}",
            f"{T}* ❄ {T2}·{T} *  ❄  *  * {T2}·{T} ❄  *  ❄ {X}",
            f"{T2}  *  ❄  *   * ❄  *   ❄   *  * {X}",
        ]

    elif config.id == "erangel":
        # 에란겔: 초원과 농장 — 초록/황금 테마
        raw = [
            f"{T}♣ ♣  ♣   ♣ ♣  ♣   ♣  ♣   ♣ ♣{X}",
            f"{T2},,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,{X}",
            f"{T}♣  {B}╔══╗{T} ♣   ♣  ♣  {B}╔═╗{T}  ♣  ♣{X}",
            f"{T2},, {B}║  ║{T2} ,,  ,, {T}♣ {B}║ ║{T2}  ,,  ,{X}",
            f"{T}♣  {B}╚══╝{T} ♣  ♣  ♣  {B}╚═╝{T} ♣  ♣  {X}",
            f"{W}≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈{X}",
            f"{T2},,, {R}♣{T2} ,,,  ,,, {R}♣♣{T2} ,,, {R}♣{T2}  ,,{X}",
            f"{T}♣  ♣  {T2},{T} ♣  ♣   ♣   {T2},{T} ♣  ♣  {X}",
            f"{T2},,,,  ,,,, ,,,,  ,,, ,,,, ,,,{X}",
            f"{T}♣ ♣  ♣   ♣ ♣  ♣   ♣  ♣   ♣ ♣{X}",
        ]

    elif config.id == "sanhok":
        # 사녹: 열대 밀림 — 짙은 초록 테마
        raw = [
            f"{T}♣♦♣♦♣♣♦♣♦♣♣♦♣♣♦♣♣♦♣♦♣♦♣♣♦♣♣♦{X}",
            f"{T2}♦♣♦♣♦♦♣♦♣♦♦♣♦♦♣♦♦♣♦♣♦♣♦♦♣♦♦♣{X}",
            f"{T}♣♦{B}╔══╗{T}♦♣♦♣♦♣♦{B}╔═╗{T}♦♣♦♣♦♣♦♣{X}",
            f"{T2}♦♣{B}║  ║{T2}♣♦♣♦♣♦♣{B}║ ║{T2}♣♦♣♦♣♦♣♦{X}",
            f"{T}♣♦{B}╚══╝{T}♦♣♦♣♦♣♦{B}╚═╝{T}♦♣♦♣♦♣♦♣{X}",
            f"{W}≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋≋{X}",
            f"{T}♣♦♣{R}♣{T}♦♣♦♣♦{R}♣{T}♦♣♦♣♦♣{R}♣{T}♦♣♦♣{X}",
            f"{T2}♦♣♦♣♦{R}♣{T2}♦♣♦♣{R}♣{T2}♦♣♦♣♦{R}♣{T2}♦♣♦♣♦{X}",
            f"{T}♣♦♣♦♣♣♦♣♦♣♣♦♣♣♦♣♣♦♣♦♣♦♣♣♦♣♣♦{X}",
            f"{T2}♦♣♦♣♦♦♣♦♣♦♦♣♦♦♣♦♦♣♦♣♦♣♦♦♣♦♦♣{X}",
        ]

    else:  # miramar
        # 미라마: 사막 — 주황/모래 테마
        raw = [
            f"{T}. . . . . ▲. . . . . . . . . {X}",
            f"{T2}  . . . .▲▲. . .↑. . . . . . {X}",
            f"{T}. . . . ▲▲▲ . . . . . . . . . {X}",
            f"{B}╔══╗{T2} . . . ↑ . . {B}╔═╗{T2} . . .{X}",
            f"{B}║  ║{T} . .↑. . . .  {B}║ ║{T} . . . {X}",
            f"{B}╚══╝{T2}. . . . . . . {B}╚═╝{T2} . . .{X}",
            f"{T}. . . . . . .↑. . . . . . . . {X}",
            f"{R}▲▲▲{T} . . . . . . {R}▲▲{T} . . . . .{X}",
            f"{T2}. . {R}▲{T2} . . . . . . . {R}▲▲▲{T2} . . {X}",
            f"{T}. . . . . . . . . . . . . . . {X}",
        ]

    # PREVIEW_W 너비로 맞추기
    result = []
    for line in raw:
        result.append(_pad_line(line, PREVIEW_W))
    return result


# ── 프리뷰 선택 ───────────────────────────────────────────────────────────────

def get_preview(config: MapConfig) -> list[str]:
    """이미지 프리뷰 시도 → 실패 시 ASCII 아트 반환."""
    img = load_image_preview(config)
    if img is not None:
        return img
    return ascii_preview(config)


# ── 맵 선택 화면 ─────────────────────────────────────────────────────────────

BOX_W   = 72
INNER_W = BOX_W - 2

BOLD   = "\033[1m"
WHITE  = "\033[97m"
DIM_C  = "\033[2m"


def _strip_ansi(s: str) -> str:
    return re.sub(r'\033\[[^m]*m', '', s)


def _display_width(s: str) -> int:
    clean = _strip_ansi(s)
    w = 0
    for ch in clean:
        cp = ord(ch)
        if (0xAC00 <= cp <= 0xD7A3 or 0x3131 <= cp <= 0x318E or
                0x4E00 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F):
            w += 2
        elif cp > 0x1F600:
            w += 2
        else:
            w += 1
    return w


def _box_row(content: str, box_color: str = "\033[38;5;240m") -> str:
    """72-wide 박스 한 줄."""
    pad = INNER_W - _display_width(content)
    return f"{box_color}║{RESET}{content}{' ' * max(0, pad)}{box_color}║{RESET}"


def _box_top(box_color: str = "\033[38;5;240m") -> str:
    return f"{box_color}╔{'═' * INNER_W}╗{RESET}"


def _box_bot(box_color: str = "\033[38;5;240m") -> str:
    return f"{box_color}╚{'═' * INNER_W}╝{RESET}"


def _box_div(box_color: str = "\033[38;5;240m") -> str:
    return f"{box_color}╠{'═' * INNER_W}╣{RESET}"


def draw_map_selection_screen():
    """4개 맵을 2×2 격자로 보여주는 선택 화면 (표시만, 입력 없음)."""
    import os as _os
    _os.system("clear" if _os.name == "posix" else "cls")

    box_c = "\033[38;5;240m"

    # 상단 헤더
    print(_box_top(box_c))
    header = f"  {BOLD}{WHITE}🗺  맵 선택  — MAP SELECT{RESET}"
    print(_box_row(header, box_c))
    print(_box_div(box_c))

    # 각 맵 카드 데이터 준비
    previews = [get_preview(m) for m in ALL_MAPS]

    # 카드 너비: INNER_W / 2 = 35
    CARD_W = INNER_W // 2  # 35

    # 2x2 레이아웃으로 출력
    for row_idx in range(2):
        left_map  = ALL_MAPS[row_idx * 2]
        right_map = ALL_MAPS[row_idx * 2 + 1]
        left_prev  = previews[row_idx * 2]
        right_prev = previews[row_idx * 2 + 1]
        num_left  = row_idx * 2 + 1
        num_right = row_idx * 2 + 2

        if row_idx > 0:
            print(_box_div(box_c))

        # 헤더 줄: [번호] 이름
        def card_header(m: MapConfig, num: int) -> str:
            return (f" {BOLD}{WHITE}[{num}]{RESET} "
                    f"{m.col_title}{BOLD}{m.name_ko}{RESET} "
                    f"{DIM_C}{m.name_en}{RESET}")

        def card_desc(m: MapConfig) -> str:
            return f"  {m.col_terrain}{m.desc}{RESET}"

        # 각 카드 줄 목록
        left_lines  = []
        right_lines = []

        left_lines.append(card_header(left_map,  num_left))
        right_lines.append(card_header(right_map, num_right))

        left_lines.append(card_desc(left_map))
        right_lines.append(card_desc(right_map))

        left_lines.append("")  # 빈 줄 (프리뷰 구분)
        right_lines.append("")

        # 프리뷰 줄들
        for i in range(PREVIEW_H):
            lp = left_prev[i]  if i < len(left_prev)  else ""
            rp = right_prev[i] if i < len(right_prev) else ""
            left_lines.append(lp)
            right_lines.append(rp)

        # 합계 줄 수
        total_lines = max(len(left_lines), len(right_lines))

        # 각 줄을 분할 박스 행으로 출력
        for li in range(total_lines):
            ls = left_lines[li]  if li < len(left_lines)  else ""
            rs = right_lines[li] if li < len(right_lines) else ""

            lw = _display_width(ls)
            rw = _display_width(rs)

            l_pad = max(0, CARD_W - lw)
            r_pad = max(0, INNER_W - CARD_W - 1 - rw)

            line = (f"{box_c}║{RESET}{ls}{' ' * l_pad}"
                    f"{box_c}║{RESET}{rs}{' ' * r_pad}"
                    f"{box_c}║{RESET}")
            print(line)

    print(_box_bot(box_c))
    print()
