from typing import List, Optional, TYPE_CHECKING
from ..cards.card import Card, CardType, RoleType, CharacterCard, RoleCard

if TYPE_CHECKING:
    pass


class Player:
    def __init__(self, player_id: int, name: str, is_human: bool = False):
        self.player_id = player_id
        self.name      = name
        self.is_human  = is_human

        self.role:      Optional[RoleCard]      = None
        self.character: Optional[CharacterCard] = None

        self.max_hp = 4
        self.hp     = 4

        self.hand:      List[Card] = []
        self.equipment: List[Card] = []  # 장비(파란 카드)

        self.is_alive      = True
        self.in_jail       = False   # Jail 카드 적용 상태
        self.has_dynamite  = False   # Dynamite 장비 여부

        self.bang_played_this_turn = 0  # 매 턴 초기화
        self.is_sheriff = False

    # ── HP ─────────────────────────────────────────────────
    def lose_hp(self, amount: int = 1):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.is_alive = False

    def gain_hp(self, amount: int = 1):
        self.hp = min(self.max_hp, self.hp + amount)

    def is_dead(self) -> bool:
        return not self.is_alive

    # ── 패 관리 ─────────────────────────────────────────────
    def add_card(self, card: Card):
        self.hand.append(card)

    def add_cards(self, cards: List[Card]):
        self.hand.extend(cards)

    def remove_card(self, card: Card) -> bool:
        if card in self.hand:
            self.hand.remove(card)
            return True
        return False

    def has_card_type(self, ct: CardType) -> bool:
        return any(c.card_type == ct for c in self.hand)

    def get_cards_of_type(self, ct: CardType) -> List[Card]:
        return [c for c in self.hand if c.card_type == ct]

    # ── 장비 ────────────────────────────────────────────────
    def equip(self, card: Card):
        self.equipment.append(card)
        if card.card_type == CardType.DYNAMITE:
            self.has_dynamite = True

    def unequip(self, card: Card) -> bool:
        if card in self.equipment:
            self.equipment.remove(card)
            if card.card_type == CardType.DYNAMITE:
                self.has_dynamite = False
            return True
        return False

    def has_equipment(self, ct: CardType) -> bool:
        return any(c.card_type == ct for c in self.equipment)

    def get_equipment(self, ct: CardType) -> Optional[Card]:
        for c in self.equipment:
            if c.card_type == ct:
                return c
        return None

    # ── 캐릭터 능력 헬퍼 ────────────────────────────────────
    @property
    def ability(self) -> str:
        return self.character.ability_key if self.character else ""

    def effective_range_attack(self) -> int:
        """스코프 / 로즈둘란 보정."""
        base = 1
        if self.has_equipment(CardType.SCOPE):
            base += 1
        if self.ability == "rose_doolan":
            base += 1
        return base

    def effective_range_defense(self) -> int:
        """무스탕 / 폴 리그렛 보정."""
        base = 0
        if self.has_equipment(CardType.MUSTANG):
            base += 1
        if self.ability == "paul_regret":
            base += 1
        return base

    # ── 역할 헬퍼 ──────────────────────────────────────────
    @property
    def role_type(self) -> Optional[RoleType]:
        return self.role.role if self.role else None

    # ── 문자열 표현 ─────────────────────────────────────────
    def status_line(self, reveal_role: bool = False) -> str:
        hp_bar = "●" * self.hp + "○" * (self.max_hp - self.hp)
        role   = f"[{self.role}]" if reveal_role else ""
        char   = f"{self.character.name}" if self.character else "?"
        equip  = " ".join(e.card_type.value for e in self.equipment)
        equip_str = f" ({equip})" if equip else ""
        return f"{self.name} {role} | {char} | {hp_bar}{equip_str}"

    def __repr__(self) -> str:
        return f"<Player {self.name} hp={self.hp}/{self.max_hp}>"
