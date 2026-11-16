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

        self.is_game_over = False
        self.waiting_for_evidence = False
        self.correct_evidence_target = ""
        self.jump_on_correct = 0
        self.jump_on_wrong = 0
            
        # ระบบ HP (มี HP เต็ม 5 หน่วย / แบ่งเป็น 5 ช่อง ช่องละ 1 หน่วย)
        self.max_hp = 5
        self.current_hp = 5
        self.game_over_jump_index = 109
        self.waiting_game_over_delay = False
        self.game_over_timer = 0
        self.show_menu_button = False
        # กำหนดขนาดและตำแหน่งของปุ่มกลับหน้าเมนู
        self.menu_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 40, 240, 50)

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
        if  not self.is_game_over and self.current_index == 108:
            print("Happy End completed (Reached 107 limit). Returning to MenuScene...")
            from scenes.menu_scene import MenuScene
            self.app.change_scene(MenuScene(self.app))
            return
        elif  self.is_game_over and self.current_index == 108:
                    print("Happy End completed (Reached 107 limit). Returning to MenuScene...")
                    from scenes.menu_scene import MenuScene
                    self.app.change_scene(MenuScene(self.app))
                    return

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
            
            self.render_textbox = data.get("show_textbox", True)
            # 2. ตั้งค่าบทพูดและผู้พูด
            speaker = data.get("speaker", "")
            text = data.get("text", "")
            self.textbox.set_text(speaker, text)

            self.waiting_for_evidence = data.get("expects_evidence", False)
            if self.waiting_for_evidence:
                self.correct_evidence_target = data.get("correct_evidence_id", "")
                self.jump_on_correct = data.get("on_correct_jump", self.current_index + 1)
                self.jump_on_wrong = data.get("on_wrong_jump", self.current_index + 1)
                # สามารถกำหนด "game_over_jump" ไว้ใน JSON ได้ ถ้าไม่ใส่จะใช้ค่า default เป็น jump_on_wrong
                self.game_over_jump_index = data.get("game_over_jump", -1)
                
                if not self.evidence_menu.is_open:
                    self.evidence_menu.can_present = True
                    self.evidence_menu.toggle()


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


    def process_evidence_choice(self, chosen_id):
        if chosen_id == self.correct_evidence_target:
            print("CORRECT EVIDENCE! (Happy End path)")
            self.is_game_over = False  # ยืนยันว่าเลือดไม่หมด เป็นเส้นทางปกติ
            self.current_index = self.jump_on_correct
        else:
            print("WRONG EVIDENCE! HP -2")
            self.current_hp = max(0, self.current_hp - 2)
            
            # ตรวจสอบว่า HP หมดหรือยัง (<= 0)
            if self.current_hp <= 0:
                print("HP Depleted! Bad End -> Jump to 107")
                self.is_game_over = True     # เปิดสถานะ Game Over (Bad End)
                self.current_index = 107     # บังคับกระโดดไป 107 ทันที
            else:
                self.current_index = self.jump_on_wrong
            
        self.waiting_for_evidence = False
        self.update_dialogue_state()

    def draw_hp_bar(self, surface):
        max_slots = 5
        slot_width = 32
        slot_height = 16
        spacing = 6
        
        # คำนวณตำแหน่ง X ให้อยู่มุมขวาบน
        start_x = SCREEN_WIDTH - (max_slots * (slot_width + spacing)) - 30
        start_y = 25
        
        for i in range(max_slots):
            slot_x = start_x + i * (slot_width + spacing)
            slot_rect = pygame.Rect(slot_x, start_y, slot_width, slot_height)
            
            # วาดกรอบช่อง HP (ช่องที่ว่าง / เลือดลดแล้ว)
            pygame.draw.rect(surface, (20, 30, 50, 220), slot_rect, border_radius=3)
            pygame.draw.rect(surface, (90, 110, 140), slot_rect, 1, border_radius=3)
            
            # วาดสีฟ้าในช่อง ถ้า i น้อยกว่าค่า HP ปัจจุบัน (พิกัด HP ช่องละ 1 หน่วย รวม 5 ช่อง)
            if i < self.current_hp:
                fill_rect = slot_rect.inflate(-4, -4)
                pygame.draw.rect(surface, (50, 150, 255), fill_rect, border_radius=2) # สีฟ้าสด

    def on_dialogue_finish(self):
        self.ost.stop()
        
        if self.is_game_over:
            # ถ้าเป็น Bad End (107) จบลง ให้เริ่มเข้าสู่โหมดดีเลย์ 5 วินาทีรอแสดงปุ่ม
            self.waiting_game_over_delay = True
        else:
            # ถ้าเป็น Happy End จบลง (หรือหมดสคริปต์ปกติ) ให้กลับหน้า Menu ทันที
            print("Dialogue finished (Happy End). Returning to MenuScene...")
            from scenes.menu_scene import MenuScene
            self.app.change_scene(MenuScene(self.app))
        

    def handle_event(self, event):
        if self.show_menu_button and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.menu_button_rect.collidepoint(event.pos):
                from scenes.menu_scene import MenuScene
                self.app.change_scene(MenuScene(self.app))
                return
        if self.waiting_game_over_delay:
            return
        
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
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # คลิกซ้าย
            # ป้องกันไม่ให้คลิกซ้ายทำงานซ้อนทับถ้าเมาส์คลิกโดนพื้นที่นอก Textbox หรือขณะเมนูเปิดอยู่
            is_action_triggered = True

        if is_action_triggered:
            # ถ้าตัวหนังสือกำลังพิมพ์อยู่ ให้เร่งให้พิมพ์จบก่อน
            current_data = self.dialogue_list[self.current_index]
            if not self.textbox.is_finished:
                self.textbox.skip_to_end()
            else:
                # ถ้ากำลังรอหลักฐานอยู่ ให้สลับไปเปิดหน้าต่างหลักฐานแทนการเปลี่ยนบรรทัด
                if self.waiting_for_evidence:
                    if not self.evidence_menu.is_open:
                        self.evidence_menu.can_present = True
                        self.evidence_menu.toggle()
                elif "next_jump" in current_data:
                    self.current_index = current_data["next_jump"]
                # 3. เช็คว่าเป็นฉากจบ Happy End จริงๆ หรือไม่
                elif current_data.get("is_happy_end", False) and not self.is_game_over:
                    print("Happy End reached. Returning to MenuScene...")
                    from scenes.menu_scene import MenuScene
                    self.app.change_scene(MenuScene(self.app))
                    return
                else:
                    # ขยับไปประโยคถัดไปอย่างถูกต้อง
                    self.current_index += 1
                    # เช็คความปลอดภัยไม่ให้ index เกินจำนวนบทพูดที่มี
                    if self.current_index < len(self.dialogue_list):
                        self.update_dialogue_state()
                    else:
                        self.on_dialogue_finish()
                        
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from scenes.menu_scene import MenuScene
            self.app.change_scene(MenuScene(self.app))

    def update(self, dt_ms):
        self.textbox.update(dt_ms)
        for char_data in self.characters.values():
            char_data["animator"].update(dt_ms)

        if self.waiting_game_over_delay and not self.show_menu_button:
            self.game_over_timer += dt_ms
            if self.game_over_timer >= 2000:  # ครบ 5 วินาที (5000 ms)
                self.show_menu_button = True

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
        
        if self.render_textbox:
            self.textbox.draw(surface)
        self.draw_hp_bar(surface)
        self.evidence_menu.draw(surface, self.app.font_sm, self.app.font_md)

        if self.show_menu_button:
            # วาดเลเยอร์สีดำโปร่งแสงทับหน้าจอ
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))

            # วาดปุ่ม Return to Menu
            pygame.draw.rect(surface, (30, 40, 60), self.menu_button_rect, border_radius=8)
            pygame.draw.rect(surface, (50, 150, 255), self.menu_button_rect, 2, border_radius=8)
            
            btn_font = pygame.font.SysFont(None, 24)
            btn_text = btn_font.render("Return to Menu", True, (255, 255, 255))
            text_rect = btn_text.get_rect(center=self.menu_button_rect.center)
            surface.blit(btn_text, text_rect)