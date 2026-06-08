"""무기·지원품·이동수단·탄약 정의 (PUBG 실제 구경 기반)."""
import random
from typing import Optional

# ── 탄약 구경 상수 ─────────────────────────────────────────────────────────────
CAL_556    = "5.56mm"
CAL_762    = "7.62mm"
CAL_9MM    = "9mm"
CAL_12G    = "12 Gauge"
CAL_50AE   = ".50 AE"
CAL_300    = ".300 Magnum"  # ★ 특수 (AWM)
CAL_50BMG  = ".50 BMG"      # ★ 특수 (링스)
CAL_MORTAR = "박격포탄"      # ★ 특수
CAL_BOLT   = "볼트"          # 석궁

SPECIAL_CALIBERS = {CAL_300, CAL_50BMG, CAL_MORTAR}

# 탄약 아이콘
_CAL_ICON = {
    CAL_556:    "🟡",
    CAL_762:    "🟠",
    CAL_9MM:    "⚫",
    CAL_12G:    "🔴",
    CAL_50AE:   "🔵",
    CAL_300:    "⭐",
    CAL_50BMG:  "⭐",
    CAL_MORTAR: "💣",
    CAL_BOLT:   "🏹",
}


# ─────────────────────────────────────────────────────────────────────────────
# Weapon
# ─────────────────────────────────────────────────────────────────────────────

