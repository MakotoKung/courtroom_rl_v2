# train_model.py
# Q-Learning สำหรับเกมศาลแนว Ace Attorney
# - อ่านโครงเรื่องจาก dialogue/judge_scene.json และหลักฐานจาก evidence.json
# - Agent = ทนาย (Phoenix) เลือกหลักฐานที่จุด "expects_evidence"
# - ผิด: HP -2 แล้วเนื้อเรื่องเดินต่อตาม on_wrong_jump / ถูก: เดินต่อตาม on_correct_jump
# - HP หมด = Bad End, ไปถึง END_INDEX โดย HP เหลือ = Happy End
# รัน: python train_model.py  -> ได้ model_q_table.json
import json
import os
import random

SCRIPT_PATH = "dialogue/judge_scene.json"
EVIDENCE_PATH = "evidence.json"

# ค่าต้องตรงกับ scenes/base_dialogue_scene.py
END_INDEX = 107
MAX_HP = 5
WRONG_HP_LOSS = 2

# Reward
R_CORRECT = 10.0
R_WRONG = -10.0
R_DEAD = -40.0   # ซ้อนเพิ่มจาก R_WRONG ตอน HP หมด
R_WIN = 50.0


def state_key(idx, hp):
    return f"{idx}|{hp}"


class CourtEnv:
    def __init__(self, script, evidence_ids):
        self.script = script
        self.evidence_ids = evidence_ids
        self.reset()

    def _advance(self, idx):
        """เดินตามบทพูดจนเจอจุดที่ต้องยื่นหลักฐาน; คืน None ถ้าจบเกม"""
        for _ in range(len(self.script) * 2 + 10):  # กัน loop ไม่รู้จบ
            if idx >= len(self.script) or idx == END_INDEX:
                return None
            d = self.script[idx]
            if d.get("expects_evidence", False):
                return idx
            idx = d["next_jump"] if "next_jump" in d else idx + 1
        return None

    def reset(self):
        self.hp = MAX_HP
        self.done = False
        self.won = False
        self.idx = self._advance(0)
        if self.idx is None:
            self.done = self.won = True
        return self.state()

    def state(self):
        return state_key(self.idx, self.hp)

    def step(self, evidence_id):
        d = self.script[self.idx]
        if evidence_id == d.get("correct_evidence_id", ""):
            reward = R_CORRECT
            nxt = d.get("on_correct_jump", self.idx + 1)
        else:
            reward = R_WRONG
            self.hp = max(0, self.hp - WRONG_HP_LOSS)
            nxt = d.get("on_wrong_jump", self.idx + 1)
            if self.hp <= 0:
                self.done = True
                self.won = False
                return None, reward + R_DEAD, True

        self.idx = self._advance(nxt)
        if self.idx is None:
            self.done = True
            self.won = True
            return None, reward + R_WIN, True
        return self.state(), reward, False


def load_inputs(script_path=SCRIPT_PATH, evidence_path=EVIDENCE_PATH):
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)
    with open(evidence_path, "r", encoding="utf-8") as f:
        evidence_ids = [e["id"] for e in json.load(f)]
    return script, evidence_ids


def best_action(qs, evidence_ids, rng=None):
    mx = max(qs.get(e, 0.0) for e in evidence_ids)
    best = [e for e in evidence_ids if qs.get(e, 0.0) == mx]
    return rng.choice(best) if rng else best[0]


def evaluate(env, q, evidence_ids, games=1000):
    wins = 0
    for _ in range(games):
        env.reset()
        while not env.done:
            qs = q.get(env.state(), {})
            _, _, _ = env.step(best_action(qs, evidence_ids, random))
        wins += env.won
    return wins / games


def train_and_export(episodes=5000, output_file="model_q_table.json",
                     alpha=0.2, gamma=0.95,
                     epsilon_start=1.0, epsilon_end=0.05,
                     script_path=SCRIPT_PATH, evidence_path=EVIDENCE_PATH,
                     seed=None):
    if seed is not None:
        random.seed(seed)

    script, evidence_ids = load_inputs(script_path, evidence_path)
    env = CourtEnv(script, evidence_ids)
    q = {}  # state -> {evidence_id: value}

    print(f"Train Q-Learning {episodes:,} episodes "
          f"[alpha={alpha}, gamma={gamma}, eps {epsilon_start}->{epsilon_end}]")

    for ep in range(episodes):
        eps = max(epsilon_end, epsilon_start - (epsilon_start - epsilon_end) * ep / max(1, episodes * 0.8))
        s = env.reset()
        while not env.done:
            qs = q.setdefault(s, {e: 0.0 for e in evidence_ids})
            if random.random() < eps:
                a = random.choice(evidence_ids)
            else:
                a = best_action(qs, evidence_ids, random)

            s2, r, done = env.step(a)
            target = r
            if not done:
                q2 = q.setdefault(s2, {e: 0.0 for e in evidence_ids})
                target += gamma * max(q2.values())
            qs[a] += alpha * (target - qs[a])
            s = s2

    # policy รายจุดตรวจ (ใช้เป็น fallback ใน game): เลือกจาก state ที่ HP เต็มก่อน
    policy = {}
    for k, qs in q.items():
        idx, hp = k.split("|")
        if idx not in policy or int(hp) == MAX_HP:
            policy[idx] = best_action(qs, evidence_ids)

    win_rate = evaluate(env, q, evidence_ids)
    print(f"Greedy win rate: {win_rate:.1%}")

    out = {
        "meta": {
            "episodes": episodes, "alpha": alpha, "gamma": gamma,
            "max_hp": MAX_HP, "end_index": END_INDEX, "win_rate": win_rate,
            "state_format": "<dialogue_index>|<hp>",
        },
        "q_table": q,
        "policy": policy,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved -> {output_file}")
    return out


if __name__ == "__main__":
    train_and_export(episodes=1000, output_file="Model/Low_gamma_q_table.json", alpha=0.2, gamma=0.4, epsilon_start=1.0, epsilon_end=0.05, seed=42)
