# scenes/ai_judge_scene.py
# คัดลอกจาก judge_scene.py + โหมดให้ Model (Q-table) เล่นเอง
import pygame
import json
import os
import random
from config import *
from scenes.base_dialogue_scene import BaseDialogueScene
from characteranimation import CharacterAnimator
from evidence_menu import EvidenceMenu

MODEL_PATH = "Model/q_table.json"
END_INDEX = 107

# ดีเลย์ของ AI (ms)
AI_LINE_DELAY = 200      #Defualt 1200 # รอหลังบทพูดพิมพ์จบ ก่อนไปประโยคถัดไป
AI_THINK_DELAY = 500     #defautl 1500 # รอก่อนเลือกหลักฐาน
AI_PRESENT_DELAY = 1200   # โชว์หลักฐานที่เลือกก่อนยื่น


class QAgent:
    """โหลด Q-table จาก train_model.py แล้วเลือกหลักฐานแบบ greedy"""
    def __init__(self, path=MODEL_PATH):
        self.q = {}
        self.policy = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.q = data.get("q_table", {})
            self.policy = data.get("policy", {})
        else:
            print(f"Warning: ไม่พบ {path} -> AI จะสุ่มเลือกหลักฐาน")

    def choose(self, state, evidence_ids):
        qs = self.q.get(state)
        if qs:
            return max(evidence_ids, key=lambda e: qs.get(e, 0.0))
        cp = state.split("|")[0]
        pid = self.policy.get(cp)
        if pid in evidence_ids:
            return pid
        return random.choice(evidence_ids)


