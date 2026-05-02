# =============================================================================
# environment.py — 3×3 틱택토 게임 환경
#
# 강화학습에서 "환경(Environment)"은 로봇이 행동하는 세계입니다.
# 로봇이 어떤 칸에 돌을 놓으면 환경이 다음 상태(board)와 보상(reward)을 돌려줍니다.
#
# 이 파일에 환경을 독립적으로 분리한 이유:
#   - 게임 규칙 변경(예: 4×4 보드)이 이 파일만 수정하면 되도록 책임을 분리합니다.
#   - 여러 에이전트(O, X)가 같은 환경 객체를 공유해서 코드 중복을 없앱니다.
#   - 단위 테스트 시 환경만 독립적으로 검증할 수 있습니다.
# =============================================================================

import numpy as np
import config


class TicTacToeEnv:
    """
    3×3 틱택토 게임 환경 클래스.

    보드 표현:
        0  = 빈 칸
        1  = O 플레이어
       -1  = X 플레이어

    행동(action):
        0~8 사이의 정수 → 보드를 1차원으로 펼쳤을 때의 칸 번호
        예) 칸 번호 배치:
            0 | 1 | 2
            ---------
            3 | 4 | 5
            ---------
            6 | 7 | 8
    """

    # ── 게임에서 승리 조건이 되는 칸 조합 ───────────────────────────────
    # 가로 3줄, 세로 3줄, 대각선 2줄 — 총 8가지 이기는 패턴입니다.
    WIN_PATTERNS = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),   # 가로
        (0, 3, 6), (1, 4, 7), (2, 5, 8),   # 세로
        (0, 4, 8), (2, 4, 6),              # 대각선
    ]

    def __init__(self):
        # 보드: 9칸짜리 1차원 배열 (모두 0으로 초기화)
        self.board = np.zeros(9, dtype=int)
        # 현재 어느 플레이어의 차례인지 (1=O, -1=X)
        self.current_player = 1
        # 게임이 끝났는지 여부
        self.done = False

    # ─────────────────────────────────────────────────────────────────────────
    # reset: 게임을 새로 시작합니다.
    # 학습 루프에서 한 판이 끝날 때마다 호출해 보드를 초기화합니다.
    # ─────────────────────────────────────────────────────────────────────────
    def reset(self):
        """보드를 초기 상태로 되돌리고, O가 먼저 시작합니다."""
        self.board = np.zeros(9, dtype=int)
        self.current_player = 1   # O 먼저
        self.done = False
        return self._get_state()

    # ─────────────────────────────────────────────────────────────────────────
    # step: 현재 플레이어가 action 위치에 돌을 놓습니다.
    #
    # 반환값:
    #   (next_state, reward_o, reward_x, done)
    #   - next_state : 행동 후의 보드 상태 (tuple)
    #   - reward_o   : O 로봇에게 줄 보상
    #   - reward_x   : X 로봇에게 줄 보상
    #   - done       : 게임 종료 여부
    # ─────────────────────────────────────────────────────────────────────────
    def step(self, action: int):
        """
        보상 설계 원칙:
          승리한 플레이어에게 +1.0, 패배한 플레이어에게 -1.0 을 줍니다.
          무승부는 양쪽 모두 +0.3 으로 "지는 것보다는 낫다"는 신호를 줍니다.
          잘못된 칸(이미 돌이 놓인 칸)을 선택하면 -0.5 패널티를 부여합니다.

          잘못된 수에 패널티를 주는 이유:
            패널티 없이 그냥 무시만 하면 로봇이 잘못된 수를 반복해도 손해가 없어
            학습 효율이 크게 떨어집니다. 음수 보상을 줘서 빠르게 규칙을 익히도록 합니다.
        """
        # ── 잘못된 수 처리 ────────────────────────────────────────────────
        # 이미 돌이 놓인 칸에 두려는 경우: 패널티를 주고 게임은 계속됩니다.
        if self.board[action] != 0:
            if self.current_player == 1:  # O 차례에 잘못된 수
                return self._get_state(), config.REWARD_INVALID, config.REWARD_STEP, False
            else:                          # X 차례에 잘못된 수
                return self._get_state(), config.REWARD_STEP, config.REWARD_INVALID, False

        # ── 돌 놓기 ───────────────────────────────────────────────────────
        self.board[action] = self.current_player

        # ── 승리 판정 ─────────────────────────────────────────────────────
        if self._check_winner(self.current_player):
            self.done = True
            if self.current_player == 1:   # O 승리
                return self._get_state(), config.REWARD_WIN, config.REWARD_LOSE, True
            else:                           # X 승리
                return self._get_state(), config.REWARD_LOSE, config.REWARD_WIN, True

        # ── 무승부 판정 ───────────────────────────────────────────────────
        # 빈 칸이 하나도 없으면서 아무도 이기지 못한 경우
        if not self._has_empty():
            self.done = True
            return self._get_state(), config.REWARD_DRAW, config.REWARD_DRAW, True

        # ── 게임 계속 — 플레이어 교체 ────────────────────────────────────
        # 진행 중인 수에는 중립 보상(0)을 줍니다.
        # 중간 보상을 주지 않는 이유:
        #   "좋은 위치(예: 중앙)"에 중간 보상을 주면 로봇이 이기는 것보다
        #   특정 위치를 고집하는 편향이 생길 수 있습니다.
        #   최종 결과(승/패/무)만으로 학습하는 것이 더 균형 잡힌 전략을 만듭니다.
        self.current_player *= -1   # 1 → -1, -1 → 1
        return self._get_state(), config.REWARD_STEP, config.REWARD_STEP, False

    # ─────────────────────────────────────────────────────────────────────────
    # get_valid_actions: 현재 보드에서 둘 수 있는 칸 목록을 반환합니다.
    # 에이전트가 행동을 선택할 때 유효한 칸만 고르도록 하는 데 사용합니다.
    # ─────────────────────────────────────────────────────────────────────────
    def get_valid_actions(self) -> list[int]:
        """빈 칸(값이 0인 칸)의 인덱스 목록을 반환합니다."""
        return [i for i, v in enumerate(self.board) if v == 0]

    # ─────────────────────────────────────────────────────────────────────────
    # render: 현재 보드 상태를 터미널에 출력합니다.
    # ─────────────────────────────────────────────────────────────────────────
    def render(self):
        """보드를 시각적으로 출력합니다. 학습 결과 확인 시 사용합니다."""
        symbols = {0: ".", 1: "O", -1: "X"}
        print()
        for row in range(3):
            cells = [symbols[self.board[row * 3 + col]] for col in range(3)]
            print(f"  {cells[0]} | {cells[1]} | {cells[2]}")
            if row < 2:
                print("  ---------")
        print()

    # ─────────────────────────────────────────────────────────────────────────
    # 내부 헬퍼 메서드들 (외부에서 직접 호출할 필요 없음)
    # ─────────────────────────────────────────────────────────────────────────

    def _get_state(self) -> tuple:
        """
        보드를 Q-테이블의 키로 사용할 수 있도록 tuple 로 변환합니다.
        tuple 은 변경 불가능(immutable)해서 딕셔너리 키로 쓸 수 있습니다.
        """
        return tuple(self.board)

    def _check_winner(self, player: int) -> bool:
        """player(1 또는 -1)가 이겼는지 WIN_PATTERNS 를 모두 확인합니다."""
        for a, b, c in self.WIN_PATTERNS:
            if self.board[a] == self.board[b] == self.board[c] == player:
                return True
        return False

    def _has_empty(self) -> bool:
        """보드에 빈 칸이 하나라도 남아 있으면 True 를 반환합니다."""
        return 0 in self.board
