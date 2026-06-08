"""간단한 그리디 AI."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .environment import GameEnv

from .items import Weapon, Supply, Vehicle
from .cards import HouseCard, SupplyDropCard
from .environment import ACTION_MOVE, ACTION_USE_CARD, ACTION_PASS


def choose_action(env: "GameEnv") -> dict:
    p       = env.current_player()
    actions = env.get_valid_actions()

    # 우선순위 1: HP 위험 → 즉시 회복
    if p.hp < 40:
        for act in actions:
            if act["type"] == ACTION_USE_CARD and "card_idx" in act:
                item = p.inventory[act["card_idx"]]
                if isinstance(item, Supply):
                    return act

    # 우선순위 2: 공격 가능한 무기 중 최선 선택
    best_atk   = None
    best_score = -1
    for act in actions:
        if act["type"] == ACTION_USE_CARD and act.get("usable", True):
            if "weapon_idx" in act:
                idx    = act["weapon_idx"]
                weapon = p.pistol if idx == -1 else p.weapon_slots[idx]
                score  = weapon.attack_range
                if score > best_score:
                    best_score, best_atk = score, act
            elif "card_idx" in act:
                item = p.inventory[act["card_idx"]]
                if isinstance(item, Weapon):
                    score = item.attack_range
                    if score > best_score:
                        best_score, best_atk = score, act

    if best_atk:
        return best_atk

    # 우선순위 3: 집/보급 카드 개봉
    for act in actions:
        if act["type"] == ACTION_USE_CARD and "card_idx" in act:
            item = p.inventory[act["card_idx"]]
            if isinstance(item, (HouseCard, SupplyDropCard)):
                return act

    # 우선순위 4: 이동수단 탑승
    for act in actions:
        if act["type"] == ACTION_USE_CARD and "card_idx" in act:
            item = p.inventory[act["card_idx"]]
            if isinstance(item, Vehicle):
                return act

    # 우선순위 5: 이동 (접근)
    for act in actions:
        if act["type"] == ACTION_MOVE:
            return act

    return {"type": ACTION_PASS, "label": "패스"}
