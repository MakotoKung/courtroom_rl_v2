import pygame
import json
import os 
from config import *
from scenes.base_dialogue_scene import BaseDialogueScene
from characteranimation import CharacterAnimator
from evidence_menu import EvidenceMenu

class judge(BaseDialogueScene):
    def __init__(self, app):
        super().__init__(app)
        
        # 1. ลงทะเบียนและตั้งค่าตัวละครที่ใช้ในฉากนี้
        judge_anim = CharacterAnimator(char_name="Judge")
        judge_anim.add_action("talking", "assets/images/judge/judge_talk.png", total_frames=5,duration=200, custom_width=120, custom_height=150)
        judge_anim.play_ani("talking", loop=True)
        judge_anim.set_scale(4)
        
        # 2. เพิ่มตัวละครเข้าสู่ระบบพร้อมกำหนดพิกัด x และ y ตรงนี้ได้เลย!
        self.add_character("Judge", judge_anim, x=400, y=SCREEN_HEIGHT - 550)

        payne_anim = CharacterAnimator(char_name="Payne")
        payne_anim.add_action("talking", "assets/images/payne/payne_talk.png",total_frames=5,duration=130,custom_width=93)
        payne_anim.add_action("hah", "assets/images/payne/payne_hah.png",total_frames=4,duration=200,custom_width=115,custom_height=120)
        payne_anim.play_ani("talking",loop=True)
        payne_anim.set_scale(4)
        self.add_character("Payne", payne_anim, x=800, y= SCREEN_HEIGHT - 500)

        phoenix_ani = CharacterAnimator(char_name="Phoenix")
        phoenix_ani.add_action("talking", "assets/images/phoenix/Phoenix_talk.png",total_frames=4, duration=130, custom_width=135)
        phoenix_ani.add_action("paper", "assets/images/phoenix/Phonix_paper2.png",total_frames=6, duration=200, custom_width=174)
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
        frank.play_ani("talking",loop=True)
        frank.set_scale(4)
        self.add_character("Frank",frank,x= 400, y= SCREEN_HEIGHT -500)
        # 2. กำหนด Script บทพูดทั้งหมด (รองรับการสลับฉากหลัง bg ระหว่างคุยได้อิสระ)
        script_path = "dialogue/judge_scene.json"

        # ต้องใส่ encoding="utf-8" เพื่อให้ Python อ่านภาษาไทยได้ถูกต้อง
        with open(script_path, "r", encoding="utf-8") as f:
            loaded_script = json.load(f)

        # 3. โหลดสคริปต์เข้าสู่ระบบ
        self.load_dialogue_data(loaded_script)

        self.player_evidence_db = []
        evidence_path = "evidence.json"
        if os.path.exists(evidence_path):
            with open(evidence_path, "r", encoding="utf-8") as f:
                self.player_evidence_db = json.load(f)

        self.evidence_menu = EvidenceMenu(self.player_evidence_db)
        
        # ตัวแปรสถานะรอหลักฐานตามเงื่อนไขใน JSON
        self.waiting_for_evidence = False
        self.correct_evidence_target = ""
        self.jump_on_correct = 0
        self.jump_on_wrong = 0

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


    def handle_event(self, event):
        # ถ้าเปิดหน้าต่าง Evidence เมนูกลางอยู่ ให้ส่ง Event ไปที่ EvidenceMenu ก่อน
        if self.evidence_menu.is_open:
            chosen_id = self.evidence_menu.handle_event(event)
            if chosen_id is not None:
                self.process_evidence_choice(chosen_id)
            return
        '''
        # กดปุ่ม TAB เพื่อเปิดดูหลักฐานสำหรับการ Test
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.evidence_menu.toggle()
            return
        super().handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self.textbox.is_finished and self.waiting_for_evidence:
                self.evidence_menu.toggle()
        '''
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.evidence_menu.can_present = False  # <--- ถ้ากด TAB เอง จะถูกเซ็ตเป็น False (ห้ามยื่น)
            self.evidence_menu.toggle()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not self.textbox.is_finished:
                    self.textbox.skip_to_end()
                else:
                    if self.waiting_for_evidence:
                        if not self.evidence_menu.is_open:
                            self.evidence_menu.can_present = True  # <--- [จุดที่ 2] เปลี่ยนเป็น True ตรงนี้ (กดเปิดตอนถึงคำถาม)
                            self.evidence_menu.toggle()
                    else:
                        self.current_index += 1
                        self.update_dialogue_state()
        # จัดการปุ่มกดปกติของ Scene
        super().handle_event(event)

    def process_evidence_choice(self, chosen_id):
        print(f"Player presented evidence ID: {chosen_id}")
        if chosen_id == self.correct_evidence_target:
            print("CORRECT EVIDENCE!")
            self.current_index = self.jump_on_correct
        else:
            print("WRONG EVIDENCE!")
            self.current_index = self.jump_on_wrong
            
        self.waiting_for_evidence = False
        self.update_dialogue_state()


    def draw(self, surface):
        super().draw(surface)  # วาดฉากหลัง, ตัวละคร, และ Textbox ตามปกติ
        self.evidence_menu.draw(surface, self.app.font_sm, self.app.font_md)  # วาดเมนูหลักฐานทับด้านบนสุด
    
    def on_dialogue_finish(self):
        """เมื่อบทพูดในหน้านี้จบลงทั้งหมด จะสลับไป Scene ถัดไปอัตโนมัติ"""
        print("บทสนทนาหน้า Judge จบแล้ว กำลังเปลี่ยน Scene ไปหน้า Evidence...")
        from scenes.grave import GavelScene
        self.app.change_scene(GavelScene(self.app))