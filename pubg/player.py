"""플레이어 상태 관리."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .items import Weapon, Supply, Vehicle
    from .cards import HouseCard, SupplyDropCard

CardItem = Union["HouseCard", "SupplyDropCard", "Weapon", "Supply", "Vehicle"]

MAX_HP = 100


@dataclass
class ActiveEffect:
    kind:        str   # "fire", "heal_over_time", "shield", "brdm_immune"
    value:       int   # 데미지 or 회복량
    turns_left:  int


class Player:
    def __init__(self, pid: int, name: str, is_human: bool = False):
        self.pid      = pid
        self.name     = name
        self.is_human = is_human

        self.hp        = MAX_HP
        self.position  = 0    # P1=0, P2=50 (환경이 설정)
        self.is_alive  = True

        self.inventory: list[CardItem] = []  # 모든 보유 카드/아이템
        self.effects:   list[ActiveEffect] = []

    # ── HP ─────────────────────────────────────────────────────────────────
    def take_damage(self, amount: int) -> int:
        """실제 피해량 반환 (shield 적용 후)."""
        if self.has_effect("shield") or self.has_effect("brdm_immune"):
            return 0
        self.hp = max(0, self.hp - amount)
        if self.hp <= 0:
            self.is_alive = False
        return amount

    def instant_kill(self) -> bool:
        """즉사 시도 — shield/brdm_immune이면 실패."""
        if self.has_effect("shield") or self.has_effect("brdm_immune"):
            return False
        self.hp       = 0
        self.is_alive = False
        return True

    def heal(self, amount: int, max_cap: int = MAX_HP):
        self.hp = min(max_cap, self.hp + amount)

    def heal_to_cap(self, cap: int):
        self.hp = min(cap, max(self.hp, 1) + (cap - self.hp))  # 현재 HP→cap 까지
        self.hp = min(cap, self.hp)

    # ── 지속 효과 ────────────────────────────────────────────────────────────
    def add_effect(self, effect: ActiveEffect):
        # 같은 종류 갱신
        self.effects = [e for e in self.effects if e.kind != effect.kind]
        self.effects.append(effect)

    def has_effect(self, kind: str) -> bool:
        return any(e.kind == kind for e in self.effects)

    def tick_effects(self) -> list[str]:
        """턴 시작 시 지속 효과 처리. 메시지 목록 반환."""
        msgs: list[str] = []
        remaining: list[ActiveEffect] = []
        for eff in self.effects:
            if eff.kind == "fire":
                self.hp = max(0, self.hp - eff.value)
                if self.hp <= 0:
                    self.is_alive = False
                msgs.append(f"🔥 {self.name} 화염 피해 {eff.value} (남은 턴 {eff.turns_left-1})")
            elif eff.kind == "heal_over_time":
                self.hp = min(MAX_HP, self.hp + eff.value)
                msgs.append(f"💉 {self.name} 회복 +{eff.value} → HP {self.hp}")
            elif eff.kind in ("shield", "brdm_immune"):
                msgs.append(f"🛡️  {self.name} {eff.kind} 유지 ({eff.turns_left-1}턴 남음)")

            eff.turns_left -= 1
            if eff.turns_left > 0:
                remaining.append(eff)
        self.effects = remaining
        return msgs

    # ── 인벤토리 ─────────────────────────────────────────────────────────────
    def add_item(self, item: CardItem):
        self.inventory.append(item)

    def remove_item(self, item: CardItem):
        if item in self.inventory:
            self.inventory.remove(item)

    def has_weapon(self) -> bool:
        from .items import Weapon
        return any(isinstance(i, Weapon) for i in self.inventory)

    def weapons(self) -> list:
        from .items import Weapon
        return [i for i in self.inventory if isinstance(i, Weapon)]

    def house_cards(self) -> list:
        from .cards import HouseCard
        return [i for i in self.inventory if isinstance(i, HouseCard)]

    def supply_cards(self) -> list:
        from .cards import SupplyDropCard
        return [i for i in self.inventory if isinstance(i, SupplyDropCard)]

    def supply_items(self) -> list:
        from .items import Supply
        return [i for i in self.inventory if isinstance(i, Supply)]

    def vehicles(self) -> list:
        from .items import Vehicle
        return [i for i in self.inventory if isinstance(i, Vehicle)]

    # ── 표시 ─────────────────────────────────────────────────────────────────
    def hp_bar(self, width: int = 20) -> str:
        filled = int(self.hp / MAX_HP * width)
        color  = "🟥" if self.hp < 30 else ("🟨" if self.hp < 60 else "🟩")
        return color * filled + "⬛" * (width - filled) + f" {self.hp}/{MAX_HP}"

    def status_summary(self) -> str:
        effects = ", ".join(e.kind for e in self.effects) or "없음"
        return f"HP:{self.hp}  위치:{self.position}  효과:[{effects}]"

    def inventory_lines(self) -> list[str]:
        lines = []
        for idx, item in enumerate(self.inventory):
            lines.append(f"  [{idx+1}] {item}")
        return lines if lines else ["  (없음)"]
