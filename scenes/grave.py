import os
import pygame
from config import *
from ui import Button
from scenes.base_scene import BaseScene

class GavelAnimator:
    """คลาสจัดการตัดเฟรมแบบกำหนดขนาดเอง, มีระบบปรับ Gap ระหว่างเฟรม, ลบ Green Screen และ Scale"""
    def __init__(self, image_path, total_frames=6, frame_w=256, frame_h=191, gap=0, scale_factor=1.0):
        self.frames = []
        self.frame_index = 0
        self.timer = 0
        self.frame_duration = 100   # ความเร็วแต่ละเฟรม (ms)
        self.is_finished = False
        
        if not os.path.exists(image_path):
            print(f"Error: ไม่พบไฟล์ภาพ {image_path}")
            return

        # 1. โหลดภาพ Sprite Sheet
        sheet = pygame.image.load(image_path).convert()
        sheet_w = sheet.get_width()
        sheet_h = sheet.get_height()
        
        # 2. ลูปตัดภาพ (Crop) โดยใช้ขนาดเฟรมที่กำหนด และเผื่อระยะห่าง (Gap)
        for i in range(total_frames):
            # คำนวณตำแหน่ง X โดยบวก Gap เข้าไปในแต่ละเฟรมถัดไป
            x = i * (frame_w + gap)
            y = 0  # แถวแรกสุด
            
            # ป้องกันกรณีตัดเกินขอบเขตภาพ
            if x + frame_w > sheet_w:
                print(f"Warning: เฟรมที่ {i} เกินขอบเขตความกว้างของ Sprite Sheet!")
                break
            
            # สร้าง Surface แบบมี Alpha รองรับความโปร่งใส
            frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), (x, y, frame_w, frame_h))
            
            # ทำการกวาดพิกเซลสีเขียวให้โปร่งใส
            frame = self.remove_green_screen(frame, tolerance=80)
            
            # 3. ขยายขนาด (Scale) ถ้าต้องการให้ภาพใหญ่ขึ้น
            if scale_factor != 1.0:
                new_w = int(frame_w * scale_factor)
                new_h = int(frame_h * scale_factor)
                frame = pygame.transform.smoothscale(frame, (new_w, new_h))
                
            self.frames.append(frame)

    def remove_green_screen(self, surface, tolerance=70):
        """ฟังก์ชันแปลงพิกเซลสีเขียวให้โปร่งใส"""
        w, h = surface.get_size()
        new_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        
        for y in range(h):
            for x in range(w):
                color = surface.get_at((x, y))
                r, g, b, a = color
                
                # เช็คโทนสีเขียว
                if g > tolerance and g > r + 30 and g > b + 30:
                    new_surface.set_at((x, y), (0, 0, 0, 0))
                else:
                    new_surface.set_at((x, y), color)
                    
        return new_surface

    def update(self, dt_ms):
        if self.is_finished or not self.frames:
            return
            
        self.timer += dt_ms
        if self.timer >= self.frame_duration:
            self.timer = 0
            self.frame_index += 1
            
            if self.frame_index >= len(self.frames):
                self.frame_index = len(self.frames) - 1
                self.is_finished = True

    def draw(self, surface, x, y):
        if self.frames:
            current_frame = self.frames[self.frame_index]
            surface.blit(current_frame, (x, y))


class GavelScene(BaseScene):
    def __init__(self, app):
        super().__init__(app)
        
        # ใส่ Path รูปภาพ Sprite Sheet ของคุณตรงนี้
        gavel_path = "assets/images/hammer/gavel.png"  
        
        # กำหนดค่าพารามิเตอร์ต่างๆ ตรงนี้:
        # - frame_w=256, frame_h=191 ตามต้องการ
        # - gap: ถ้ามีเส้นแบ่งหรือขอบเกิน ให้ปรับเพิ่ม/ลดค่านี้ เช่น 1, 2, 4 เพื่อ Optimize การตัดภาพ
        # - scale_factor: ปรับขนาดความใหญ่ของภาพบนจอ
        frame_w=256 
        frame_h=191
        scale_factor = min(SCREEN_WIDTH / frame_w, SCREEN_HEIGHT / frame_h)
        self.gavel_anim = GavelAnimator(
            image_path=gavel_path, 
            total_frames=6,  
            gap=24,               # <--- ปรับจูนค่า Gap ตรงนี้ (ถ้าเฟรมเหลื่อมหรือติดขอบข้างๆ)
            scale_factor=scale_factor     # <--- ปรับขนาดความใหญ่ตามต้องการ
        )
        
        # จัดตำแหน่งให้อยู่กึ่งกลางจออัตโนมัติ
        if self.gavel_anim.frames:
            frame_w, frame_h = self.gavel_anim.frames[0].get_size()
            self.pos_x = (SCREEN_WIDTH - frame_w) // 2
            self.pos_y = (SCREEN_HEIGHT - frame_h) // 2
        else:
            self.pos_x, self.pos_y = 100, 100

        # ปุ่มย้อนกลับ
        self.btn_back = Button(
            rect=(30, 80, 140, 40),
            text="ย้อนกลับ",
            color=PANEL_BG
        )

    def on_enter(self):
        self.gavel_anim.frame_index = 0
        self.gavel_anim.timer = 0
        self.gavel_anim.is_finished = False

    def handle_event(self, event):
        if self.btn_back.handle_event(event):
            from scenes.menu_scene import MenuScene
            self.app.change_scene(MenuScene(self.app))
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from scenes.menu_scene import MenuScene
                self.app.change_scene(MenuScene(self.app))

        

    def update(self, dt_ms):
        self.gavel_anim.update(dt_ms)
        if self.gavel_anim.timer >= 1000: 
                    from scenes.judge_scene import judge
                    self.app.change_scene(judge(self.app))

    def draw(self, surface):
        surface.fill(DARK_BG)  
        
        # วาดแอนิเมชันกลางจอ
        self.gavel_anim.draw(surface, self.pos_x, self.pos_y)
        if self.gavel_anim.is_finished: 
            from scenes.judge_scene import judge
            self.app.change_scene(judge(self.app))

        if hasattr(self, 'btn_back') and self.btn_back:
            self.btn_back.draw(surface, self.app.font_sm, self.app.font_sm)