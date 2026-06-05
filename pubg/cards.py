"""집 카드 & 보급 카드 — 랜덤 0~60 번호로 아이템 결정."""
import random
from dataclasses import dataclass, field
from typing import Union

from .items import Weapon, Supply, Vehicle, WEAPONS, SUPPLIES, VEHICLES

Item = Union[Weapon, Supply, Vehicle]


# ── 집 카드 룻 테이블 (0~60) ─────────────────────────────────────────────────
# 낮은 번호 = 일반 아이템, 높은 번호 = 희귀 아이템

_HOUSE_TABLE: list[tuple[int, str, str]] = [
    # (max_roll, category, item_name)
    (5,  "supply",  "붕대"),
    (11, "weapon",  "Deagle"),
    (17, "weapon",  "S686"),
    (22, "weapon",  "수류탄"),
    (27, "weapon",  "화염병"),
    (32, "weapon",  "Beryl"),
    (36, "weapon",  "M416"),
    (40, "supply",  "구급상자"),
    (44, "weapon",  "VSS"),
    (48, "weapon",  "벡터"),
    (51, "vehicle", "UAZ"),
    (54, "weapon",  "AUG"),
    (56, "weapon",  "석궁"),
    (58, "supply",  "연막탄"),
    (59, "weapon",  "Ace45"),
    (60, "supply",  "의료용키트"),
]

# ── 보급 카드 룻 테이블 (0~60) ───────────────────────────────────────────────
# 고성능 무기·차량 중심

_SUPPLY_TABLE: list[tuple[int, str, str]] = [
    (8,  "weapon",  "P90"),
    (15, "supply",  "진통제"),
    (21, "weapon",  "SLR"),
    (26, "weapon",  "SKS"),
    (31, "weapon",  "Mk14"),
    (36, "weapon",  "M24"),
    (40, "weapon",  "AWM"),
    (44, "weapon",  "링스-AMR"),
    (47, "vehicle", "버기"),
    (50, "vehicle", "미라도"),
    (53, "vehicle", "쿠페"),
    (56, "vehicle", "BRDM2"),
    (58, "weapon",  "M249"),
    (59, "weapon",  "박격포"),
    (60, "supply",  "의료용키트"),
]


def _lookup(table: list[tuple[int, str, str]], roll: int) -> Item:
    for max_roll, category, name in table:
        if roll <= max_roll:
            if category == "weapon":
                return WEAPONS[name]
            if category == "supply":
                return SUPPLIES[name]
            if category == "vehicle":
                return VEHICLES[name]
    # fallback
    return WEAPONS["Deagle"]


# ── 카드 클래스 ──────────────────────────────────────────────────────────────

@dataclass
class HouseCard:
    """집 카드 — 사용 시 pre-assigned 번호로 아이템 획득."""
    roll: int = field(default_factory=lambda: random.randint(0, 60))

    def open(self) -> Item:
        return _lookup(_HOUSE_TABLE, self.roll)

    def peek(self) -> str:
        """카드 겉면(번호)만 공개."""
        return f"집 카드 [번호:{self.roll}]"

    def __str__(self) -> str:
        return self.peek()


@dataclass
class SupplyDropCard:
    """보급 카드 — 게임당 1장, 고급 아이템."""
    roll: int = field(default_factory=lambda: random.randint(0, 60))

    def open(self) -> Item:
        return _lookup(_SUPPLY_TABLE, self.roll)

    def peek(self) -> str:
        return f"보급 카드 [번호:{self.roll}] ★"

    def __str__(self) -> str:
        return self.peek()
