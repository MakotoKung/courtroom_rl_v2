# train_model.py
import json
import random
import itertools
from pathlib import Path

class CourtEnv:
    def __init__(self, data):
        self.data = data
        self.reset()

    def reset(self):
        self.hp = 5.0
        self.submitted = []  # รายการหลักฐานที่อัยการยื่นไปแล้ว เช่น ["P1", "P3"]
        self.witness_active = False
        self.done = False
        self.winner = None
        return self.get_state_key()

    def get_state_key(self):
        # สร้าง Key สำหรับดึงค่า Q-value ของอัยการจากหลักฐานที่เคยยื่นไปแล้ว
        return ",".join(sorted(self.submitted)) if self.submitted else "EMPTY"

    def step_prosecutor_action(self, action_idx):
        """
        Action Index ของอัยการ:
        0 = เรียกพยานหนุน (เพิ่ม Power ตาหน้า)
        1..5 = ยื่นหลักฐาน P1 ถึง P5
        6 = ตัดสินคดี (จบเกม)
        """
        if self.done:
            return {"type": "game_over"}

        # 1. เรียกพยาน
        if action_idx == 0:
            if self.witness_active:
                return {"type": "witness_duplicate"}
            self.witness_active = True
            return {"type": "witness_called"}

        # 6. ตัดสินคดี
        elif action_idx == 6:
            self.done = True
            # ตัดสินแพ้-ชนะจาก HP เท่านั้น (ถ้าสู้รอดจนครบ 5 ชิ้นแล้ว HP ยังเหลือ ทนายชนะ)
            if self.hp <= 0:
                self.winner = "prosecutor"
                return {"type": "verdict_guilty"}
            else:
                self.winner = "lawyer"
                return {"type": "verdict_not_guilty"}

        # 1..5 ยื่นหลักฐาน P1 - P5
        else:
            p_id = f"P{action_idx}"
            if p_id in self.submitted:
                return {"type": "evidence_duplicate"}

            self.submitted.append(p_id)
            power = 2 if self.witness_active else 1
            self.witness_active = False  # ใช้พยานแล้วหมดสิทธิ์รอบนี้

            return {
                "type": "evidence_presented",
                "p_id": p_id,
                "power": power
            }

    def resolve_lawyer_response(self, p_id, power, lawyer_choice):
        # ตรวจสอบว่าทนายเลือกหลักฐานถูกต้องตามเงื่อนไขหักล้างหรือไม่
        correct_counter = self.data["prosecutor_evidence"][p_id]["counter"]
        is_correct = (lawyer_choice == correct_counter)

        hp_loss = 0.0
        if lawyer_choice == "PASS":
            hp_loss = float(power)
        elif is_correct:
            hp_loss = 0.0
        else:
            hp_loss = float(power) * 1.5

        self.hp = max(0.0, self.hp - hp_loss)

        if self.hp <= 0:
            self.done = True
            self.winner = "prosecutor"

        return {
            "is_correct": is_correct,
            "hp_loss": hp_loss
        }

    def get_defendant_status(self):
        # คำนวณสถานะความกังวลของจำเลยตาม HP ที่เหลือ
        if self.hp > 3.5:
            return 1
        elif self.hp > 2.0:
            return 2
        elif self.hp > 0.5:
            return 3
        return 4


def train_and_export(episodes=15000, output_file="model_q_table.json", alpha=0.1, gamma=0.9, epsilon=0.1):
    # โหลดข้อมูลจาก game_data.json
    with open("game_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    env = CourtEnv(data)

    # Q-Tables สำหรับอัยการและทนาย
    prosecutor_q = {}
    lawyer_q = {}

    script = data.get("prosecutor_script", [])

    print(f"กำลังเริ่มฝึก AI (Q-Learning) จำนวน {episodes:,} รอบ [Alpha={alpha}, Gamma={gamma}, Epsilon={epsilon}]...")

    for ep in range(episodes):
        state = env.reset()
        done = False
        script_idx = 0

        while not done:
            state_key = env.get_state_key()
            if state_key not in prosecutor_q:
                prosecutor_q[state_key] = [0.0] * 7

            # เลือก Action ของอัยการ
            if script and script_idx < len(script) and random.random() > epsilon:
                target_p = script[script_idx]["evidence"]
                action_idx = int(target_p[1])
                script_idx += 1
            else:
                if random.random() < epsilon:
                    action_idx = random.randint(0, 6)
                else:
                    q_vals = prosecutor_q[state_key]
                    max_q = max(q_vals)
                    best_actions = [i for i, v in enumerate(q_vals) if v == max_q]
                    action_idx = random.choice(best_actions)

            p_info = env.step_prosecutor_action(action_idx)

            if p_info["type"] == "game_over":
                break
            elif p_info["type"] in ("witness_duplicate", "evidence_duplicate"):
                continue
            elif p_info["type"] in ("verdict_guilty", "verdict_not_guilty"):
                done = True
                break

            if p_info["type"] == "evidence_presented":
                p_id = p_info["p_id"]
                power = p_info["power"]
                l_state = f"{p_id}|PWR:{power}"

                if l_state not in lawyer_q:
                    lawyer_q[l_state] = [0.0] * 6  # D1-D5, PASS

                all_def_actions = ["D1", "D2", "D3", "D4", "D5", "PASS"]

                if random.random() < epsilon:
                    lawyer_choice = random.choice(all_def_actions)
                else:
                    l_vals = lawyer_q[l_state]
                    max_l = max(l_vals)
                    best_l = [i for i, v in enumerate(l_vals) if v == max_l]
                    lawyer_choice = all_def_actions[random.choice(best_l)]

                res = env.resolve_lawyer_response(p_id, power, lawyer_choice)

                reward_lawyer = 10.0 if res["is_correct"] else (-5.0 if lawyer_choice != "PASS" else -2.0)
                l_idx = all_def_actions.index(lawyer_choice)
                lawyer_q[l_state][l_idx] += alpha * (reward_lawyer - lawyer_q[l_state][l_idx])

                reward_prosecutor = -reward_lawyer
                next_state_key = env.get_state_key()
                if next_state_key not in prosecutor_q:
                    prosecutor_q[next_state_key] = [0.0] * 7

                max_next_q = max(prosecutor_q[next_state_key])
                prosecutor_q[state_key][action_idx] += alpha * (
                    reward_prosecutor + gamma * max_next_q - prosecutor_q[state_key][action_idx]
                )

            if env.done:
                done = True

    output_data = {
        "prosecutor_q_table": prosecutor_q,
        "lawyer_q_table": lawyer_q
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print(f"ฝึก AI สำเร็จ! บันทึกโมเดลลงในไฟล์: {output_file}")


if __name__ == "__main__":
    train_and_export()
