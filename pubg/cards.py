"""집 카드 & 보급 카드 — 랜덤 0~60 번호로 아이템 결정."""
import random
from dataclasses import dataclass, field
from typing import Union

from .items import (
    Weapon, Supply, Vehicle, Ammo, WEAPONS, SUPPLIES, VEHICLES,
    CAL_556, CAL_762, CAL_9MM, CAL_12G, CAL_50AE, CAL_BOLT,
    CAL_300, CAL_50BMG, CAL_MORTAR, SPECIAL_CALIBERS,
)

Item = Union[Weapon, Supply, Vehicle, Ammo]

# (max_roll, category, name_or_caliber, ammo_caliber|None, ammo_count)
# category "ammo" → pure ammo drop; name_or_caliber = caliber string

_HOUSE_TABLE: list[tuple[int, str, str, str | None, int]] = [
    (4,  "supply",  "붕대",    None,     0),
    (9,  "ammo",    CAL_9MM,   CAL_9MM,  40),
    (14, "weapon",  "Deagle",  CAL_50AE, 20),
    (19, "weapon",  "S686",    CAL_12G,  16),
    (23, "thrown",  "수류탄",  None,     0),
    (27, "thrown",  "화염병",  None,     0),
    (32, "weapon",  "Beryl",   CAL_762,  20),
    (37, "weapon",  "M416",    CAL_556,  30),
    (41, "supply",  "구급상자", None,    0),
    (45, "ammo",    CAL_556,   CAL_556,  60),
    (48, "weapon",  "벡터",    CAL_9MM,  30),
    (51, "vehicle", "UAZ",     None,     0),
    (54, "weapon",  "AUG",     CAL_556,  30),
    (56, "weapon",  "VSS",     CAL_9MM,  30),
    (58, "weapon",  "석궁",    CAL_BOLT, 10),
    (59, "weapon",  "Ace45",   CAL_9MM,  25),
    (60, "supply",  "연막탄",  None,     0),
]

_SUPPLY_TABLE: list[tuple[int, str, str, str | None, int]] = [
    (7,  "weapon",  "P90",      CAL_9MM,    40),
    (13, "supply",  "진통제",   None,       0),
    (18, "weapon",  "SLR",      CAL_762,    20),
    (23, "weapon",  "SKS",      CAL_762,    20),
    (28, "weapon",  "Mk14",     CAL_762,    20),
    (33, "weapon",  "M24",      CAL_762,    10),
    (38, "weapon",  "AWM",      CAL_300,    20),
    (42, "weapon",  "링스-AMR", CAL_50BMG,  10),
    (46, "vehicle", "버기",     None,       0),
    (49, "vehicle", "미라도",   None,       0),
    (52, "vehicle", "쿠페",     None,       0),
    (55, "vehicle", "BRDM2",    None,       0),
    (57, "weapon",  "M249",     CAL_556,    75),
    (59, "weapon",  "박격포",   CAL_MORTAR, 3),
    (60, "supply",  "의료용키트", None,     0),
]


def _lookup(table: list, roll: int) -> list[Item]:
    for max_roll, category, name, ammo_cal, ammo_cnt in table:
        if roll <= max_roll:
            result: list[Item] = []
            if category == "ammo":
                result.append(Ammo(name, ammo_cnt, name in SPECIAL_CALIBERS))
            elif category in ("weapon",):
                w = WEAPONS[name].copy()
                result.append(w)
                if ammo_cal and ammo_cnt > 0:
                    result.append(Ammo(ammo_cal, ammo_cnt, ammo_cal in SPECIAL_CALIBERS))
            elif category == "thrown":
                result.append(WEAPONS[name].copy())
            elif category == "supply":
                result.append(SUPPLIES[name])
            elif category == "vehicle":
                result.append(VEHICLES[name])
            return result
    return [WEAPONS["Deagle"].copy(), Ammo(CAL_50AE, 10)]


@dataclass
class HouseCard:
    roll: int = field(default_factory=lambda: random.randint(0, 60))

    def open(self) -> list[Item]:
        return _lookup(_HOUSE_TABLE, self.roll)

    def peek(self) -> str:
        return f"집 카드 [번호:{self.roll}]"

    def __str__(self) -> str:
        return self.peek()


@dataclass
class SupplyDropCard:
    roll: int = field(default_factory=lambda: random.randint(0, 60))

    def open(self) -> list[Item]:
        return _lookup(_SUPPLY_TABLE, self.roll)

    def peek(self) -> str:
        return f"보급 카드 [번호:{self.roll}] ★"

    def __str__(self) -> str:
        return self.peek()
