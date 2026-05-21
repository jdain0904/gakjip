from enum import Enum
from dataclasses import dataclass
from typing import Optional


class CardSuit(Enum):
    SPADES   = "♠"
    HEARTS   = "♥"
    DIAMONDS = "♦"
    CLUBS    = "♣"


class CardValue(Enum):
    TWO   = ("2",  2)
    THREE = ("3",  3)
    FOUR  = ("4",  4)
    FIVE  = ("5",  5)
    SIX   = ("6",  6)
    SEVEN = ("7",  7)
    EIGHT = ("8",  8)
    NINE  = ("9",  9)
    TEN   = ("10", 10)
    JACK  = ("J",  11)
    QUEEN = ("Q",  12)
    KING  = ("K",  13)
    ACE   = ("A",  14)

    def __init__(self, symbol: str, numeric: int):
        self.symbol  = symbol
        self.numeric = numeric


class CardType(Enum):
    # 즉시 발동 (갈색 카드)
    BANG          = "BANG!"
    MISSED        = "Missed!"
    BEER          = "Beer"
    SALOON        = "Saloon"
    INDIANS       = "Indians!"
    DUEL          = "Duel"
    GENERAL_STORE = "General Store"
    PANIC         = "Panic!"
    CAT_BALOU     = "Cat Balou"
    STAGECOACH    = "Stagecoach"
    WELLS_FARGO   = "Wells Fargo"
    GATLING       = "Gatling"
    # 장비 (파란 카드)
    DYNAMITE      = "Dynamite"
    JAIL          = "Jail"
    BARREL        = "Barrel"
    SCOPE         = "Scope"
    MUSTANG       = "Mustang"

    def is_brown(self) -> bool:
        return self in {
            CardType.BANG, CardType.MISSED, CardType.BEER,
            CardType.SALOON, CardType.INDIANS, CardType.DUEL,
            CardType.GENERAL_STORE, CardType.PANIC, CardType.CAT_BALOU,
            CardType.STAGECOACH, CardType.WELLS_FARGO, CardType.GATLING,
        }

    def is_blue(self) -> bool:
        return not self.is_brown()


class RoleType(Enum):
    SHERIFF  = "Sheriff"
    DEPUTY   = "Deputy"
    OUTLAW   = "Outlaw"
    RENEGADE = "Renegade"


@dataclass(frozen=True)
class Card:
    card_type: CardType
    suit:      CardSuit
    value:     CardValue

    def __str__(self) -> str:
        return f"{self.card_type.value}[{self.suit.value}{self.value.symbol}]"

    def short(self) -> str:
        return f"{self.suit.value}{self.value.symbol}"

    def draw_check_is_hit(self) -> bool:
        """♥ 또는 ♦ → 히트 (배럴·감옥 판정에 사용)"""
        return self.suit in (CardSuit.HEARTS, CardSuit.DIAMONDS)


@dataclass(frozen=True)
class RoleCard:
    role: RoleType

    def __str__(self) -> str:
        return self.role.value


@dataclass(frozen=True)
class CharacterCard:
    name:        str
    description: str
    base_hp:     int
    ability_key: str

    def __str__(self) -> str:
        return f"{self.name} [{self.base_hp}HP]"
