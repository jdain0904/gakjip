"""인스크립션+서부 분위기 ASCII 아트."""

TITLE = r"""
  ██████╗  █████╗ ███╗   ██╗ ██████╗ ██╗
  ██╔══██╗██╔══██╗████╗  ██║██╔════╝ ██║
  ██████╔╝███████║██╔██╗ ██║██║  ███╗██║
  ██╔══██╗██╔══██║██║╚██╗██║██║   ██║╚═╝
  ██████╔╝██║  ██║██║ ╚████║╚██████╔╝██╗
  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝

  ☠  D E A D  M A N ' S  S A L O O N  ☠
  ─────────────────────────────────────────
  어둠 속 서부, 죽음이 패를 나눠준다...
"""

SKULL = r"""
     .d8888b.
    d88P  Y88b
    888    888
    888    888
    Y88b  d88P
     "Y8888P"
      ╔══╗
      ║  ║
     ╔╩══╩╗
     ║    ║
     ╚════╝
"""

WINNER_SHERIFF = r"""
  ╔══════════════════════════════╗
  ║   ⭐  THE LAW PREVAILS  ⭐   ║
  ║  셰리프와 부관의 승리!         ║
  ╚══════════════════════════════╝
"""

WINNER_OUTLAW = r"""
  ╔══════════════════════════════╗
  ║  💀  OUTLAWS WIN  💀         ║
  ║  무법자들이 마을을 장악했다!   ║
  ╚══════════════════════════════╝
"""

WINNER_RENEGADE = r"""
  ╔══════════════════════════════╗
  ║  🌑  THE LONE WOLF  🌑       ║
  ║  레네게이드가 홀로 살아남았다! ║
  ╚══════════════════════════════╝
"""

SALOON_DIVIDER = "  ═══╤═══╤═══╤═══╤═══╤═══╤═══╤═══╤═══"

BULLET_FULL  = "●"
BULLET_EMPTY = "○"

CARD_ICONS = {
    "BANG!"        : "🔫",
    "Missed!"      : "💨",
    "Beer"         : "🍺",
    "Saloon"       : "🍻",
    "Indians!"     : "🏹",
    "Duel"         : "⚔️ ",
    "General Store": "🏪",
    "Panic!"       : "🖐️ ",
    "Cat Balou"    : "🐱",
    "Stagecoach"   : "🚌",
    "Wells Fargo"  : "🏦",
    "Gatling"      : "💥",
    "Dynamite"     : "💣",
    "Jail"         : "⛓️ ",
    "Barrel"       : "🛢️ ",
    "Scope"        : "🔭",
    "Mustang"      : "🐴",
}

ROLE_ART = {
    "Sheriff" : "⭐",
    "Deputy"  : "🔰",
    "Outlaw"  : "💀",
    "Renegade": "🌑",
}

INTRO_LINES = [
    "삐걱거리는 살롱 문이 열리고...",
    "바람 소리만이 황야를 가른다.",
    "죽음의 내음이 카드 위를 맴돈다.",
    "서커스는 끝났다. 이제 총이 말한다.",
    "운명은 덱 속에 숨어있다...",
]

DEATH_LINES = [
    "먼지로 돌아간다...",
    "총성이 메아리쳐 사라진다.",
    "아무도 그를 기억하지 않을 것이다.",
    "황야의 바람이 그를 데려간다.",
    "또 하나의 묘비가 세워진다.",
]

def card_box(name: str, suit: str, value: str, is_blue: bool = False) -> str:
    icon   = CARD_ICONS.get(name, "  ")
    border = "╔" + "═"*9 + "╗"
    bottom = "╚" + "═"*9 + "╝"
    color  = "~" if is_blue else " "
    lines  = [
        border,
        f"║{value:<2}       ║",
        f"║         ║",
        f"║  {icon}    ║",
        f"║         ║",
        f"║      {suit}{value:>2}║",
        bottom,
    ]
    return "\n".join(lines)
