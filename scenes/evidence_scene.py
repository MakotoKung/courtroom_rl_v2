# scenes/my_new_scene.py
import os
import pygame
from config import *
from ui import Button
from scenes.base_scene import BaseScene
from characteranimation import CharacterAnimator

class evidence(BaseScene):
    def __init__(self, app):
        super().__init__(app)  # เชื่อมต่อกับหลัก (เข้าถึง self.app.data, sound, font_*, ฯลฯ)
        
        # 1. โหลดรูปภาพพื้นหลังหรือทรัพยากรเฉพาะของฉากนี้
        self.current_image = None
        bg_path = "assets/images/hammer/bg008.png"  # เปลี่ยน path รูปตามต้องการ
        if os.path.exists(bg_path):
            img = pygame.image.load(bg_path).convert()
            self.current_image = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))

        if os.path.exists("assets/images/hammer/bg009.png"):
            self.ving = pygame.image.load("assets/images/hammer/bg009.png").convert_alpha()
            self.ving = pygame.transform.scale(self.ving, (SCREEN_WIDTH, SCREEN_HEIGHT))

        if os.path.exists("assets/images/hammer/spr500.png"):
            self.hammer = pygame.image.load("assets/images/hammer/spr500.png").convert_alpha()
            self.hammer = pygame.transform.scale(self.hammer, (SCREEN_WIDTH, SCREEN_HEIGHT))
              
        '''
        self.larry = CharacterAnimator(char_name="Larry")
        self.larry.add_action("crying","assets/images/larry/larry_cry2.png",
                              total_frames=5, duration=150,custom_width=102
                              )
        self.larry.set_scale(1.8)
        self.larry.play_ani("crying", loop=True)
        '''
        #สร้างปุ่ม
        self.btn_back = Button(
            rect=(30, 80, 140, 40),
            text="ย้อนกลับ",
            color=PANEL_BG
        )

        # 3. กำหนดตัวแปรและสถานะต่างๆ ของฉาก
        self.timer = 0

    def on_enter(self):
        """ทำงานอัตโนมัติทันทีที่สลับเข้ามาในฉากนี้ (ใช้รีเซ็ตค่าต่างๆ)"""
        self.timer = 0
        self.is_finish = False

    def on_exit(self):
        """ทำงานอัตโนมัติก่อนเปลี่ยนไปฉากอื่น (ใช้เคลียร์ค่า)"""
        pass

    def handle_event(self, event):
        """จัดการ Event (เมาส์ / คีย์บอร์ด) เฉพาะของฉากนี้"""
        # ตัวอย่าง: กดปุ่มย้อนกลับไปเมนูหลัก

        if self.is_finish: 
            from scens.judge_scene import judge
            self.app.change_scene(judge(self.app))

        if self.btn_back.handle_event(event):
            from scenes.menu_scene import MenuScene
            self.app.change_scene(MenuScene(self.app))
            return

        # ตัวอย่าง: รับปุ่มคีย์บอร์ด
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from scenes.menu_scene import MenuScene
                self.app.change_scene(MenuScene(self.app))
            elif event.key == pygame.K_SPACE:
                from scenes.judge_scene import judge
                self.app.change_scene(judge(self.app))
                return

    

        

    def update(self, dt_ms):
        """อัปเดตลอจิกและแอนิเมชันในแต่ละเฟรม (dt_ms = มิลลิวินาที)"""
        # ตัวอย่างการนับเวลา
        self.timer += dt_ms
        #self.larry.update(dt_ms)
        

    def draw(self, surface):
        """วาดองค์ประกอบทุกอย่างลงบนหน้าจอ surface"""
        
        if self.current_image:
            surface.blit(self.current_image,(0,0))
            surface.blit(self.ving,  (0,0))
            surface.blit(self.hammer, (400,300))
            self.is_finish = True
            
        else: 
            surface.fill(DARK_BG)
        
        
        # 2. วาดข้อความหรือ UI บนจอ
        #txt = self.app.font_md.render(f"Timer: {self.timer} ms", True, WHITE)
        #surface.blit(txt, (50, 150))
        # 3. วาดปุ่ม UI
        self.btn_back.draw(surface, self.app.font_sm, self.app.font_sm)

