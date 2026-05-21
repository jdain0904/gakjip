"""카드 덱 및 캐릭터 정의."""
from typing import List
from .card import Card, CardType, CardSuit, CardValue, CharacterCard

# ──────────────────────────────────────────────────────────
#  플레이 카드 덱 빌드
# ──────────────────────────────────────────────────────────

def build_play_deck() -> List[Card]:
    S, H, D, C = CardSuit.SPADES, CardSuit.HEARTS, CardSuit.DIAMONDS, CardSuit.CLUBS
    v = {n: CardValue[n] for n in CardValue.__members__}

    def card(ct, suit, val):
        return Card(ct, suit, v[val])

    B  = CardType.BANG
    MS = CardType.MISSED
    BE = CardType.BEER
    SA = CardType.SALOON
    IN = CardType.INDIANS
    DU = CardType.DUEL
    GS = CardType.GENERAL_STORE
    PA = CardType.PANIC
    CB = CardType.CAT_BALOU
    SC = CardType.STAGECOACH
    WF = CardType.WELLS_FARGO
    GA = CardType.GATLING
    DY = CardType.DYNAMITE
    JA = CardType.JAIL
    BA = CardType.BARREL
    SP = CardType.SCOPE
    MU = CardType.MUSTANG

    deck: List[Card] = [
        # BANG! ×25
        card(B, S, "TWO"),   card(B, S, "THREE"), card(B, S, "FOUR"),
        card(B, S, "FIVE"),  card(B, S, "SIX"),   card(B, S, "SEVEN"),
        card(B, S, "EIGHT"), card(B, S, "NINE"),  card(B, S, "TEN"),
        card(B, S, "JACK"),  card(B, S, "QUEEN"), card(B, S, "KING"),
        card(B, S, "ACE"),
        card(B, H, "TWO"),   card(B, H, "THREE"), card(B, H, "FOUR"),
        card(B, H, "FIVE"),  card(B, H, "SIX"),   card(B, H, "SEVEN"),
        card(B, D, "TWO"),   card(B, D, "THREE"), card(B, D, "FOUR"),
        card(B, D, "FIVE"),  card(B, D, "SIX"),
        card(B, C, "TWO"),

        # Missed! ×12
        card(MS, S, "TWO"),  card(MS, S, "THREE"), card(MS, S, "FOUR"),
        card(MS, S, "FIVE"), card(MS, S, "SIX"),   card(MS, S, "SEVEN"),
        card(MS, S, "EIGHT"),card(MS, S, "NINE"),  card(MS, S, "TEN"),
        card(MS, H, "TWO"),  card(MS, H, "THREE"), card(MS, H, "FOUR"),

        # Beer ×8
        card(BE, H, "SIX"),  card(BE, H, "SEVEN"), card(BE, H, "EIGHT"),
        card(BE, H, "NINE"), card(BE, H, "TEN"),   card(BE, H, "JACK"),
        card(BE, D, "SIX"),  card(BE, D, "SEVEN"),

        # Saloon ×1
        card(SA, H, "FIVE"),

        # Indians! ×2
        card(IN, D, "KING"),  card(IN, C, "ACE"),

        # Duel ×3
        card(DU, S, "JACK"), card(DU, D, "QUEEN"), card(DU, C, "EIGHT"),

        # General Store ×2
        card(GS, C, "NINE"), card(GS, S, "QUEEN"),

        # Panic! ×4
        card(PA, H, "JACK"), card(PA, H, "QUEEN"), card(PA, H, "ACE"),
        card(PA, D, "EIGHT"),

        # Cat Balou ×4
        card(CB, D, "NINE"), card(CB, D, "TEN"), card(CB, D, "JACK"),
        card(CB, C, "THREE"),

        # Stagecoach ×2
        card(SC, S, "NINE"), card(SC, S, "TEN"),

        # Wells Fargo ×1
        card(WF, H, "THREE"),

        # Gatling ×1
        card(GA, H, "TEN"),

        # Dynamite ×1
        card(DY, D, "TWO"),

        # Jail ×3
        card(JA, S, "FOUR"), card(JA, S, "TEN"), card(JA, H, "TWO"),

        # Barrel ×2
        card(BA, S, "KING"), card(BA, S, "ACE"),

        # Scope ×1
        card(SP, S, "EIGHT"),

        # Mustang ×2
        card(MU, H, "EIGHT"), card(MU, H, "NINE"),
    ]
    return deck


# ──────────────────────────────────────────────────────────
#  캐릭터 카드 목록
# ──────────────────────────────────────────────────────────

ALL_CHARACTERS: List[CharacterCard] = [
    CharacterCard("Bart Cassidy",     "피격 시마다 카드 1장 드로우",                          4, "bart_cassidy"),
    CharacterCard("Black Jack",       "두 번째 드로우 공개, 붉은 카드면 추가 드로우",           4, "black_jack"),
    CharacterCard("Calamity Janet",   "BANG!↔Missed! 교환 사용 가능",                        4, "calamity_janet"),
    CharacterCard("El Gringo",        "피격 시 공격자 패에서 카드 1장 강탈",                  3, "el_gringo"),
    CharacterCard("Jesse Jones",      "첫 드로우를 다른 플레이어 패에서 가져올 수 있음",        4, "jesse_jones"),
    CharacterCard("Jourdonnais",      "배럴 능력 내장 (♥ 뒤집으면 회피)",                    4, "jourdonnais"),
    CharacterCard("Kit Carlson",      "상위 3장 공개 후 2장 선택, 1장 덱 상단 복귀",          4, "kit_carlson"),
    CharacterCard("Lucky Duke",       "드로! 판정 시 2장 뒤집어 유리한 것 선택",              4, "lucky_duke"),
    CharacterCard("Paul Regret",      "무스탕 효과 내장 (사거리 +1 방어)",                    3, "paul_regret"),
    CharacterCard("Pedro Ramirez",    "첫 드로우를 버려진 더미 최상단에서 가져올 수 있음",     4, "pedro_ramirez"),
    CharacterCard("Rose Doolan",      "스코프 효과 내장 (사거리 +1 공격)",                    4, "rose_doolan"),
    CharacterCard("Sid Ketchum",      "언제든 패 2장 버려 HP 1 회복",                        4, "sid_ketchum"),
    CharacterCard("Slab the Killer",  "그의 BANG!을 피하려면 Missed! 2장 필요",              4, "slab_the_killer"),
    CharacterCard("Suzy Lafayette",   "패가 0이 되는 순간 카드 1장 드로우",                  4, "suzy_lafayette"),
    CharacterCard("Vulture Sam",      "플레이어 사망 시 그 패와 장비 모두 획득",              4, "vulture_sam"),
    CharacterCard("Willy the Kid",    "BANG! 카드를 매 턴 무제한 사용 가능",                  4, "willy_the_kid"),
]
