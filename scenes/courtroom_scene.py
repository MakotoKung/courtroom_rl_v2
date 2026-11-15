# scenes/courtroom_scene.py
import random
import itertools
import pygame

from config import *
from ui import Button
from train_model import CourtEnv
from scenes.base_scene import BaseScene

class CourtroomScene(BaseScene):
    def __init__(self, app, mode=1):
        super().__init__(app)
        self.game_mode = mode
        self.data = app.data
        self.anim = app.anim
        self.sound = app.sound
        self.q_prosecutor = app.q_prosecutor
        self.q_lawyer = app.q_lawyer

        # แผนที่ 120 Permutations (5!)
        self.all_120_perms = list(itertools.permutations(["P1", "P2", "P3", "P4", "P5"]))
        self.seen_perms = set()
        self.last_perm = None

        self.env = CourtEnv(self.data)
        self._init_ui()
        self.reset_match()

    def _init_ui(self):
        self.defense_buttons = []
        d_keys = ["D1", "D2", "D3", "D4", "D5"]
        for i, d_id in enumerate(d_keys):
            d_info = self.data["defense_evidence"][d_id]
            btn = Button(
                (30, 390 + i * 52, 410, 46),
                f"[{i+1}] {d_id}: {d_info['name']}",
                BLUE_LAWYER,
                subtext=d_info["desc"][:48] + "..."
            )
            self.defense_buttons.append((d_id, btn))

        self.btn_pass = Button((30, 652, 410, 44), "[0] ปล่อยผ่าน (ไม่มีหลักฐานโต้)", (90, 90, 100))
        self.btn_restart = Button((SCREEN_WIDTH // 2 - 140, 460, 280, 55), "เล่นอีกครั้ง (Restart)", GREEN_SUCCESS)

    def reset_match(self):
        self.env.reset()
        self._script_turn_idx = 0
        self.anim.display_hp = 5.0
        self.anim.lag_hp = 5.0
        self.current_evidence = None
        self.current_power = 0
        self.last_q_values = [0.0] * 7
        self.last_action_idx = -1
        self.logs = [f"เริ่มเกมในโหมดที่ {self.game_mode}"]

        # รีเซ็ตท่าทางตัวละครทั้งหมดกลับไปเป็น idle
        for c_id in ["judge", "prosecutor", "lawyer", "defendant", "witness"]:
            self.anim.set_character_anim(c_id, "idle", loop=True)

        self.set_speech("ผู้พิพากษา", GOLD_JUDGE, self.data["dialogues"]["intro"])
        self.sound.play("gavel")
        self.phase = "PROSECUTOR_TURN"
        self.ai_timer = 900

    def set_speech(self, speaker, color, text):
        self.speaker = speaker
        self.speaker_color = color
        self.anim.set_dialogue(text)

    def run_prosecutor_turn(self):
        state_key = self.env.get_state_key()
        q_vals = self.q_prosecutor.get(state_key, [0.0] * 7)
        self.last_q_values = q_vals

        # แยกการสุ่มโหมด 1 และ โหมด 2 ตามโครงสร้างล่าสุด
        # แยกการสุ่มโหมด 1 และ โหมด 2 ตามโครงสร้างที่ถูกต้อง
        if self.game_mode == 1:
            remaining_p_m1 = [i for i in range(1, 6) if f"P{i}" not in self.env.submitted]
            if remaining_p_m1:
                valid_actions_m1 = [0] + remaining_p_m1
                action_idx = random.choice(valid_actions_m1)
            else:
                action_idx = 6  # สั่งตัดสินคดีเฉพาะตอนที่ยื่นหลักฐานครบหมดแล้วเท่านั้น
        else:
            remaining_p_m2 = [i for i in range(1, 6) if f"P{i}" not in self.env.submitted]
            if remaining_p_m2:
                valid_actions_m2 = [0] + remaining_p_m2
                action_idx = random.choice(valid_actions_m2)
            else:
                action_idx = 6

        self.last_action_idx = action_idx
        info = self.env.step_prosecutor_action(action_idx)

        if info["type"] == "witness_called":
            self.sound.play("gavel")
            self.anim.set_character_anim("prosecutor", "talk", loop=True)
            self.anim.set_character_anim("witness", "idle", loop=True)
            self.set_speech("อัยการปีศาจดา", PURPLE_PROSECUTOR, self.data["dialogues"]["witness"])
            self.logs.append("อัยการเรียกพยานหนุน (+1 Power ตาถัดไป)")
            self.ai_timer = 1200

        elif info["type"] == "witness_duplicate":
            self.anim.set_character_anim("prosecutor", "idle", loop=True)
            self.set_speech("อัยการปีศาจดา", PURPLE_PROSECUTOR, "พยานยืนอยู่บนแท่นแล้ว เสียจังหวะชะมัด...")
            self.logs.append("อัยการเรียกพยานซ้ำ (เสียเปล่า)")
            self.ai_timer = 900

        elif info["type"] == "evidence_duplicate":
            self.anim.set_character_anim("prosecutor", "idle", loop=True)
            self.set_speech("อัยการปีศาจดา", PURPLE_PROSECUTOR, "หลักฐานชิ้นนี้ข้ายื่นไปแล้ว...")
            self.logs.append("อัยการยื่นหลักฐานซ้ำ")
            self.ai_timer = 900

        elif info["type"] == "evidence_presented":
            p_id = info["p_id"]
            power = info["power"]
            self.current_evidence = p_id
            self.current_power = power
            ev_obj = self.data["prosecutor_evidence"][p_id]

            self.sound.play("slam")
            self.anim.trigger_shake(intensity=6, duration_ms=250)
            # เล่นแอนิเมชันตบโต๊ะจนถึงเฟรมสุดท้าย (loop=False)
            self.anim.set_character_anim("prosecutor", "slam", loop=False, force_restart=True)
            self.anim.set_character_anim("lawyer", "idle", loop=True)

            self.set_speech("อัยการปีศาจดา", PURPLE_PROSECUTOR, f"[{p_id} ★x{power}] {ev_obj['dialogue_present']}")
            self.logs.append(f"อัยการยื่น {p_id} ({ev_obj['name']}) ความหนักแน่น ★{power}")

            if self.game_mode == 1:
                self.phase = "PLAYER_WAIT"
            else:
                self.phase = "AI_LAWYER_THINK"
                self.ai_timer = 1100

        elif info["type"] in ("verdict_guilty", "verdict_not_guilty"):
            self._finish_game()

    def handle_lawyer_choice(self, d_choice):
        if not self.current_evidence:
            return
        res = self.env.resolve_lawyer_response(self.current_evidence, self.current_power, d_choice)

        if d_choice == "PASS":
            self.sound.play("buzz")
            self.anim.trigger_shake(intensity=12, duration_ms=400)
            self.anim.set_character_anim("lawyer", "damage", loop=False, force_restart=True)
            self.set_speech("อัยการปีศาจดา", PURPLE_PROSECUTOR, self.data["dialogues"]["pass"])
            self.logs.append(f"ทนายปล่อยผ่าน! เสีย HP -{res['hp_loss']}")
        elif res["is_correct"]:
            d_obj = self.data["defense_evidence"][d_choice]
            self.sound.play("ding")
            self.anim.trigger_flash(GREEN_SUCCESS, 200)
            # ทนายชี้หน้าคัดค้านจนถึงเฟรมสุดท้าย
            self.anim.set_character_anim("lawyer", "objection", loop=False, force_restart=True)
            self.anim.set_character_anim("prosecutor", "damage", loop=False, force_restart=True)
            self.set_speech("ทนายแตน", BLUE_LAWYER, d_obj["dialogue_counter"])
            self.logs.append(f"โต้ถูกด้วย {d_choice}! (เสีย HP -{res['hp_loss']})")
        else:
            self.sound.play("buzz")
            self.anim.trigger_shake(intensity=14, duration_ms=450)
            self.anim.set_character_anim("lawyer", "damage", loop=False, force_restart=True)
            self.set_speech("ทนายแตน", BLUE_LAWYER, self.data["dialogues"]["counter_fail"])
            self.logs.append(f"โต้ผิดด้วย {d_choice}! เสีย HP -{res['hp_loss']}")

        self.current_evidence = None
        if self.env.done:
            self._finish_game()
        else:
            self.phase = "PROSECUTOR_TURN"
            self.ai_timer = 1300

    def run_ai_lawyer_turn(self):
        p_id = self.current_evidence
        l_state = f"{p_id}|PWR:{self.current_power}"
        all_def_actions = ["D1", "D2", "D3", "D4", "D5", "PASS"]

        if l_state in self.q_lawyer:
            q_vals = self.q_lawyer[l_state]
            best_idx = q_vals.index(max(q_vals))
            choice = all_def_actions[best_idx]
        else:
            choice = self.data["prosecutor_evidence"][p_id]["counter"]

        self.handle_lawyer_choice(choice)

    def _finish_game(self):
        self.phase = "GAME_OVER"
        self.sound.play("win" if self.env.winner == "lawyer" else "gavel")
        self.anim.set_character_anim("judge", "gavel", loop=False, force_restart=True)

        if len(self.env.submitted) == 5:
            perm_tuple = tuple(self.env.submitted)
            self.seen_perms.add(perm_tuple)
            self.last_perm = perm_tuple

        if self.env.winner == "lawyer":
            self.set_speech("ผู้พิพากษา", GOLD_JUDGE, self.data["dialogues"]["verdict_not_guilty"])
            self.logs.append("ผลตัดสิน: NOT GUILTY (ทนายชนะ)")
        else:
            self.set_speech("ผู้พิพากษา", GOLD_JUDGE, self.data["dialogues"]["verdict_guilty"])
            self.logs.append("ผลตัดสิน: GUILTY (อัยการชนะ)")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and not self.anim.is_dialogue_done():
            self.anim.skip_dialogue()

        if self.phase == "PLAYER_WAIT" and self.game_mode == 1:
            for d_id, btn in self.defense_buttons:
                if btn.handle_event(event):
                    self.handle_lawyer_choice(d_id)
            if self.btn_pass.handle_event(event):
                self.handle_lawyer_choice("PASS")

            if event.type == pygame.KEYDOWN:
                key_map = {
                    pygame.K_1: "D1", pygame.K_2: "D2", pygame.K_3: "D3",
                    pygame.K_4: "D4", pygame.K_5: "D5", pygame.K_0: "PASS"
                }
                if event.key in key_map:
                    self.handle_lawyer_choice(key_map[event.key])

        elif self.phase == "GAME_OVER":
            if self.btn_restart.handle_event(event):
                self.reset_match()

    def update(self, dt_ms):
        self.anim.update(dt_ms, self.env.hp)

        if self.phase == "PROSECUTOR_TURN":
            self.ai_timer -= dt_ms
            if self.ai_timer <= 0:
                self.run_prosecutor_turn()

        elif self.phase == "AI_LAWYER_THINK":
            self.ai_timer -= dt_ms
            if self.ai_timer <= 0:
                self.run_ai_lawyer_turn()

    def draw_stage(self, surface, tick_ms):
        stage_rect = pygame.Rect(460, 65, 540, 290)
        pygame.draw.rect(surface, (48, 36, 32), stage_rect, border_radius=12)
        pygame.draw.rect(surface, GOLD_JUDGE, stage_rect, 2, border_radius=12)

        sorted_q = sorted(self.last_q_values, reverse=True)
        q_gap = min(1.0, max(0.0, (sorted_q[0] - sorted_q[1]) / 50.0)) if len(sorted_q) >= 2 else 0.0

        self.anim.draw_character(surface, "judge", 630, 65, tick_ms=tick_ms)
        self.anim.draw_character(surface, "prosecutor", 475, 95, tick_ms=tick_ms, extra_param=q_gap)
        self.anim.draw_character(surface, "lawyer", 785, 95, tick_ms=tick_ms)

        def_shake = (self.env.get_defendant_status() - 1) * 2
        self.anim.draw_character(surface, "defendant", 830, 125, tick_ms=tick_ms, extra_param=def_shake)

        if self.env.witness_active:
            self.anim.draw_character(surface, "witness", 630, 115, tick_ms=tick_ms)

        pygame.draw.rect(surface, (95, 60, 35), (462, 295, 536, 58), border_bottom_left_radius=10, border_bottom_right_radius=10)

    def draw_dialogue_box(self, surface):
        box_rect = pygame.Rect(460, 365, 540, 130)
        pygame.draw.rect(surface, (22, 24, 34), box_rect, border_radius=10)
        pygame.draw.rect(surface, self.speaker_color, box_rect, 3, border_radius=10)

        tag_rect = pygame.Rect(475, 352, 160, 28)
        pygame.draw.rect(surface, self.speaker_color, tag_rect, border_radius=6)
        spk_surf = self.app.font_sm.render(self.speaker, True, WHITE)
        surface.blit(spk_surf, spk_surf.get_rect(center=tag_rect.center))

        shown_text = self.anim.full_text[:self.anim.visible_chars]
        words = shown_text.split(" ")
        lines, cur = [], ""
        for w in words:
            if len(cur + w) < 42:
                cur += w + " "
            else:
                lines.append(cur)
                cur = w + " "
        lines.append(cur)

        for idx, line in enumerate(lines[:3]):
            txt_surf = self.app.font_md.render(line, True, WHITE)
            surface.blit(txt_surf, (480, 390 + idx * 30))

    def draw_right_panel(self, surface):
        panel = pygame.Rect(1015, 65, 245, 630)
        pygame.draw.rect(surface, PANEL_BG, panel, border_radius=10)

        title = self.app.font_md.render("AI Q-Values (7 Actions)", True, YELLOW_WARN)
        surface.blit(title, (1028, 75))

        labels = ["พยาน", "P1", "P2", "P3", "P4", "P5", "ตัดสิน"]
        max_abs = max([abs(v) for v in self.last_q_values] + [1.0])
        for i, val in enumerate(self.last_q_values):
            bx = 1030 + i * 31
            by = 165
            bar_h = int((val / max_abs) * 45)
            color = GOLD_JUDGE if i == self.last_action_idx else (GREEN_SUCCESS if val >= 0 else RED_DANGER)
            if bar_h >= 0:
                pygame.draw.rect(surface, color, (bx, by - bar_h, 22, max(2, bar_h)))
            else:
                pygame.draw.rect(surface, color, (bx, by, 22, max(2, -bar_h)))
            lbl = self.app.font_sm.render(labels[i], True, WHITE)
            surface.blit(lbl, (bx, 215))

        map_title = self.app.font_md.render(f"แผนที่ 120 กรณี ({len(self.seen_perms)}/120)", True, WHITE)
        surface.blit(map_title, (1028, 250))
        for idx, perm in enumerate(self.all_120_perms):
            col = idx % 12
            row = idx // 12
            cx = 1030 + col * 18
            cy = 282 + row * 16
            c_rect = pygame.Rect(cx, cy, 15, 13)
            fill_col = GREEN_SUCCESS if perm in self.seen_perms else (65, 70, 90)
            pygame.draw.rect(surface, fill_col, c_rect, border_radius=2)
            if perm == self.last_perm:
                pygame.draw.rect(surface, RED_DANGER, c_rect, 2)

        log_title = self.app.font_md.render("บันทึกศาล (Log)", True, WHITE)
        surface.blit(log_title, (1028, 455))
        for i, entry in enumerate(self.logs[-6:]):
            l_surf = self.app.font_sm.render("• " + entry[:28], True, (210, 215, 225))
            surface.blit(l_surf, (1028, 485 + i * 26))

    def draw(self, surface):
        tick_ms = pygame.time.get_ticks()

        left_panel = pygame.Rect(20, 65, 430, 635)
        pygame.draw.rect(surface, PANEL_BG, left_panel, border_radius=10)

        hp_lbl = self.app.font_md.render(f"ความน่าเชื่อถือทนาย (HP): {self.env.hp} / 5", True, WHITE)
        surface.blit(hp_lbl, (35, 78))
        self.anim.draw_hp_bar(surface, 35, 110, 395, 22, max_hp=5)

        seq_lbl = self.app.font_sm.render(f"ลำดับที่อัยการยื่น: {' -> '.join(self.env.submitted) or 'ยังไม่มี'}", True, YELLOW_WARN)
        surface.blit(seq_lbl, (35, 145))

        ev_box = pygame.Rect(35, 175, 395, 195)
        pygame.draw.rect(surface, (32, 35, 48), ev_box, border_radius=8)
        pygame.draw.rect(surface, PURPLE_PROSECUTOR, ev_box, 2, border_radius=8)

        if self.current_evidence:
            ev = self.data["prosecutor_evidence"][self.current_evidence]
            stars = "★" * self.current_power
            t1 = self.app.font_md.render(f"หลักฐาน: {ev['id']} - {ev['name']} ({stars})", True, RED_DANGER)
            t2 = self.app.font_sm.render(ev["desc"][:46], True, WHITE)
            t3 = self.app.font_sm.render(ev["desc"][46:], True, WHITE)
            surface.blit(t1, (48, 190))
            surface.blit(t2, (48, 228))
            surface.blit(t3, (48, 255))
        else:
            wait_msg = "กำลังรอการเคลื่อนไหวของอัยการ..." if self.phase != "GAME_OVER" else "การพิจารณาคดีสิ้นสุดลงแล้ว"
            surface.blit(self.app.font_md.render(wait_msg, True, GRAY), (55, 255))

        can_click = (self.game_mode == 1 and self.phase == "PLAYER_WAIT")
        for _, btn in self.defense_buttons:
            btn.disabled = not can_click
            btn.draw(surface, self.app.font_md, self.app.font_sm)
        self.btn_pass.disabled = not can_click
        self.btn_pass.draw(surface, self.app.font_md, self.app.font_sm)

        self.draw_stage(surface, tick_ms)
        self.draw_dialogue_box(surface)
        self.draw_right_panel(surface)

        hint_box = pygame.Rect(460, 505, 540, 190)
        pygame.draw.rect(surface, PANEL_BG, hint_box, border_radius=10)
        mode_txt = "โหมด 1: คุณควบคุมทนายแตน (กดปุ่ม 1-5 หรือคลิกหลักฐานโต้)" if self.game_mode == 1 else "โหมด 2: AI ทนายแตนกำลังเล่นอัตโนมัติจาก Q-table"
        surface.blit(self.app.font_md.render(mode_txt, True, GREEN_SUCCESS), (478, 520))
        surface.blit(self.app.font_sm.render("วิธีเพิ่ม Sprite/ท่าทาง: กำหนดพิกัด Crop ใน game_data.json และวางไฟล์ใน assets/images/", True, (200, 205, 215)), (478, 555))
        surface.blit(self.app.font_sm.render("วิธีฝึก AI ใหม่: รันคำสั่ง python train_model.py เพื่อสร้าง model_q_table_noob.json", True, (200, 205, 215)), (478, 585))

        if self.phase == "GAME_OVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 165))
            surface.blit(overlay, (0, 0))

            res_text = "NOT GUILTY — ทนายแตนชนะ!" if self.env.winner == "lawyer" else "GUILTY — อัยการปีศาจดาชนะ!"
            res_col = GREEN_SUCCESS if self.env.winner == "lawyer" else RED_DANGER
            banner = self.app.font_lg.render(res_text, True, res_col)
            surface.blit(banner, banner.get_rect(center=(SCREEN_WIDTH // 2, 360)))
            self.btn_restart.draw(surface, self.app.font_md, self.app.font_sm)
