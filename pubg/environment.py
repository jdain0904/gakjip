"""GameEnv — PUBG 보드게임 핵심 환경."""
from __future__ import annotations
import random
from typing import Optional

from .player import Player, ActiveEffect, MAX_HP
from .items import Weapon, Supply, Vehicle, Ammo
from .cards import HouseCard, SupplyDropCard

ACTION_MOVE     = "move"
ACTION_USE_CARD = "use_card"
ACTION_PASS     = "pass"

INITIAL_DISTANCE = 50
BLUEZONE_DAMAGE  = 20
REDZONE_DAMAGE   = 50


class GameEnv:
    def __init__(self, p1_name: str = "플레이어1", p2_name: str = "플레이어2",
                 p1_human: bool = True, p2_human: bool = False):
        self.p1 = Player(0, p1_name, p1_human)
        self.p2 = Player(1, p2_name, p2_human)

        self.turn:     int  = 1
        self.cur_pid:  int  = 0
        self.distance: int  = INITIAL_DISTANCE
        self.done:     bool = False
        self.winner:   Optional[Player] = None
        self.log:      list[str] = []

        self.last_drawn_items: list  = []
        self.last_draw_is_supply: bool = False

        self._supply_card_remaining: int = 1

        self.reset()

    # ── 초기화 ────────────────────────────────────────────────────────────────
    def reset(self):
        self.p1 = Player(self.p1.pid, self.p1.name, self.p1.is_human)
        self.p2 = Player(self.p2.pid, self.p2.name, self.p2.is_human)
        self.p1.position = 0
        self.p2.position = INITIAL_DISTANCE
        self.turn     = 1
        self.cur_pid  = 0
        self.distance = INITIAL_DISTANCE
        self.done     = False
        self.winner   = None
        self.log      = []
        self.last_drawn_items    = []
        self.last_draw_is_supply = False
        self._supply_card_remaining = 1

        for _ in range(2):
            self.p1.add_item(HouseCard())
            self.p2.add_item(HouseCard())

        lucky = random.choice([self.p1, self.p2])
        lucky.add_item(SupplyDropCard())
        self._log(f"★ 보급 카드가 {lucky.name}에게 배정되었습니다.")
        self._log(f"=== 게임 시작! (초기 거리: {INITIAL_DISTANCE}) ===")
        return self._get_state()

    # ── 공개 인터페이스 ───────────────────────────────────────────────────────
    def current_player(self) -> Player:
        return self.p1 if self.cur_pid == 0 else self.p2

    def opponent(self) -> Player:
        return self.p2 if self.cur_pid == 0 else self.p1

    def flush_drawn_items(self) -> tuple[list, bool]:
        items, is_sup = self.last_drawn_items[:], self.last_draw_is_supply
        self.last_drawn_items    = []
        self.last_draw_is_supply = False
        return items, is_sup

    def get_valid_actions(self) -> list[dict]:
        p = self.current_player()
        actions: list[dict] = []

        if self.distance > 0:
            actions.append({"type": ACTION_MOVE, "label": "이동 (1칸 접근)"})

        # Pistol attack
        pistol = p.pistol
        in_range   = self.distance <= pistol.attack_range
        has_ammo   = p.has_ammo_for(pistol)
        ammo_cnt   = p.ammo.get(pistol.caliber, 0)
        if has_ammo:
            note   = f"거리{self.distance}≤{pistol.attack_range}" if in_range else "사거리부족"
            actions.append({
                "type":       ACTION_USE_CARD,
                "weapon_idx": -1,
                "label":      f"공격[P]: {pistol.name} [{note}] 탄:{ammo_cnt}",
                "usable":     in_range,
            })

        # Weapon slot attacks
        for i, w in enumerate(p.weapon_slots):
            in_r = self.distance <= w.attack_range
            h_am = p.has_ammo_for(w)
            cnt  = p.ammo.get(w.caliber, 0) if w.caliber else "∞"
            if not in_r:
                note = f"사거리부족({self.distance}>{w.attack_range})"
            elif not h_am:
                note = "탄약없음"
            else:
                note = f"거리{self.distance}≤{w.attack_range}"
            actions.append({
                "type":       ACTION_USE_CARD,
                "weapon_idx": i,
                "label":      f"공격[W{i+1}]: {w.name} [{note}] 탄:{cnt}",
                "usable":     in_r and h_am,
            })

        # Inventory items (cards, thrown/melee, supplies, vehicles)
        for idx, item in enumerate(p.inventory):
            act = self._make_card_action(item, idx)
            if act:
                actions.append(act)

        if not actions:
            actions.append({"type": ACTION_PASS, "label": "패스"})
        return actions

    def step(self, action: dict) -> tuple[dict, bool]:
        if self.done:
            return self._get_state(), True

        p   = self.current_player()
        opp = self.opponent()

        atype = action["type"]

        if atype == ACTION_MOVE:
            self._do_move(p, action.get("speed", 1))

        elif atype == ACTION_USE_CARD:
            if "weapon_idx" in action:
                idx    = action["weapon_idx"]
                weapon = p.pistol if idx == -1 else p.weapon_slots[idx]
                self._do_attack(p, opp, weapon)
            else:
                idx  = action["card_idx"]
                item = p.inventory[idx]
                self._do_use_card(p, opp, item)

        elif atype == ACTION_PASS:
            self._log(f"{p.name}: 패스")

        self._end_turn()
        return self._get_state(), self.done

    # ── 이동 ─────────────────────────────────────────────────────────────────
    def _do_move(self, p: Player, speed: int = 1):
        old = self.distance
        self.distance = max(0, self.distance - speed)
        p.position  += speed if p.pid == 0 else -speed
        moved = old - self.distance
        self._log(f"🚶 {p.name}이(가) {moved}칸 이동 → 거리 {self.distance}")

    # ── 카드/인벤토리 아이템 사용 ─────────────────────────────────────────────
    def _do_use_card(self, p: Player, opp: Player, item):
        p.remove_item(item)

        if isinstance(item, (HouseCard, SupplyDropCard)):
            is_sup = isinstance(item, SupplyDropCard)
            kind   = "보급 카드" if is_sup else "집 카드"
            self._log(f"📦 {p.name}: {kind} [번호:{item.roll}] 개봉!")
            items_gained = item.open()
            self.last_drawn_items    = list(items_gained)
            self.last_draw_is_supply = is_sup
            for gained in items_gained:
                self._give_item(p, gained)
            return

        if isinstance(item, Weapon):
            # 투척/근접은 인벤에서 이미 제거됨 → 공격 후 소모
            self._do_attack(p, opp, item, from_inventory=True)
            return

        if isinstance(item, Supply):
            self._do_supply(p, item)
            return

        if isinstance(item, Vehicle):
            self._log(f"🚗 {p.name}: {item.name} 탑승! +{item.speed}칸 이동")
            self._do_move(p, item.speed)
            if item.special == "immunity":
                p.add_effect(ActiveEffect("brdm_immune", 0, 1))
                self._log(f"  🛡️  BRDM2 방호 활성 (피격 면역, 링스 제외)")
            return

    def _give_item(self, p: Player, item):
        if isinstance(item, Weapon):
            displaced = p.add_weapon(item)
            self._log(f"  🔫 {item.name} 획득! (사거리:{item.attack_range}  {item.cal_label()})")
            if displaced:
                self._log(f"  ↩️  슬롯 초과 → {displaced.name} 버림")
        elif isinstance(item, Ammo):
            p.add_ammo(item)
            total = p.ammo.get(item.caliber, 0)
            star  = "★" if item.is_special else ""
            self._log(f"  🔶 {item.caliber}{star} ×{item.count} 획득 (보유:{total}발)")
        elif isinstance(item, Supply):
            p.add_item(item)
            self._log(f"  💊 {item.name} 획득")
        elif isinstance(item, Vehicle):
            p.add_item(item)
            self._log(f"  🚗 {item.name} 획득")

    # ── 공격 ─────────────────────────────────────────────────────────────────
    def _do_attack(self, attacker: Player, target: Player, weapon: Weapon,
                   from_inventory: bool = False):
        if self.distance > weapon.attack_range:
            self._log(f"  ❌ 거리 {self.distance} > 사정거리 {weapon.attack_range}")
            if from_inventory:
                attacker.inventory.append(weapon)  # 투척 무기 복구
            return

        if weapon.is_firearm and not attacker.has_ammo_for(weapon):
            self._log(f"  ❌ {weapon.name} 탄약 없음! ({weapon.caliber})")
            return

        brdm_on = target.has_effect("brdm_immune")
        if weapon.special == "BRDM_pierce":
            brdm_on = False

        dmg, is_kill, desc = weapon.calc_damage(brdm_on)
        self._log(f"🔫 {attacker.name} → {target.name}  [{weapon.name}]  {desc}")

        if weapon.is_firearm:
            attacker.consume_ammo(weapon)
            rem = attacker.ammo.get(weapon.caliber, 0)
            self._log(f"  탄약 소모 → {weapon.caliber} 잔탄 {rem}발")

        if is_kill:
            killed = target.instant_kill()
            if killed:
                self._log(f"  💀 {target.name} 즉사!")
            else:
                self._log(f"  🛡️  {target.name} 방호로 즉사 무효!")
        else:
            actual = target.take_damage(dmg)
            if actual == 0:
                self._log(f"  🛡️  {target.name} 방호로 피해 차단!")
            else:
                self._log(f"  💥 {target.name} HP {target.hp + actual} → {target.hp}")

        if weapon.name == "화염병" and not target.has_effect("shield"):
            target.add_effect(ActiveEffect("fire", 30, 3))

        if weapon.name == "M249" and target.has_effect("brdm_immune"):
            target.effects = [e for e in target.effects if e.kind != "brdm_immune"]
            self._log(f"  ⚡ BRDM2 무력화!")

    # ── 지원품 ───────────────────────────────────────────────────────────────
    def _do_supply(self, p: Player, supply: Supply):
        if supply.heal_type == "instant":
            p.heal(supply.heal_amount)
            self._log(f"💊 {p.name} {supply.name} → HP +{supply.heal_amount} ({p.hp})")
        elif supply.heal_type == "max_cap":
            old  = p.hp
            p.hp = min(MAX_HP, max(p.hp, supply.heal_amount))
            self._log(f"💊 {p.name} {supply.name} → HP {old} → {p.hp}")
        elif supply.heal_type == "per_turn":
            p.add_effect(ActiveEffect("heal_over_time", supply.heal_amount, supply.turns))
            self._log(f"💊 {p.name} {supply.name} → {supply.turns}턴 매 +{supply.heal_amount}")
        elif supply.heal_type == "shield":
            p.add_effect(ActiveEffect("shield", 0, supply.turns))
            self._log(f"💊 {p.name} 연막탄 → {supply.turns}턴 피격 면역")

    # ── 턴 종료 ───────────────────────────────────────────────────────────────
    def _end_turn(self):
        msgs = self.current_player().tick_effects()
        for m in msgs:
            self._log(m)

        if self._check_death():
            return

        if self.cur_pid == 1:
            self.turn += 1
            self._phase_events()

        if not self.done:
            self.cur_pid = 1 - self.cur_pid

    def _phase_events(self):
        safe_dist = max(0, 100 - 10 * self.turn)
        if self.distance > safe_dist:
            self._log(f"🌀 자기장! (안전거리 {safe_dist}) 양쪽 -{BLUEZONE_DAMAGE}")
            for p in [self.p1, self.p2]:
                actual = p.take_damage(BLUEZONE_DAMAGE)
                if actual:
                    self._log(f"  {p.name} HP {p.hp + actual} → {p.hp}")
            if self._check_death():
                return

        if random.random() < 0.25:
            tgt = random.choice([self.p1, self.p2])
            self._log(f"💣 레드존! → {tgt.name}")
            actual = tgt.take_damage(REDZONE_DAMAGE)
            if actual == 0:
                self._log(f"  (방호 차단)")
            else:
                self._log(f"  {tgt.name} -{REDZONE_DAMAGE} HP ({tgt.hp})")
            self._check_death()

    def _check_death(self) -> bool:
        for p in [self.p1, self.p2]:
            if not p.is_alive:
                opp = self.p2 if p.pid == 0 else self.p1
                self.winner = opp
                self.done   = True
                self._log(f"🏆 {opp.name} 승리! ({p.name} HP 0)")
                return True
        return False

    def render(self):
        from .visualize import render_state
        render_state(self)

    def _get_state(self) -> dict:
        return {
            "turn":     self.turn,
            "distance": self.distance,
            "p1_hp":    self.p1.hp,
            "p2_hp":    self.p2.hp,
            "cur_pid":  self.cur_pid,
            "done":     self.done,
        }

    def _log(self, msg: str):
        self.log.append(msg)

    def flush_log(self) -> list[str]:
        lines, self.log = self.log[:], []
        return lines

    def _make_card_action(self, item, idx: int) -> Optional[dict]:
        if isinstance(item, (HouseCard, SupplyDropCard)):
            return {"type": ACTION_USE_CARD, "card_idx": idx,
                    "label": f"카드 개봉: {item.peek()}"}
        if isinstance(item, Weapon):
            in_range = self.distance <= item.attack_range
            note     = f"거리{self.distance}≤{item.attack_range}" if in_range else f"사거리부족"
            return {"type": ACTION_USE_CARD, "card_idx": idx,
                    "label": f"사용: {item.name} [{note}]",
                    "usable": in_range}
        if isinstance(item, Supply):
            return {"type": ACTION_USE_CARD, "card_idx": idx,
                    "label": f"사용: {item.name} ({item.description})"}
        if isinstance(item, Vehicle):
            return {"type": ACTION_USE_CARD, "card_idx": idx,
                    "label": f"탑승: {item.name} (+{item.speed}칸)"}
        return None