class judge_ai(BaseDialogueScene):
    def __init__(self, app):
        super().__init__(app)

        pygame.mixer.stop() #stop Souund before play new Sound
        pygame.mixer.music.stop()
        self.ost = pygame.mixer.Sound("assets/sounds/aceOST.mp3")
        self.ost.set_volume(0.05)
        self.ost.play(-1)  # Play the OST on loop

        # 1. ลงทะเบียนและตั้งค่าตัวละครที่ใช้ในฉากนี้
        judge_anim = CharacterAnimator(char_name="Judge")
        judge_anim.add_action("talking", "assets/images/judge/judge_talk.png", total_frames=5,duration=200, custom_width=120, custom_height=150)
        judge_anim.add_action("no", "assets/images/judge/judge_no.png", total_frames=8, duration=200, custom_width=122, custom_height=100)
        judge_anim.play_ani("talking", loop=True)
        judge_anim.set_scale(4)
        self.add_character("Judge", judge_anim, x=400, y=SCREEN_HEIGHT - 550)

        payne_anim = CharacterAnimator(char_name="Payne")
        payne_anim.add_action("talking", "assets/images/payne/payne_talk.png",total_frames=5,duration=130,custom_width=93)
        payne_anim.add_action("hah", "assets/images/payne/payne_hah.png",total_frames=4,duration=200,custom_width=115,custom_height=120)
        payne_anim.play_ani("talking",loop=True)
        payne_anim.set_scale(4)
        self.add_character("Payne", payne_anim, x=800, y= SCREEN_HEIGHT - 480)

        phoenix_ani = CharacterAnimator(char_name="Phoenix")
        phoenix_ani.add_action("talking", "assets/images/phoenix/Phoenix_talk.png",total_frames=4, duration=130, custom_width=135)
        phoenix_ani.add_action("paper", "assets/images/phoenix/Phoenix_paper2.png",total_frames=6, duration=220, custom_width=180)
        phoenix_ani.add_action("finger", "assets/images/phoenix/Phoenix_finger.png",total_frames=1, duration=100, custom_width=260)
        phoenix_ani.play_ani("talking", loop=True)
        phoenix_ani.set_scale(4)
        self.add_character("Phoenix", phoenix_ani, x=200, y= SCREEN_HEIGHT-500)

        larry  = CharacterAnimator(char_name="Larry")
        larry.add_action("talking","assets/images/larry/larry_talk.png",total_frames=4,duration=250,custom_width=170 ,custom_height=185)
        larry.add_action("emm", "assets/images/larry/larry_emm.png",total_frames=1)
        larry.play_ani("talking",loop=True)
        larry.set_scale(4)
        self.add_character("Larry",larry,x= 300, y= SCREEN_HEIGHT - 500)

        frank = CharacterAnimator(char_name="Frank")
        frank.add_action("talking", "assets/images/frank/frank_talk2.png",total_frames=4,duration=200,custom_width=102)
        frank.add_action("angry", "assets/images/frank/frank_angry.png",total_frames=4, duration=220, custom_width=110)
        frank.play_ani("talking",loop=True)
        frank.set_scale(4)
        self.add_character("Frank",frank,x= 400, y= SCREEN_HEIGHT -500)

        clock = CharacterAnimator(char_name="Clock")
        clock.add_action("talking", "assets/images/frank/frank_talk2.png",total_frames=4,duration=200,custom_width=102)
        self.add_character("Clock",clock,x= 400, y= SCREEN_HEIGHT -500)

        # --- ตัว AI ---
        if not os.path.exists(MODEL_PATH):
            from train_model import train_and_export
            train_and_export(output_file=MODEL_PATH)
        self.agent = QAgent(MODEL_PATH)
        self.ai_timer = 0
        self.ai_stage = "idle"      # idle -> selected
        self.ai_choice = None

        script_path = "dialogue/judge_scene.json"
        with open(script_path, "r", encoding="utf-8") as f:
            loaded_script = json.load(f)

        self.load_dialogue_data(loaded_script)

        self.player_evidence_db = []
        evidence_path = "evidence.json"
        if os.path.exists(evidence_path):
            with open(evidence_path, "r", encoding="utf-8") as f:
                self.player_evidence_db = json.load(f)

        self.evidence_menu = EvidenceMenu(self.player_evidence_db)

        self.waiting_for_evidence = False
        self.correct_evidence_target = ""
        self.jump_on_correct = 0
        self.jump_on_wrong = 0

    def on_exit(self):
        self.ost.stop()

    def update_dialogue_state(self):
        super().update_dialogue_state()
        if self.current_index < len(self.dialogue_list):
            data = self.dialogue_list[self.current_index]
            self.waiting_for_evidence = data.get("expects_evidence", False)
            if self.waiting_for_evidence:
                self.correct_evidence_target = data.get("correct_evidence_id", "")
                self.jump_on_correct = data.get("on_correct_jump", self.current_index + 1)
                self.jump_on_wrong = data.get("on_wrong_jump", self.current_index + 1)
                if not self.evidence_menu.is_open:
                    self.evidence_menu.can_present = True
                    self.evidence_menu.toggle()
            self.ai_stage = "idle"
            self.ai_timer = 0

    # ---------- AI ----------
    def handle_event(self, event):
        """โหมด AI: ไม่รับ input เล่น รับแค่ ESC และปุ่ม Return to Menu"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from scenes.menu_scene import MenuScene
            self.app.change_scene(MenuScene(self.app))
            return
        if self.show_menu_button:
            super().handle_event(event)

    def update(self, dt_ms):
        super().update(dt_ms)
        if self.waiting_game_over_delay or self.show_menu_button:
            return
        if not self.textbox.is_finished:
            self.ai_timer = 0
            return

        if self.waiting_for_evidence:
            self._ai_evidence_step(dt_ms)
        else:
            self.ai_timer += dt_ms
            if self.ai_timer >= AI_LINE_DELAY:
                self.ai_timer = 0
                self._ai_next_line()

    def _ai_next_line(self):
        # Bad End: 107 คือจุดจบ (ใน Base ไม่ได้หยุดที่ 107 ตอน game over จะไหลต่อไป 108+)
        if self.is_game_over and self.current_index >= END_INDEX:
            self.on_dialogue_finish()
            return
        self.handle_event_space()

    def handle_event_space(self):
        # ส่ง SPACE ปลอมเข้า logic เดิมของ BaseDialogueScene
        BaseDialogueScene.handle_event(
            self, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))

    def _ai_evidence_step(self, dt_ms):
        menu = self.evidence_menu
        if not menu.is_open:
            menu.can_present = True
            menu.toggle()
        self.ai_timer += dt_ms

        if self.ai_stage == "idle":
            if self.ai_timer >= AI_THINK_DELAY:
                ids = [e["id"] for e in menu.evidence_db]
                if not ids:
                    return
                state = f"{self.current_index}|{self.current_hp}"
                self.ai_choice = self.agent.choose(state, ids)
                menu.selected_index = ids.index(self.ai_choice)
                print(f"[AI] state={state} -> {self.ai_choice}")
                self.ai_stage = "selected"
                self.ai_timer = 0
        elif self.ai_stage == "selected":
            if self.ai_timer >= AI_PRESENT_DELAY:
                choice = self.ai_choice
                menu.is_open = False
                self.ai_stage = "idle"
                self.ai_timer = 0
                self.process_evidence_choice(choice)

    def draw(self, surface):
        super().draw(surface)
        self.evidence_menu.draw(surface, self.app.font_sm, self.app.font_md)

    def on_dialogue_finish(self):
        if self.is_game_over:
            super().on_dialogue_finish()
            return
        from scenes.menu_scene import MenuScene
        self.app.change_scene(MenuScene(self.app))
