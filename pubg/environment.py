"""GameEnv — PUBG 보드게임 핵심 환경."""
from __future__ import annotations
import random
from typing import Optional

from .player import Player, ActiveEffect, MAX_HP
from .items import Weapon, Supply, Vehicle
from .cards import HouseCard, SupplyDropCard

# ── 액션 타입 ────────────────────────────────────────────────────────────────
ACTION_MOVE      = "move"       # 이동 (1칸 또는 vehicle 카드 사용)
ACTION_USE_CARD  = "use_card"   # 인벤토리 카드 사용
ACTION_PASS      = "pass"       # 패스 (아무것도 못할 때)

# ── 자기장 설정 ──────────────────────────────────────────────────────────────
# 턴 T에서 최대 안전 거리 = max(0, 100 - 10*T)
# 거리가 이 값보다 크면 자기장 피해 20

INITIAL_DISTANCE = 50
BLUEZONE_DAMAGE  = 20
REDZONE_DAMAGE   = 50


class GameEnv:
    def __init__(self, p1_name: str = "플레이어1", p2_name: str = "플레이어2",
                 p1_human: bool = True, p2_human: bool = False):
        self.p1 = Player(0, p1_name, p1_human)
        self.p2 = Player(1, p2_name, p2_human)

        self.turn:      int  = 1
        self.cur_pid:   int  = 0      # 현재 행동할 플레이어 (0 or 1)
        self.distance:  int  = INITIAL_DISTANCE
        self.done:      bool = False
        self.winner:    Optional[Player] = None
        self.log:       list[str] = []

        self._supply_card_remaining: int = 1  # 게임당 보급 카드 1장

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
        self._supply_card_remaining = 1

        # 초기 패 배분: 각각 집 카드 2장
        for _ in range(2):
            self.p1.add_item(HouseCard())
            self.p2.add_item(HouseCard())

        # 보급 카드 1장 — 랜덤으로 한 명에게
        lucky = random.choice([self.p1, self.p2])
        lucky.add_item(SupplyDropCard())
        self._log(f"★ 보급 카드가 {lucky.name}에게 배정되었습니다.")

        self._log(f"=== 게임 시작! (초기 거리: {INITIAL_DISTANCE}) ===")
        return self._get_state()

    # ── 외부 인터페이스 ───────────────────────────────────────────────────────
    def current_player(self) -> Player:
        return self.p1 if self.cur_pid == 0 else self.p2

    def opponent(self) -> Player:
        return self.p2 if self.cur_pid == 0 else self.p1

    def get_valid_actions(self) -> list[dict]:
        """현재 플레이어가 선택 가능한 액션 목록."""
        p = self.current_player()
        actions: list[dict] = []

        # 이동 (항상 가능, 거리 > 0 일 때)
        if self.distance > 0:
            actions.append({"type": ACTION_MOVE, "label": "이동 (1칸 접근)"})

        # 인벤토리 카드 사용
        for idx, item in enumerate(p.inventory):
            action = self._make_card_action(item, idx)
            if action:
                actions.append(action)

        if not actions:
            actions.append({"type": ACTION_PASS, "label": "패스"})
        return actions

    def step(self, action: dict) -> tuple[dict, bool]:
        """액션 실행. (state, done) 반환."""
        if self.done:
            return self._get_state(), True

        p   = self.current_player()
        opp = self.opponent()

        atype = action["type"]

        if atype == ACTION_MOVE:
            self._do_move(p, action.get("speed", 1))

        elif atype == ACTION_USE_CARD:
            idx  = action["card_idx"]
            item = p.inventory[idx]
            self._do_use_card(p, opp, item)

        elif atype == ACTION_PASS:
            self._log(f"{p.name}: 패스")

        # 턴 종료 처리
        self._end_turn()
        return self._get_state(), self.done

    # ── 이동 ─────────────────────────────────────────────────────────────────
    def _do_move(self, p: Player, speed: int = 1):
        old = self.distance
        self.distance = max(0, self.distance - speed)
        p.position   += speed if p.pid == 0 else -speed
        moved = old - self.distance
        self._log(f"🚶 {p.name}이(가) {moved}칸 이동 → 거리 {self.distance}")

    # ── 카드 사용 ─────────────────────────────────────────────────────────────
    def _do_use_card(self, p: Player, opp: Player, item):
        p.remove_item(item)

        # 집 카드 / 보급 카드 → 아이템 획득
        if isinstance(item, (HouseCard, SupplyDropCard)):
            gained = item.open()
            p.add_item(gained)
            kind = "집 카드" if isinstance(item, HouseCard) else "보급 카드"
            self._log(f"📦 {p.name}이(가) {kind}(번호:{item.roll}) 개봉 → {gained.name} 획득!")
            return

        # 무기 → 공격
        if isinstance(item, Weapon):
            self._do_attack(p, opp, item)
            return

        # 지원품 → 회복 / 보호
        if isinstance(item, Supply):
            self._do_supply(p, item)
            return

        # 이동수단 → 추가 이동
        if isinstance(item, Vehicle):
            self._log(f"🚗 {p.name}이(가) {item.name} 탑승! +{item.speed}칸 이동")
            self._do_move(p, item.speed)
            if item.special == "immunity":
                p.add_effect(ActiveEffect("brdm_immune", 0, 1))
                self._log(f"  🛡️  BRDM2 방호 활성 (이번 상대 턴까지 피격 면역, 링스 제외)")
            return

    # ── 공격 처리 ─────────────────────────────────────────────────────────────
    def _do_attack(self, attacker: Player, target: Player, weapon: Weapon):
        if self.distance > weapon.attack_range:
            self._log(f"  ❌ 거리 {self.distance} > 사정거리 {weapon.attack_range} — 사거리 부족!")
            attacker.add_item(weapon)  # 되돌려 줌
            return

        brdm_on = target.has_effect("brdm_immune")
        # 링스는 BRDM 관통
        if weapon.special == "BRDM_pierce":
            brdm_on = False

        dmg, is_kill, desc = weapon.calc_damage(brdm_on)
        self._log(f"🔫 {attacker.name} → {target.name}  [{weapon.name}]  {desc}")

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

        # 화염병 DOT
        if weapon.name == "화염병" and not target.has_effect("shield"):
            target.add_effect(ActiveEffect("fire", 30, 3))

        # M249 → BRDM 무력화
        if weapon.name == "M249" and target.has_effect("brdm_immune"):
            target.effects = [e for e in target.effects if e.kind != "brdm_immune"]
            self._log(f"  ⚡ BRDM2 무력화!")

        # 무기는 소모되지 않음 (인벤에 복귀)
        attacker.add_item(weapon)

    # ── 지원품 처리 ───────────────────────────────────────────────────────────
    def _do_supply(self, p: Player, supply: Supply):
        if supply.heal_type == "instant":
            p.heal(supply.heal_amount)
            self._log(f"💊 {p.name} {supply.name} 사용 → HP +{supply.heal_amount} ({p.hp})")
        elif supply.heal_type == "max_cap":
            old = p.hp
            p.hp = min(supply.heal_amount, MAX_HP)
            self._log(f"💊 {p.name} {supply.name} 사용 → HP {old} → {p.hp}")
        elif supply.heal_type == "per_turn":
            p.add_effect(ActiveEffect("heal_over_time", supply.heal_amount, supply.turns))
            self._log(f"💊 {p.name} {supply.name} 사용 → {supply.turns}턴 동안 매 턴 +{supply.heal_amount}")
        elif supply.heal_type == "shield":
            p.add_effect(ActiveEffect("shield", 0, supply.turns))
            self._log(f"💊 {p.name} 연막탄 사용 → {supply.turns}턴 피격 면역")

    # ── 턴 종료 처리 ──────────────────────────────────────────────────────────
    def _end_turn(self):
        # 현재 플레이어 지속 효과 tick
        msgs = self.current_player().tick_effects()
        for m in msgs:
            self._log(m)

        # 사망 체크
        if self._check_death():
            return

        # 양쪽 턴이 끝나면 (P1→P2→턴 증가)
        if self.cur_pid == 1:
            self.turn += 1
            self._phase_events()

        if not self.done:
            self.cur_pid = 1 - self.cur_pid

    # ── 이벤트 페이즈 (매 2턴마다 발동) ──────────────────────────────────────
    def _phase_events(self):
        # 자기장 — 항상 체크
        safe_dist = max(0, 100 - 10 * self.turn)
        if self.distance > safe_dist and safe_dist >= 0:
            self._log(f"🌀 자기장 발동! (안전거리 {safe_dist}) 양쪽 -{BLUEZONE_DAMAGE} 데미지")
            for p in [self.p1, self.p2]:
                actual = p.take_damage(BLUEZONE_DAMAGE)
                if actual:
                    self._log(f"  {p.name} HP {p.hp + actual} → {p.hp}")
            if self._check_death():
                return

        # 레드존 (확률 25%, 집 안에 있으면 무시 — 이 게임에선 단순 랜덤)
        if random.random() < 0.25:
            target = random.choice([self.p1, self.p2])
            self._log(f"💣 레드존! → {target.name}")
            actual = target.take_damage(REDZONE_DAMAGE)
            if actual == 0:
                self._log(f"  (방호로 차단)")
            else:
                self._log(f"  {target.name} -{REDZONE_DAMAGE} HP ({target.hp})")
            self._check_death()

    # ── 사망 체크 ────────────────────────────────────────────────────────────
    def _check_death(self) -> bool:
        for p in [self.p1, self.p2]:
            if not p.is_alive:
                opp = self.p2 if p.pid == 0 else self.p1
                self.winner = opp
                self.done   = True
                self._log(f"🏆 {opp.name} 승리! ({p.name} HP 0)")
                return True
        return False

    # ── 렌더링 ───────────────────────────────────────────────────────────────
    def render(self):
        from .visualize import render_state
        render_state(self)

    # ── 상태 반환 (RL용) ─────────────────────────────────────────────────────
    def _get_state(self) -> dict:
        return {
            "turn":      self.turn,
            "distance":  self.distance,
            "p1_hp":     self.p1.hp,
            "p2_hp":     self.p2.hp,
            "cur_pid":   self.cur_pid,
            "done":      self.done,
        }

    # ── 로그 ──────────────────────────────────────────────────────────────────
    def _log(self, msg: str):
        self.log.append(msg)

    def flush_log(self) -> list[str]:
        lines, self.log = self.log[:], []
        return lines

    # ── 카드 액션 빌더 ────────────────────────────────────────────────────────
    def _make_card_action(self, item, idx: int) -> Optional[dict]:
        p   = self.current_player()
        opp = self.opponent()
        if isinstance(item, (HouseCard, SupplyDropCard)):
            return {"type": ACTION_USE_CARD, "card_idx": idx,
                    "label": f"카드 개봉: {item.peek()}"}
        if isinstance(item, Weapon):
            in_range = self.distance <= item.attack_range
            note     = f"거리{self.distance}≤{item.attack_range}" if in_range else f"사거리 부족({self.distance}>{item.attack_range})"
            return {"type": ACTION_USE_CARD, "card_idx": idx,
                    "label": f"공격: {item.name} [{note}]",
                    "usable": in_range}
        if isinstance(item, Supply):
            return {"type": ACTION_USE_CARD, "card_idx": idx,
                    "label": f"사용: {item.label()}"}
        if isinstance(item, Vehicle):
            return {"type": ACTION_USE_CARD, "card_idx": idx,
                    "label": f"탑승: {item.label()}"}
        return None
