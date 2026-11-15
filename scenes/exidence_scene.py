# scenes/new_scene.py
import os
import pygame
from config import *
from ui import Button
from scenes.base_scene import BaseScene


class exidence(BaseScene):
    def __init__(self, app):
        super().__init__(app)  # เชื่อมต่อกับ AceAttorneyApp (เข้าถึง self.app.data, sound, anim, font_* ได้)[cite: 5, 13]
        
        # 1. โหลดรูปภาพเฉพาะของฉากนี้ (ถ้ามี)
        self.scene_image = None
        image_path = "assets/images/cutscene/bg021b.png"
        if os.path.exists(image_path):
            scene = pygame.image.load(image_path).convert()
            self.scene_image = pygame.transform.scale(scene, (SCREEN_WIDTH,SCREEN_HEIGHT))

        # 1.2 load bg021a
        self.bg021a = None
        path021a = "assets/images/cutscene/bg021a.png"
        if os.path.exists(path021a):
            i021a = pygame.image.load(path021a).convert()
            self.bg021a = pygame.transform.scale(i021a,(SCREEN_WIDTH,SCREEN_HEIGHT))

        # 2.1 load bg022
        self.bg022 = None
        path022 = "assets/images/cutscene/bg022.png"
        if os.path.exists(path022):
            i022 = pygame.image.load(path022).convert()
            self.bg022 = pygame.transform.scale(i022,(SCREEN_WIDTH,SCREEN_HEIGHT))
        
        self.fade_alpha = 0               # ค่าความโปร่งใส (0 ถึง 255)
        self.fade_speed = 0.4             # ความเร็วในการเฟด (ปรับค่ามากยิ่งเฟดไว)
        self.fade_state = "IDLE"          # สถานะ: "IDLE" (ปกติ), "FADE_OUT" (กำลังมืดลง), "FADE_IN" (กำลังสว่างขึ้น)
        self.active_image = self.bg021a

        # 2.2 load blood effect
        # 2.2 load blood effect
        effect_sheet_path = "assets/images/cutscene/spr000.png"
        if os.path.exists(effect_sheet_path):
            effect_raw = pygame.image.load(effect_sheet_path).convert_alpha()
        else:
            effect_raw = pygame.Surface((300, 300), pygame.SRCALPHA)

        self.effect_cols = 3
        self.effect_rows = 3
        sheet_w = effect_raw.get_width()
        sheet_h = effect_raw.get_height()
        
        self.effect_frame_w = sheet_w // self.effect_cols
        self.effect_frame_h = sheet_h // self.effect_rows

        # ---> [กำหนดสัดส่วนการย่อขนาดตรงนี้] เช่น 0.5 คือลดขนาดลงเหลือ 50% (ครึ่งนึง) <---
        scale_factor = 0.61  # ปรับตัวเลขนี้ได้ตามใจชอบ (เช่น 0.6 ใหญ่ขึ้น, 0.4 เล็กลง)
        
        target_w = int(self.effect_frame_w * scale_factor)
        target_h = int(self.effect_frame_h * scale_factor)

        # ตัดภาพแยกเป็นเฟรม และทำการย่อขนาด (Scale) ทันที
        self.effect_frames = []
        for r in range(self.effect_rows):
            for c in range(self.effect_cols):
                if len(self.effect_frames) >= 8:  
                    break
                x = c * self.effect_frame_w
                y = r * self.effect_frame_h
                
                # ตัดภาพเฟรมเดิม
                frame = pygame.Surface((self.effect_frame_w, self.effect_frame_h), pygame.SRCALPHA)
                frame.blit(effect_raw, (0, 0), (x, y, self.effect_frame_w, self.effect_frame_h))
                
                # ---> ย่อขนาดเฟรมภาพให้เล็กลงตามสัดส่วนที่ตั้งไว้ <---
                scaled_frame = pygame.transform.smoothscale(frame, (target_w, target_h))
                self.effect_frames.append(scaled_frame)

        # อัปเดตตัวแปรขนาดเฟรมใหม่ให้ตรงกับขนาดที่ย่อแล้ว เพื่อให้คำนวณตำแหน่งจัดวางตรงกลางได้ถูกต้อง
        self.effect_frame_w = target_w
        self.effect_frame_h = target_h

        # ตัวแปรควบคุมแอนิเมชันเอฟเฟกต์
        self.effect_frame_index = 0
        self.effect_timer = 0
        self.effect_duration = 100      
        self.effect_is_finished = False  
        
        # ตำแหน่งแสดงผลตรงกลางจอ
        self.effect_pos_x = SCREEN_WIDTH // 2 - self.effect_frame_w // 2
        self.effect_pos_y = SCREEN_HEIGHT // 2 - self.effect_frame_h // 2

        #load bg002
        bg02_sheet_path = "assets/images/cutscene/bg002.png"
        if os.path.exists(effect_sheet_path):
            self.bg02 = pygame.image.load(bg02_sheet_path).convert_alpha()
        # ตัวแปรสำหรับหน่วงเวลาก่อนเปลี่ยน Scene (หน่วยเป็นมิลลิวินาที)
        self.scene_delay_timer = 0
        self.scene_target_delay = 1500   # กำหนดเวลาหน่วงตรงนี้ (เช่น 1500 ms = 1.5 วินาที)
        self.is_ready_to_change_scene = False 
        
        self.phase1 = False
        self.phase2 = False
        # 2. สร้างปุ่มกด (UI) ของฉากนี้[cite: 6]
        self.btn_action = Button(
            rect=(SCREEN_WIDTH // 2 - 150, 350, 300, 55),
            text="ปุ่มดำเนินการ",
            color=BLUE_LAWYER,
            subtext="คำอธิบายย่อย (ลบออกได้)"
        )
        self.btn_back = Button(
            rect=(30, 80, 140, 40),
            text="ย้อนกลับ",
            color=PANEL_BG
        )

        # 3. กำหนดตัวแปร State ของฉากนี้
        # self.message = "พร้อมทำงานใน Scene ใหม่"
        sheet_path = "assets/images/cutscene/spr001.png"
        self.sheet_image = pygame.image.load(sheet_path).convert_alpha()

        self.frames = []
        self.frame_width = 110
        self.frame_height = self.sheet_image.get_height()
        total_frames = 11    # สมมติว่ามี 3 เฟรมเรียงกันในแนวนอน
        
        for i in range(total_frames):
            x = i * self.frame_width -40
            frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
            frame.blit(self.sheet_image, (0, 0), (x, 0, self.frame_width, self.frame_height))
            self.frames.append(frame)

        # 3. ตัวแปรสำหรับควบคุมการเล่นแอนิเมชันใน update()
        self.frame_index = 0
        self.timer = 0
        self.frame_duration = 110

        self.pos_x = (SCREEN_WIDTH // 2 - self.frame_width // 2) - 30
        self.pos_y = (SCREEN_HEIGHT // 2 - self.frame_height // 2) - 340

    def start_fade_transition(self, target_image):
        """เรียกใช้เมื่อต้องการ Fade ไปยังภาพเป้าหมายใหม่"""
        self.fade_target_image = target_image  # เก็บภาพเป้าหมายที่จะเปลี่ยนไป
        self.fade_state = "FADE_OUT"
        self.fade_alpha = 0

    def fade_to_new_scene(self, target_scene_class):
        """
        เรียกใช้ฟังก์ชันนี้เพื่อสั่ง Fade จอมืดลง แล้วสลับไป Scene ใหม่
        ตัวอย่างการใช้งาน: self.fade_to_new_scene(MenuScene(self.app))
        """
        self.next_scene_to_load = target_scene_class  # เก็บ Scene ปลายทาง
        self.fade_state = "FADE_OUT"                  # เริ่มต้นกระบวนการ Fade ออก (มืดลง)
        self.fade_alpha = 0 

    def on_enter(self):
        """ทำงานอัตโนมัติทันทีที่สลับเข้ามาฉากนี้[cite: 5, 13]"""
        # ตัวอย่าง: เล่นเสียง หรือตั้งค่าท่าทางตัวละครเริ่มต้น
        # self.app.sound.play("gavel")
        # self.app.anim.set_character_anim("lawyer", "idle", loop=True)
        self.frame_index = 0
        self.timer = 0
        self.delay_timer = 0
        self.target_delay = 2000  # หน่วงเวลา 2000 มิลลิวินาที (2 วินาที)
        self.is_switched = False  # เช็คว่าเปลี่ยนภาพหรือยัง
        
        self.is_waiting = True        # สถานะกำลังรอดีเลย์
        self.is_sliding = False       # สถานะกำลังเลื่อนขึ้น
        self.slide_progress = 0.0
        self.slide_duration = 1000     # ใช้เวลาเลื่อนขึ้น 0.6 วินาที
        self.y_offset = 0             # ระยะพิกัด Y ที่จะขยับขึ้น

        #for phase1 spr000  
        self.effect_frame_index = 0
        self.effect_timer = 0
        self.effect_is_finished = False
    def on_exit(self):
        """ทำงานอัตโนมัติก่อนเปลี่ยนไปฉากอื่น (ใช้เคลียร์ค่าต่างๆ)[cite: 5, 13]"""
        pass

    def handle_event(self, event):
        """จัดการ Event (เมาส์ / คีย์บอร์ด) เฉพาะของฉากนี้[cite: 5, 13]"""
        # กดปุ่มย้อนกลับไปเมนูหลัก
        if self.btn_back.handle_event(event):
            from scenes.menu_scene import MenuScene
            self.app.change_scene(MenuScene(self.app))
            return

        # กดปุ่มดำเนินการ
        if self.btn_action.handle_event(event):
            self.app.sound.play("ding")
            self.message = "กดปุ่มเรียบร้อย!"

        # ตัวอย่างการรับปุ่มคีย์บอร์ด
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from scenes.menu_scene import MenuScene
                self.app.change_scene(MenuScene(self.app))
            elif event.type == pygame.MOUSEBUTTONDOWN:
            # ถ้าข้อความยังพิมพ์ไม่จบ ให้กดคลิกเพื่อข้ามข้อความให้แสดงผลเต็มทันที[cite: 8]
                if not self.app.anim.is_dialogue_done():
                    self.app.anim.skip_dialogue()
                else:
                    self.finish_cutscene()

    def update(self, dt_ms):
        """อัปเดตลอจิกและแอนิเมชันในแต่ละเฟรม (dt_ms = มิลลิวินาที)[cite: 5, 13]"""
        # หากในฉากนี้มีการแสดงตัวละครหรือข้อความ Typewriter ให้เปิดบรรทัดนี้:
        # self.app.anim.update(dt_ms, target_hp=5.0)
        # สะสมเวลาที่ผ่านไปในแต่ละเฟรม (dt_ms ได้มาจาก clock.tick() ใน main.py)

        self.timer += dt_ms
        if self.timer >= self.frame_duration:
            self.timer = 0
            self.frame_index += 1
            
            # เช็คว่าวิ่งมาถึงเฟรมสุดท้ายหรือยัง (Index 9 คือเฟรมที่ 10)
            if self.frame_index >= len(self.frames):
                self.frame_index = 0 # ล็อกไว้ที่เฟรมสุดท้าย

        if self.is_waiting:
            self.delay_timer += dt_ms
            if self.delay_timer >= self.target_delay:
                self.is_waiting = False
                self.is_switched = True
                self.is_sliding = True  # หมดเวลาดีเลย์ เริ่มสั่งเลื่อนขึ้นทันที!

        # เฟสที่ 2: กำลังเลื่อนภาพขึ้น
        elif self.is_sliding:
            self.slide_progress += dt_ms / self.slide_duration
            
            if self.slide_progress >= 1.0:
                self.slide_progress = 1.0
                self.is_sliding = False
                self.scene_image = self.bg021a  # เลื่อนเสร็จ สลับเป็นภาพใหม่ถาวร
                self.y_offset = 0
                self.start_fade_transition(self.bg022)
            else:
                # คำนวณตำแหน่ง Y ให้ค่อยๆ เลื่อนขึ้นไปข้างบน (-SCREEN_HEIGHT)
                self.y_offset = -SCREEN_HEIGHT * self.slide_progress
        
        if self.fade_state == "FADE_OUT":
            self.fade_alpha += self.fade_speed * dt_ms
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                
                # ถ้ามีการกำหนด Scene ปลายทางไว้ เปลี่ยน Scene ทันทีตอนจอมืดสนิท
                if hasattr(self, 'next_scene_to_load') and self.next_scene_to_load:
                    self.app.change_scene(self.next_scene_to_load)
                    return
                
                # ถ้าไม่ใช่การเปลี่ยน Scene ให้เปลี่ยนภาพพื้นหลังปกติ
                if hasattr(self, 'fade_target_image') and self.fade_target_image:
                    self.scene_image = self.fade_target_image
                    self.active_image = self.fade_target_image
                    
                self.fade_state = "FADE_IN"       # ค่อยๆ สว่างขึ้น

        elif self.fade_state == "FADE_IN":
            self.fade_alpha -= self.fade_speed * dt_ms
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fade_state = "IDLE"   

        #effect spr00
        if self.fade_state == "IDLE" and self.scene_image == self.bg022:
            if not self.effect_is_finished and len(self.effect_frames) > 0:
                self.effect_timer += dt_ms
                if self.effect_timer >= self.effect_duration:
                    self.effect_timer = 0
                    self.effect_frame_index += 1
                    
                    # ถ้าวิ่งมาถึงเฟรมสุดท้าย ให้ล็อกไว้ที่เฟรมสุดท้าย
                    if self.effect_frame_index >= len(self.effect_frames):
                        self.effect_frame_index = len(self.effect_frames) - 1
                        self.effect_is_finished = True

        # หน่วงเวลาก่อนเปลี่ยน Scene หลังจากเอฟเฟกต์ spr000 เล่นจบ
        if self.fade_state == "IDLE" and self.scene_image == self.bg022 and self.effect_is_finished:
            if not self.is_ready_to_change_scene:
                self.scene_delay_timer += dt_ms
                
                # ถ้านับเวลาครบกำหนด (เช่น 1500 ms) ค่อยสั่ง Fade เปลี่ยน Scene
                if self.scene_delay_timer >= self.scene_target_delay:
                    self.is_ready_to_change_scene = True
                    from scenes.grave import GavelScene  # เปลี่ยนชื่อ Scene ปลายทางตามที่คุณใช้งาน
                    self.fade_to_new_scene(GavelScene(self.app))

    def draw(self, surface):
        """วาดทุกอย่างของฉากนี้ลงบน surface (หมายเหตุ: Header Bar ด้านบนถูกวาดให้อัตโนมัติจาก main.py แล้ว)[cite: 5, 13]"""
        # 1. วาดพื้นหลัง (ถ้ามีรูป)
        if self.scene_image:
            surface.blit(self.scene_image, (0, 0))
            if not self.is_switched:
                current_frame = self.frames[self.frame_index]
                surface.blit(current_frame, (self.pos_x, self.pos_y+(self.frame_index* 75)))
            
            if self.is_sliding:
                # ขณะกำลังเลื่อน: วาดภาพเก่าขยับขึ้นข้างบน และวาดภาพใหม่ตามขึ้นมาจากด้านล่าง
                surface.blit(self.scene_image, (0, self.y_offset))
                surface.blit(self.bg021a, (0, self.y_offset + SCREEN_HEIGHT))
                # [ลบออก] surface.blit(self.active_image, (0, 0)) <- บรรทัดนี้ทำให้ภาพซ้อนทับผิดปกติ
                self.phase1 = True

        # ถ้าเข้าสู่ phase1 (หลังเลื่อนภาพเสร็จ และเริ่มเข้าสู่กระบวนการ Fade / แสดงเอฟเฟกต์)
        if self.phase1:
            if self.fade_alpha > 0:
                if self.fade_alpha >= 128:
                    self.active_image = self.bg022
                elif self.fade_alpha >= 255: 
                    self.phase2 = True
            
            surface.blit(self.active_image, (0, 0))

            # สร้างเลเยอร์เงาดำทับเพื่อทำเอฟเฟกต์ Fade
            if self.fade_alpha > 0:
                fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                fade_surface.fill((0, 0, 0))                    
                fade_surface.set_alpha(int(min(255, self.fade_alpha)))    
                surface.blit(fade_surface, (0, 0))
            
            # ---> [ย้ายมาไว้ตรงนี้] วาดเอฟเฟกต์ spr000 เฉพาะตอนที่ Fade เสร็จเรียบร้อยแล้ว (IDLE) <---
            if self.fade_state == "IDLE" and self.scene_image == self.bg022:
                if len(self.effect_frames) > 0:
                    current_effect_frame = self.effect_frames[self.effect_frame_index]
                    surface.blit(current_effect_frame, (self.effect_pos_x+110, self.effect_pos_y+30))

                    

        # 3. วาดตัวละคร (ถ้าต้องการโชว์ Sprite ในฉากนี้)[cite: 8]
        # self.app.anim.draw_character(surface, "lawyer", x=565, y=280)

        # 4. วาดปุ่มกด[cite: 6]

