"""간단한 그리디 AI."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .environment import GameEnv

from .items import Weapon, Supply, Vehicle
from .cards import HouseCard, SupplyDropCard
from .environment import ACTION_MOVE, ACTION_USE_CARD, ACTION_PASS


def choose_action(env: "GameEnv") -> dict:
    """AI 행동 결정."""
    p       = env.current_player()
    actions = env.get_valid_actions()

    # 우선순위 1: HP 위험 → 즉시 회복 (HP < 40)
    if p.hp < 40:
        for act in actions:
            if act["type"] == ACTION_USE_CARD:
                item = p.inventory[act["card_idx"]]
                if isinstance(item, Supply):
                    return act

    # 우선순위 2: 공격 가능 무기 사용
    best_atk = None
    best_dmg = -1
    for act in actions:
        if act["type"] == ACTION_USE_CARD and act.get("usable", True):
            item = p.inventory[act["card_idx"]]
            if isinstance(item, Weapon):
                # 예상 최대 데미지로 정렬 (간단: attack_range 우선)
                if item.attack_range >= best_dmg:
                    best_dmg   = item.attack_range
                    best_atk   = act
    if best_atk:
        return best_atk

    # 우선순위 3: 집/보급 카드 개봉
    for act in actions:
        if act["type"] == ACTION_USE_CARD:
            item = p.inventory[act["card_idx"]]
            if isinstance(item, (HouseCard, SupplyDropCard)):
                return act

    # 우선순위 4: 차량 탑승 → 이동 효율 증가
    for act in actions:
        if act["type"] == ACTION_USE_CARD:
            item = p.inventory[act["card_idx"]]
            if isinstance(item, Vehicle):
                return act

    # 우선순위 5: 이동 (적에게 접근)
    for act in actions:
        if act["type"] == ACTION_MOVE:
            return act

    # 패스
    return {"type": ACTION_PASS, "label": "패스"}
