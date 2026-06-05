"""무기·지원품·이동수단 정의 (엑셀 데이터 기반)."""
import random
from dataclasses import dataclass


# ── 무기 ────────────────────────────────────────────────────────────────────

@dataclass
class Weapon:
    name:         str
    attack_range: int      # 사정거리
    special:      str = "" # "DOT", "BRDM_disable", "BRDM_pierce"

    def calc_damage(self, brdm_active: bool = False) -> tuple[int, bool, str]:
        """(데미지, 즉사여부, 설명) 반환.
        즉사=True 이면 데미지 값은 무시하고 HP를 0으로 만든다."""
        d = random.randint(1, 6)
        msg_d = f"주사위 {d}"
        n = self.name

        if n == "후라이팬":
            return 0, True,  "💥 후라이팬 한 방! 즉사!"
        if n == "수류탄":
            dmg = d * 15
            return dmg, False, f"{msg_d} → {dmg} 데미지"
        if n == "화염병":
            return 30, False, "🔥 화염! (3턴 DOT 시작)"
        if n == "M416":
            return d * 10, False, f"{msg_d} → {d*10} 데미지"
        if n == "M249":
            dmg = d * 6 * 2
            note = " [BRDM 무력화!]" if brdm_active else ""
            return dmg, False, f"{msg_d} → {dmg} 데미지{note}"
        if n == "M24":
            if d == 6: return 0, True, f"{msg_d} → 🎯 즉사탄!"
            return 50, False, f"{msg_d} → 50 데미지"
        if n == "링스-AMR":   # BRDM 무시
            if d >= 5: return 0, True, f"{msg_d} → 🎯 즉사탄! (BRDM 관통)"
            return 60, False, f"{msg_d} → 60 데미지"
        if n == "벡터":
            return d * 17, False, f"{msg_d} → {d*17} 데미지"
        if n == "Deagle":
            return 25, False, "25 데미지"
        if n == "S686":
            if d >= 3: return 0, True, f"{msg_d} → 🎯 즉사!"
            return 50, False, f"{msg_d} → 50 데미지"
        if n == "DBS":
            if d >= 2: return 0, True, f"{msg_d} → 🎯 즉사!"
            return 60, False, f"{msg_d} → 60 데미지"
        if n == "AWM":
            if d == 6: return 0, True, f"{msg_d} → 🎯 즉사탄!"
            return 80, False, f"{msg_d} → 80 데미지"
        if n == "P90":
            return d * 20, False, f"{msg_d} → {d*20} 데미지"
        if n == "AUG":
            return d * 15, False, f"{msg_d} → {d*15} 데미지"
        if n == "Ace45":
            return d * 16, False, f"{msg_d} → {d*16} 데미지"
        if n == "Beryl":
            return d * 18, False, f"{msg_d} → {d*18} 데미지"
        if n == "SLR":
            dmg = 30 if d <= 3 else 60
            return dmg, False, f"{msg_d} → {dmg} 데미지"
        if n == "SKS":
            dmg = 25 if d <= 3 else 80
            return dmg, False, f"{msg_d} → {dmg} 데미지"
        if n == "Mk14":
            dmg = 30 if d <= 2 else 85
            return dmg, False, f"{msg_d} → {dmg} 데미지"
        if n == "Mini":
            dmg = 25 if d <= 4 else 55
            return dmg, False, f"{msg_d} → {dmg} 데미지"
        if n == "VSS":
            if d <= 4: return 20,  False, f"{msg_d} → 20 데미지"
            if d == 5: return 60,  False, f"{msg_d} → 60 데미지"
            return 120, False, f"{msg_d} → 60×2 더블 히트!"
        if n == "박격포":
            if d == 6: return 80, False, f"{msg_d} → 80 데미지 💥"
            return 0, False, f"{msg_d} → 불발…"
        if n == "석궁":
            if d >= 5: return 0, True, f"{msg_d} → 🎯 즉사!"
            return 0, False, f"{msg_d} → 빗나감"
        return 0, False, "알 수 없는 무기"


# ── 지원품 ──────────────────────────────────────────────────────────────────

@dataclass
class Supply:
    name:        str
    heal_type:   str   # "instant" | "per_turn" | "max_cap" | "shield"
    heal_amount: int
    turns:       int = 1
    description: str = ""

    def label(self) -> str:
        return f"{self.name} [{self.description}]"


# ── 이동수단 ────────────────────────────────────────────────────────────────

@dataclass
class Vehicle:
    name:    str
    speed:   int
    special: str = ""   # "immunity" (BRDM2)

    def label(self) -> str:
        note = " [피격 면역]" if self.special == "immunity" else ""
        return f"{self.name} (이동+{self.speed}칸{note})"


# ── 전체 아이템 레지스트리 ────────────────────────────────────────────────────

WEAPONS: dict[str, Weapon] = {
    "후라이팬":  Weapon("후라이팬",  1),
    "수류탄":    Weapon("수류탄",    10),
    "화염병":    Weapon("화염병",    10,  special="DOT"),
    "M416":      Weapon("M416",      15),
    "M249":      Weapon("M249",      12,  special="BRDM_disable"),
    "M24":       Weapon("M24",       30),
    "링스-AMR":  Weapon("링스-AMR",  35,  special="BRDM_pierce"),
    "벡터":      Weapon("벡터",      10),
    "Deagle":    Weapon("Deagle",    7),
    "S686":      Weapon("S686",      3),
    "DBS":       Weapon("DBS",       3),
    "AWM":       Weapon("AWM",       35),
    "P90":       Weapon("P90",       18),
    "AUG":       Weapon("AUG",       15),
    "Ace45":     Weapon("Ace45",     14),
    "Beryl":     Weapon("Beryl",     12),
    "SLR":       Weapon("SLR",       25),
    "SKS":       Weapon("SKS",       20),
    "Mk14":      Weapon("Mk14",      23),
    "Mini":      Weapon("Mini",      18),
    "VSS":       Weapon("VSS",       15),
    "박격포":    Weapon("박격포",    60),
    "석궁":      Weapon("석궁",      10),
}

SUPPLIES: dict[str, Supply] = {
    "구급상자":   Supply("구급상자",   "max_cap",  70,  description="HP 70까지 회복"),
    "의료용키트": Supply("의료용키트", "max_cap",  100, description="HP 100까지 회복"),
    "드링크":     Supply("드링크",     "per_turn", 10,  turns=3, description="매 턴 10 회복 (3턴)"),
    "진통제":     Supply("진통제",     "per_turn", 15,  turns=3, description="매 턴 15 회복 (3턴)"),
    "붕대":       Supply("붕대",       "instant",  30,  description="즉시 30 회복"),
    "연막탄":     Supply("연막탄",     "shield",   0,   turns=2, description="2턴 피격 면역"),
}

VEHICLES: dict[str, Vehicle] = {
    "UAZ":   Vehicle("UAZ",   4),
    "쿠페":  Vehicle("쿠페",  6),
    "미라도": Vehicle("미라도", 5),
    "BRDM2": Vehicle("BRDM2", 3, special="immunity"),
    "버기":  Vehicle("버기",  5),
}
