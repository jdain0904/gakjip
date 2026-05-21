import random
from typing import List, Optional
from .card import Card
from .definitions import build_play_deck


class Deck:
    def __init__(self):
        self._draw:    List[Card] = []
        self._discard: List[Card] = []
        self.reset()

    def reset(self):
        self._draw    = build_play_deck()
        self._discard = []
        random.shuffle(self._draw)

    # ── 드로우 ──────────────────────────────────────────────
    def draw(self) -> Card:
        if not self._draw:
            self._reshuffle()
        return self._draw.pop()

    def draw_n(self, n: int) -> List[Card]:
        return [self.draw() for _ in range(n)]

    def peek_top(self) -> Optional[Card]:
        """덱 상단 공개 (드로! 판정용)."""
        if not self._draw:
            self._reshuffle()
        return self._draw[-1] if self._draw else None

    def pop_top(self) -> Optional[Card]:
        """덱 상단 제거 (드로! 판정용)."""
        if not self._draw:
            self._reshuffle()
        return self._draw.pop() if self._draw else None

    def peek_top_discard(self) -> Optional[Card]:
        return self._discard[-1] if self._discard else None

    def pop_top_discard(self) -> Optional[Card]:
        return self._discard.pop() if self._discard else None

    # ── 버리기 ──────────────────────────────────────────────
    def discard(self, card: Card):
        self._discard.append(card)

    def discard_many(self, cards: List[Card]):
        for c in cards:
            self._discard.append(c)

    # ── 내부 ────────────────────────────────────────────────
    def _reshuffle(self):
        if not self._discard:
            return
        top = self._discard[-1]
        self._draw = self._discard[:-1]
        self._discard = [top]
        random.shuffle(self._draw)

    # ── 정보 ────────────────────────────────────────────────
    @property
    def draw_size(self) -> int:
        return len(self._draw)

    @property
    def discard_size(self) -> int:
        return len(self._discard)

    def __len__(self) -> int:
        return len(self._draw)
