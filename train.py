# =============================================================================
# train.py — O 로봇과 X 로봇의 자가대전(Self-Play) 학습 루프
#
# 자가대전(Self-Play)이란?
#   두 에이전트가 서로를 상대로 반복적으로 게임을 하면서 동시에 학습합니다.
#   한쪽이 강해지면 상대방도 그에 맞게 더 강해지는 구조여서,
#   사람이 직접 상대해주지 않아도 점점 수준 높은 전략을 터득합니다.
#
# 이 파일을 분리한 이유:
#   - "학습"이라는 단 하나의 책임만 담당합니다.
#   - 학습 완료 후 play.py 에서 결과를 별도로 확인할 수 있도록 역할을 분리합니다.
#   - 하이퍼파라미터 튜닝 실험 시 이 파일만 반복 실행하면 됩니다.
# =============================================================================

import time
import config
from environment import TicTacToeEnv
from agent import QLearningAgent


def run_episode(env: TicTacToeEnv, agent_o: QLearningAgent, agent_x: QLearningAgent):
    """
    게임 한 판(에피소드)을 진행하고 양쪽 에이전트를 모두 학습시킵니다.
    O는 항상 선공, X는 항상 후공입니다 (틱택토 규칙).

    핵심 설계 원칙 — "상대 응답 후 상태"로 Q-업데이트:
        Q-러닝 수식:  Q(s, a) ← r + γ · max Q(s', a')
        2인 게임에서 s'는 "내가 다음 번에 실제로 마주할 상태"여야 합니다.
        즉 상대가 응답한 뒤의 상태 = 내 차례가 다시 돌아왔을 때의 state.

        ❌ 잘못된 방식: next_state (내가 방금 둔 직후, 상대 미응답)
        ✓  올바른 방식: state (상대가 이미 응답해서 내 차례가 된 현재)

        예)
          타임라인: s0 →[O둠]→ s1 →[X둠]→ s2 →[O둠]→ ...
          O의 이전 수(s0→s1)에 대한 next_state = s2  (O 차례가 다시 된 시점)
          → 업데이트는 O 차례가 돌아왔을 때(state=s2)에 실행합니다.
    """
    state = env.reset()

    # 각 에이전트의 직전 (상태, 행동)을 기억합니다.
    # 상대가 응답한 뒤 내 차례가 돌아왔을 때 비로소 Q-업데이트에 사용합니다.
    last_o = None   # (prev_state, prev_action)
    last_x = None   # (prev_state, prev_action)

    result = "draw"

    while not env.done:
        valid = env.get_valid_actions()

        # ── O 차례 ──────────────────────────────────────────────────────
        if env.current_player == 1:

            # ▶ 이전 O 수에 대한 Q-업데이트 (버그 수정 핵심)
            #   last_o 의 next_state = 지금 O가 마주한 state (상대가 이미 응답 완료)
            #   이전 코드는 next_state(O 직후 상태)를 썼는데, 그 상태는 X 차례이므로
            #   O의 관점에서 "미래 최선 행동"을 올바르게 평가할 수 없었습니다.
            if last_o is not None:
                agent_o.learn(last_o[0], last_o[1], config.REWARD_STEP, state, False, valid)

            # 행동 선택 및 실행
            action = agent_o.choose_action(state, valid)
            next_state, r_o, r_x, done = env.step(action)

            # 잘못된 수: 즉시 패널티 학습 후 재시도 (플레이어 교체 없음)
            if r_o == config.REWARD_INVALID:
                agent_o.learn(state, action, r_o, state, False, valid)
                continue

            if done:
                # 종료 시: 현재 수(O 승/무)와 X의 직전 수(-1.0) 모두 최종 학습
                agent_o.learn(state, action, r_o, next_state, True, [])
                if last_x is not None:
                    agent_x.learn(last_x[0], last_x[1], r_x, next_state, True, [])
                result = "O_win" if r_o == config.REWARD_WIN else "draw"
            else:
                last_o = (state, action)

        # ── X 차례 ──────────────────────────────────────────────────────
        else:

            # ▶ 이전 X 수에 대한 Q-업데이트 (동일한 원칙 적용)
            #   last_x 의 next_state = 지금 X가 마주한 state (O가 이미 응답 완료)
            if last_x is not None:
                agent_x.learn(last_x[0], last_x[1], config.REWARD_STEP, state, False, valid)

            action = agent_x.choose_action(state, valid)
            next_state, r_o, r_x, done = env.step(action)

            if r_x == config.REWARD_INVALID:
                agent_x.learn(state, action, r_x, state, False, valid)
                continue

            if done:
                agent_x.learn(state, action, r_x, next_state, True, [])
                if last_o is not None:
                    agent_o.learn(last_o[0], last_o[1], r_o, next_state, True, [])
                result = "X_win" if r_x == config.REWARD_WIN else "draw"
            else:
                last_x = (state, action)

        state = next_state

    return result


def train():
    """
    O 로봇과 X 로봇을 NUM_EPISODES 판 동안 자가대전으로 학습시킵니다.

    학습 진행 요약:
        - 매 LOG_INTERVAL 판마다 승률·무승부율·평균 ε 을 출력합니다.
        - 학습 종료 후 두 에이전트의 Q-테이블을 파일로 저장합니다.
    """
    print("=" * 60)
    print("  틱택토 강화학습 — O 로봇 vs X 로봇 자가대전 시작")
    print(f"  총 {config.NUM_EPISODES:,} 판 학습 예정")
    print("=" * 60)

    env = TicTacToeEnv()
    agent_o = QLearningAgent("O")
    agent_x = QLearningAgent("X")

    # 이미 저장된 모델이 있으면 이어서 학습합니다.
    agent_o.load(config.MODEL_PATH_O)
    agent_x.load(config.MODEL_PATH_X)

    # 통계 집계용 카운터
    counts = {"O_win": 0, "X_win": 0, "draw": 0}
    start_time = time.time()

    for episode in range(1, config.NUM_EPISODES + 1):
        result = run_episode(env, agent_o, agent_x)
        counts[result] += 1

        # 탐험 비율 감소 — 에피소드가 끝날 때마다 한 번씩 줄입니다.
        agent_o.decay_epsilon()
        agent_x.decay_epsilon()

        # ── 주기적 진행 상황 출력 ─────────────────────────────────────────
        if episode % config.LOG_INTERVAL == 0:
            elapsed = time.time() - start_time
            total = sum(counts.values())
            o_rate  = counts["O_win"] / total * 100
            x_rate  = counts["X_win"] / total * 100
            d_rate  = counts["draw"]  / total * 100
            print(
                f"[{episode:>7,}판] "
                f"O승 {o_rate:5.1f}%  X승 {x_rate:5.1f}%  무승부 {d_rate:5.1f}%  "
                f"ε(O)={agent_o.epsilon:.4f}  ε(X)={agent_x.epsilon:.4f}  "
                f"경과 {elapsed:.0f}s"
            )
            # 통계 초기화 (구간별 추이를 보기 위해)
            counts = {"O_win": 0, "X_win": 0, "draw": 0}

    # ── 학습 완료 — 모델 저장 ─────────────────────────────────────────────
    print("\n학습 완료! 모델을 저장합니다...")
    agent_o.save(config.MODEL_PATH_O)
    agent_x.save(config.MODEL_PATH_X)

    total_time = time.time() - start_time
    print(f"\n총 소요 시간: {total_time:.1f}초")
    print("play.py 를 실행하면 학습된 로봇과 대전하거나 평가할 수 있습니다.")


if __name__ == "__main__":
    train()