class Weapon:
    def __init__(self, name: str, attack_range: int,
                 caliber: Optional[str],
                 starter_ammo: int = 0,
                 ammo_per_shot: int = 1,
                 special: str = ""):
        self.name          = name
        self.attack_range  = attack_range
        self.caliber       = caliber        # None = 근접 / 투척
        self.starter_ammo  = starter_ammo   # 수령 시 지급
        self.ammo_per_shot = ammo_per_shot
        self.special       = special

    def copy(self) -> "Weapon":
        return Weapon(self.name, self.attack_range, self.caliber,
                      self.starter_ammo, self.ammo_per_shot, self.special)

    @property
    def is_special_ammo(self) -> bool:
        return self.caliber in SPECIAL_CALIBERS

    @property
    def is_firearm(self) -> bool:
        """탄약 슬롯을 차지하는 총기 여부 (근접/투척 제외)."""
        return self.caliber is not None

    @property
    def category(self) -> str:
        if self.caliber is None:
            return "근접" if self.name == "후라이팬" else "투척"
        if self.attack_range <= 7:  return "권총"
        if self.attack_range <= 10: return "기관단총"
        if self.attack_range <= 18: return "돌격소총"
        if self.attack_range <= 25: return "DMR"
        if self.attack_range < 60:  return "저격소총"
        return "특수"

    def cal_icon(self) -> str:
        return _CAL_ICON.get(self.caliber, "•") if self.caliber else "—"

    def cal_label(self) -> str:
        if not self.caliber:
            return "—"
        star = "★" if self.is_special_ammo else ""
        return f"{self.caliber}{star}"

    def damage_desc(self) -> str:
        n = self.name
        if n == "후라이팬":  return "즉사"
        if n == "수류탄":    return "d6×15"
        if n == "화염병":    return "30/턴(3턴)"
        if n == "M416":      return "d6×10"
        if n == "M249":      return "d6×6×2발"
        if n == "M24":       return "6=즉사 / 50"
        if n == "링스-AMR":  return "5,6=즉사 / 60"
        if n == "벡터":      return "d6×17"
        if n == "Deagle":    return "25"
        if n == "S686":      return "3+=즉사 / 50"
        if n == "DBS":       return "2+=즉사 / 60"
        if n == "AWM":       return "6=즉사 / 80"
        if n == "P90":       return "d6×20"
        if n == "AUG":       return "d6×15"
        if n == "Ace45":     return "d6×16"
        if n == "Beryl":     return "d6×18"
        if n == "SLR":       return "≤3:30 / 60"
        if n == "SKS":       return "≤3:25 / 80"
        if n == "Mk14":      return "≤2:30 / 85"
        if n == "Mini":      return "≤4:25 / 55"
        if n == "VSS":       return "≤4:20/5=60/6=×2"
        if n == "박격포":    return "6=80 / 불발"
        if n == "석궁":      return "5+=즉사"
        if n == "P18C":      return "d6×10"
        return "?"

    def calc_damage(self, brdm_active: bool = False) -> tuple:
        """(데미지, 즉사여부, 설명) 반환."""
        d  = random.randint(1, 6)
        md = f"d{d}"
        n  = self.name
        if n == "후라이팬":  return (0, True,  f"💥즉사!")
        if n == "수류탄":    return (d*15, False, f"{md}→{d*15}")
        if n == "화염병":    return (30, False, "🔥화염DOT")
        if n == "M416":      return (d*10, False, f"{md}→{d*10}")
        if n == "M249":
            dmg = d*6*2
            note = "[BRDM무력화]" if brdm_active else ""
            return (dmg, False, f"{md}→{dmg}{note}")
        if n == "M24":
            return (0, True, f"{md}→즉사!") if d==6 else (50, False, f"{md}→50")
        if n == "링스-AMR":
            return (0, True, f"{md}→즉사!(BRDM관통)") if d>=5 else (60, False, f"{md}→60")
        if n == "벡터":     return (d*17, False, f"{md}→{d*17}")
        if n == "Deagle":   return (25, False, "25")
        if n == "S686":     return (0, True, f"{md}→즉사!") if d>=3 else (50, False, f"{md}→50")
        if n == "DBS":      return (0, True, f"{md}→즉사!") if d>=2 else (60, False, f"{md}→60")
        if n == "AWM":      return (0, True, f"{md}→즉사!") if d==6 else (80, False, f"{md}→80")
        if n == "P90":      return (d*20, False, f"{md}→{d*20}")
        if n == "AUG":      return (d*15, False, f"{md}→{d*15}")
        if n == "Ace45":    return (d*16, False, f"{md}→{d*16}")
        if n == "Beryl":    return (d*18, False, f"{md}→{d*18}")
        if n == "SLR":
            dmg = 30 if d<=3 else 60; return (dmg, False, f"{md}→{dmg}")
        if n == "SKS":
            dmg = 25 if d<=3 else 80; return (dmg, False, f"{md}→{dmg}")
        if n == "Mk14":
            dmg = 30 if d<=2 else 85; return (dmg, False, f"{md}→{dmg}")
        if n == "Mini":
            dmg = 25 if d<=4 else 55; return (dmg, False, f"{md}→{dmg}")
        if n == "VSS":
            if d<=4: return (20, False, f"{md}→20")
            if d==5: return (60, False, f"{md}→60")
            return (120, False, f"{md}→60×2!")
        if n == "박격포":
            return (80, False, f"{md}→80") if d==6 else (0, False, f"{md}→불발")
        if n == "석궁":
            return (0, True, f"{md}→즉사!") if d>=5 else (0, False, f"{md}→빗나감")
        if n == "P18C":     return (d*10, False, f"{md}→{d*10}")
        return (0, False, "?")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Weapon({self.name})"


# ─────────────────────────────────────────────────────────────────────────────
# Ammo
# ─────────────────────────────────────────────────────────────────────────────

class Ammo:
    def __init__(self, caliber: str, count: int, is_special: bool = False):
        self.caliber    = caliber
        self.count      = count
        self.is_special = is_special

    @property
    def name(self) -> str:
        star = "★" if self.is_special else ""
        return f"{self.caliber}{star}"

    @property
    def icon(self) -> str:
        return _CAL_ICON.get(self.caliber, "•")

    def __str__(self) -> str:
        return f"{self.name} ×{self.count}"


# ─────────────────────────────────────────────────────────────────────────────
# Supply / Vehicle
# ─────────────────────────────────────────────────────────────────────────────

class Supply:
    def __init__(self, name, heal_type, heal_amount, turns=1, description=""):
        self.name        = name
        self.heal_type   = heal_type  # instant|per_turn|max_cap|shield
        self.heal_amount = heal_amount
        self.turns       = turns
        self.description = description

    def __str__(self): return self.name
    def __repr__(self): return f"Supply({self.name})"


