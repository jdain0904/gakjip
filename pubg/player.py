"""플레이어 상태 관리."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

MAX_HP = 100
MAX_WEAPON_SLOTS = 2


@dataclass
class ActiveEffect:
    kind:       str
    value:      int
    turns_left: int


class Player:
    def __init__(self, pid: int, name: str, is_human: bool = False):
        self.pid      = pid
        self.name     = name
        self.is_human = is_human

        self.hp       = MAX_HP
        self.position = 0
        self.is_alive = True

        from .items import P18C_PISTOL
        self.pistol = P18C_PISTOL.copy()          # 항상 장비된 기본 권총
        self.weapon_slots: list = []              # 최대 2 (총기만, P18C 제외)
        self.ammo: dict[str, int] = {             # 구경 → 발 수 공용 풀
            self.pistol.caliber: self.pistol.starter_ammo
        }
        self.inventory: list = []                 # 카드 / 지원품 / 이동수단 / 투척·근접
        self.effects:   list[ActiveEffect] = []

    # ── HP ─────────────────────────────────────────────────────────────────
    def take_damage(self, amount: int) -> int:
        if self.has_effect("shield") or self.has_effect("brdm_immune"):
            return 0
        self.hp = max(0, self.hp - amount)
        if self.hp <= 0:
            self.is_alive = False
        return amount

    def instant_kill(self) -> bool:
        if self.has_effect("shield") or self.has_effect("brdm_immune"):
            return False
        self.hp = 0
        self.is_alive = False
        return True

    def heal(self, amount: int, max_cap: int = MAX_HP):
        self.hp = min(max_cap, self.hp + amount)

    # ── 지속 효과 ────────────────────────────────────────────────────────────
    def add_effect(self, effect: ActiveEffect):
        self.effects = [e for e in self.effects if e.kind != effect.kind]
        self.effects.append(effect)

    def has_effect(self, kind: str) -> bool:
        return any(e.kind == kind for e in self.effects)

    def tick_effects(self) -> list[str]:
        msgs: list[str] = []
        remaining: list[ActiveEffect] = []
        for eff in self.effects:
            if eff.kind == "fire":
                self.hp = max(0, self.hp - eff.value)
                if self.hp <= 0:
                    self.is_alive = False
                msgs.append(f"🔥 {self.name} 화염 피해 {eff.value} (남은 {eff.turns_left-1}턴)")
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

    # ── 무기 슬롯 관리 ───────────────────────────────────────────────────────
    def add_weapon(self, weapon) -> Optional[object]:
        """
        총기 → weapon_slots (최대 2).
        비총기(투척·근접) → inventory.
        슬롯 꽉 찬 경우 사정거리 최단 무기 교체 후 반환.
        """
        if not weapon.is_firearm:
            self.inventory.append(weapon)
            return None
        # 스타터 탄약 지급
        if weapon.starter_ammo > 0:
            self.ammo[weapon.caliber] = self.ammo.get(weapon.caliber, 0) + weapon.starter_ammo

        if len(self.weapon_slots) < MAX_WEAPON_SLOTS:
            self.weapon_slots.append(weapon)
            return None
        # 슬롯 꽉 참 → 사정거리 최소 무기 교체
        min_idx = min(range(len(self.weapon_slots)),
                      key=lambda i: self.weapon_slots[i].attack_range)
        displaced = self.weapon_slots[min_idx]
        self.weapon_slots[min_idx] = weapon
        return displaced

    def add_ammo(self, ammo) -> None:
        self.ammo[ammo.caliber] = self.ammo.get(ammo.caliber, 0) + ammo.count

    def has_ammo_for(self, weapon) -> bool:
        if weapon.caliber is None:
            return True
        return self.ammo.get(weapon.caliber, 0) >= weapon.ammo_per_shot

    def consume_ammo(self, weapon) -> None:
        if weapon.caliber:
            self.ammo[weapon.caliber] = max(0, self.ammo.get(weapon.caliber, 0) - weapon.ammo_per_shot)

    def all_weapons(self) -> list:
        """pistol + weapon_slots + 인벤토리 내 투척·근접."""
        from .items import Weapon
        thrown = [i for i in self.inventory if isinstance(i, Weapon)]
        return [self.pistol] + self.weapon_slots + thrown

    # ── 인벤토리 (비총기) ────────────────────────────────────────────────────
    def add_item(self, item) -> Optional[object]:
        from .items import Weapon, Ammo
        if isinstance(item, Weapon):
            return self.add_weapon(item)
        if isinstance(item, Ammo):
            self.add_ammo(item)
            return None
        self.inventory.append(item)
        return None

    def remove_item(self, item) -> None:
        if item in self.inventory:
            self.inventory.remove(item)

    def has_weapon(self) -> bool:
        return bool(self.weapon_slots)

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
        eff = ", ".join(e.kind for e in self.effects) or "없음"
        return f"HP:{self.hp}  위치:{self.position}  효과:[{eff}]"

    def ammo_summary(self) -> str:
        parts = [f"{cal}:{cnt}" for cal, cnt in self.ammo.items() if cnt > 0]
        return "  ".join(parts) if parts else "(탄약없음)"

    def inventory_lines(self) -> list[str]:
        lines = [
            f"  [P18C] {self.pistol.name}  탄:{self.ammo.get(self.pistol.caliber, 0)}"
        ]
        for i, w in enumerate(self.weapon_slots):
            cnt = self.ammo.get(w.caliber, 0) if w.caliber else "∞"
            lines.append(f"  [W{i+1}] {w.name}  {w.cal_label()}  탄:{cnt}")
        for idx, item in enumerate(self.inventory):
            lines.append(f"  [{idx+1}] {item}")
        return lines
