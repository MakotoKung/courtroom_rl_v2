import pygame
import json
import os
from config import *
from scenes.base_scene import BaseScene
from textbox import Textbox
from evidence_menu import EvidenceMenu

class BaseDialogueScene(BaseScene):
    def __init__(self, app):
        super().__init__(app)

        self.player_evidence_db = []
        evidence_path = "evidence.json"
        
        if os.path.exists(evidence_path):
            with open(evidence_path, "r", encoding="utf-8") as f:
                self.player_evidence_db = json.load(f)
        else:
            print(f"Warning: Not found {evidence_path}, using empty evidence list.")

        # ส่งฐานข้อมูลหลักฐานเข้าสู่หน้าต่าง EvidenceMenu
        self.evidence_menu = EvidenceMenu(self.player_evidence_db)

        self.font = pygame.font.SysFont(None, 28)
        self.textbox = Textbox(50, SCREEN_HEIGHT - 190, SCREEN_WIDTH - 100, 160, self.font)
        
        self.dialogue_list = []
        self.current_index = 0
        self.current_bg = None
        self.characters = {}  # เก็บข้อมูลตัวละครทั้งหมด
        
        # ---> เพิ่มตัวเก็บรายชื่อตัวละครที่จะแสดงผลในประโยคปัจจุบัน <---
        self.current_dialogue_image = None
        self.image_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)
        self.current_visible_chars = []

    def add_character(self, name, animator_obj, x, y):
        self.characters[name] = {
            "animator": animator_obj,
            "x": x,
            "y": y
        }

    def load_dialogue_data(self, script_data):
        self.dialogue_list = script_data
        self.current_index = 0
        if self.dialogue_list:
            self.update_dialogue_state()

    def update_dialogue_state(self):
        if self.current_index < len(self.dialogue_list):
            data = self.dialogue_list[self.current_index]
            
            # 1. เปลี่ยน Background
            if "bg" in data:
                bg_path = data["bg"]
                self.current_bg = pygame.transform.scale(
                    pygame.image.load(bg_path).convert(), (SCREEN_WIDTH, SCREEN_HEIGHT)
                )
            else:
                self.current_bg = None
            
            # 2. ตั้งค่าบทพูดและผู้พูด
            speaker = data.get("speaker", "")
            text = data.get("text", "")
            self.textbox.set_text(speaker, text)

            # 3. เล่นเสียงประกอบ (ถ้ามีระบุไว้ใน JSON)
            if "sound" in data and data["sound"]:
                sound_path = data["sound"]
                if os.path.exists(sound_path):
                    try:
                        sound_effect = pygame.mixer.Sound(sound_path)
                        sound_effect.play()  # สั่งเล่นเสียงทันทีที่เปลี่ยนมาถึงประโยคนี้
                    except Exception as e:
                        print(f"Error loading/playing sound {sound_path}: {e}")
                else:
                    print(f"Warning: Sound file not found -> {sound_path}")
            
            # ---> 3. จัดการว่าใครควรแสดงบนจอในบรรทัดนี้ <---
            # ถ้าระบุ "visible": ["Judge", "Phoenix"] มาในสคริปต์ ให้แสดงตามนั้น
            # แต่ถ้าไม่ได้ระบุ ให้แสดงเฉพาะคนที่เป็น "speaker" อัตโนมัติ
            if "visible" in data:
                self.current_visible_chars = data["visible"]
            else:
                if speaker:
                    self.current_visible_chars = [speaker]
                else:
                    self.current_visible_chars = []

            action_name = data.get("action", None)
            if action_name and speaker in self.characters:
                # สั่งให้ตัวละครของผู้พูดเปลี่ยนไปเล่น Action นั้นๆ ทันที
                char_animator = self.characters[speaker]["animator"]
                char_animator.play_ani(action_name, loop=True)
            # ---> 5. จัดการโหลดรูปภาพประกอบ (ถ้ามีระบุไว้ในสคริปต์บรรทัดนี้) <---
            self.current_dialogue_image = None
            if "image" in data and data["image"]:
                img_path = data["image"]
                if os.path.exists(img_path):
                    img = pygame.image.load(img_path).convert_alpha()
                    
                    # เช็คว่าใน JSON มีการกำหนด "size" มาไหม ถ้ามีให้ใช้ค่านั้น ถ้าไม่มีให้ใช้ค่า Default (เช่น 250x250)
                    img_size = tuple(data.get("size", [250, 250]))
                    self.current_dialogue_image = pygame.transform.scale(img, img_size)
                    if "pos" in data:
                        self.image_pos = data["pos"]
                else:
                    print(f"Warning: ไม่พบไฟล์รูปภาพประกอบที่ {img_path}")
        else:
            self.on_dialogue_finish()

    def on_dialogue_finish(self):
        pass

    def handle_event(self, event):
        '''
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not self.textbox.is_finished:
                    self.textbox.skip_to_end()
                else:
                    self.current_index += 1
                    self.update_dialogue_state()
                    
            elif event.key == pygame.K_ESCAPE:
                from scenes.menu_scene import MenuScene
                self.app.change_scene(MenuScene(self.app))
                '''
        # 1. ถ้าหน้าต่าง Evidence เปิดอยู่ ให้ส่ง Event ไปที่เมนูหลักฐานก่อน
        if self.evidence_menu.is_open:
            chosen_id = self.evidence_menu.handle_event(event)
            if chosen_id is not None:
                self.process_evidence_choice(chosen_id)
            return

        # 2. กดปุ่ม TAB เพื่อเปิด/ปิดหน้าต่างหลักฐาน
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.evidence_menu.can_present = self.waiting_for_evidence
            self.evidence_menu.toggle()
            return

        # 3. จัดการปุ่ม Spacebar (ป้องกันการกดรัวที่ทำให้ Typewriter สะดุด)
        is_action_triggered = False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            is_action_triggered = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # ปุ่ม 1 คือคลิกซ้าย
            is_action_triggered = True

        if is_action_triggered:
            # ถ้าตัวหนังสือกำลังพิมพ์อยู่ (ยังไม่จบ) ให้สั่งข้ามมาแสดงผลจนจบก่อนทันที
            if not self.textbox.is_finished:
                self.textbox.skip_to_end()
            else:
                # แต่ถ้าตัวหนังสือแสดงครบถ้วนแล้ว ถึงจะยอมให้เปลี่ยนสถานะหรือเปลี่ยนบรรทัดถัดไป
                if self.waiting_for_evidence:
                    if not self.evidence_menu.is_open:
                        self.evidence_menu.can_present = True
                        self.evidence_menu.toggle()
                else:
                    self.current_index += 1
                    self.update_dialogue_state()
                        
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from scenes.menu_scene import MenuScene
            self.app.change_scene(MenuScene(self.app))

    def update(self, dt_ms):
        self.textbox.update(dt_ms)
        for char_data in self.characters.values():
            char_data["animator"].update(dt_ms)

    def draw(self, surface):
        if self.current_bg:
            surface.blit(self.current_bg, (0, 0))
        else:
            surface.fill(DARK_BG)
            
        # ---> 4. วาดเฉพาะตัวละครที่มีรายชื่ออยู่ใน current_visible_chars เท่านั้น! <---
        for char_name in self.current_visible_chars:
            if char_name in self.characters:
                char_data = self.characters[char_name]
                anim = char_data["animator"]
                anim.draw(surface, char_data["x"], char_data["y"])

        if self.current_dialogue_image:
            img_rect = self.current_dialogue_image.get_rect(center=self.image_pos)
            surface.blit(self.current_dialogue_image, img_rect)
        
        self.textbox.draw(surface)
        self.evidence_menu.draw(surface, self.app.font_sm, self.app.font_md)