class Vehicle:
    def __init__(self, name, speed, special=""):
        self.name    = name
        self.speed   = speed
        self.special = special  # "immunity" for BRDM2

    def __str__(self): return self.name
    def __repr__(self): return f"Vehicle({self.name})"


# ─────────────────────────────────────────────────────────────────────────────
# 레지스트리
# ─────────────────────────────────────────────────────────────────────────────

# 기본 권총 (항상 장비)
P18C_PISTOL = Weapon("P18C", 10, CAL_9MM, 15, 1)

WEAPONS: dict[str, Weapon] = {
    # 근접
    "후라이팬":  Weapon("후라이팬",  1,   None,    1,  1),
    # 투척
    "수류탄":    Weapon("수류탄",    10,  None,    3,  1),
    "화염병":    Weapon("화염병",    10,  None,    2,  1,  special="DOT"),
    # 권총
    "Deagle":    Weapon("Deagle",    7,   CAL_50AE, 10, 1),
    # 산탄총
    "S686":      Weapon("S686",      3,   CAL_12G, 8,  2),
    "DBS":       Weapon("DBS",       3,   CAL_12G, 8,  2),
    # 기관단총 (9mm)
    "벡터":      Weapon("벡터",      10,  CAL_9MM, 30, 1),
    "P90":       Weapon("P90",       18,  CAL_9MM, 40, 1),
    "Ace45":     Weapon("Ace45",     14,  CAL_9MM, 25, 1),
    "VSS":       Weapon("VSS",       15,  CAL_9MM, 30, 1),
    # 돌격소총 (5.56mm)
    "M416":      Weapon("M416",      15,  CAL_556, 30, 1),
    "AUG":       Weapon("AUG",       15,  CAL_556, 30, 1),
    "Mini":      Weapon("Mini",      18,  CAL_556, 30, 1),
    "M249":      Weapon("M249",      12,  CAL_556, 75, 1,  special="BRDM_disable"),
    # 돌격소총 (7.62mm)
    "Beryl":     Weapon("Beryl",     12,  CAL_762, 20, 1),
    # DMR (7.62mm)
    "SLR":       Weapon("SLR",       25,  CAL_762, 10, 1),
    "SKS":       Weapon("SKS",       20,  CAL_762, 10, 1),
    "Mk14":      Weapon("Mk14",      23,  CAL_762, 10, 1),
    # 저격 (7.62mm)
    "M24":       Weapon("M24",       30,  CAL_762,  5, 1),
    # 저격 (특수탄 ★)
    "AWM":       Weapon("AWM",       35,  CAL_300, 20, 1),
    "링스-AMR":  Weapon("링스-AMR",  35,  CAL_50BMG, 10, 1, special="BRDM_pierce"),
    # 특수
    "박격포":    Weapon("박격포",    60,  CAL_MORTAR, 3, 1),
    "석궁":      Weapon("석궁",      10,  CAL_BOLT, 10, 1),
}

SUPPLIES: dict[str, Supply] = {
    "구급상자":   Supply("구급상자",   "max_cap",  70,  description="HP 70까지"),
    "의료용키트": Supply("의료용키트", "max_cap",  100, description="HP 100까지"),
    "드링크":     Supply("드링크",     "per_turn", 10,  turns=3, description="3턴 +10"),
    "진통제":     Supply("진통제",     "per_turn", 15,  turns=3, description="3턴 +15"),
    "붕대":       Supply("붕대",       "instant",  30,  description="+30 즉시"),
    "연막탄":     Supply("연막탄",     "shield",   0,   turns=2, description="2턴 면역"),
}

VEHICLES: dict[str, Vehicle] = {
    "UAZ":    Vehicle("UAZ",   4),
    "쿠페":   Vehicle("쿠페",  6),
    "미라도": Vehicle("미라도", 5),
    "BRDM2":  Vehicle("BRDM2", 3, special="immunity"),
    "버기":   Vehicle("버기",  5),
}
