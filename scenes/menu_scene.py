# scenes/menu_scene.py
import os
import pygame
from config import *
from ui import Button
from scenes.base_scene import BaseScene
from menu_button import MenuButton
from menu_button import draw_slanted_background

class MenuScene(BaseScene):
    def __init__(self, app):
        super().__init__(app)
        pygame.font.init()
        try:
            self.font = GLOBAL_FONT
        except Exception:
            self.font = pygame.font.SysFont(None, 26)

        self.bg_image = None
        bg_path = "assets/images/title/title_screen.png"
        if os.path.exists(bg_path):
            # โหลดภาพและปรับขนาดให้พอดีกับหน้าจอเกม (1280x720 ตาม config)
            raw_img = pygame.image.load(bg_path).convert()
            self.bg_image = pygame.transform.scale(raw_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.logo_image = pygame.image.load("assets/images/title/logo_trans.png").convert_alpha()
        self.logo_image = pygame.transform.scale(self.logo_image, (400, 200))  # ปรับขนาดโลโก้ให้เหมาะสม
        
        self.menu_items = ["Play", "AI Play","Q-Table", "Exit Game"]
        self.buttons = []
        self.selected_index = 0

        self.blue_btn_img = pygame.image.load("assets/images/name_bg.png").convert_alpha()
        self.blue_btn_img = pygame.transform.scale(self.blue_btn_img, (280, 40))  # ปรับขนาดให้พอดีกับปุ่ม
        start_x = 940 
        start_y = 310   # ปรับระยะสูงต่ำของกลุ่มปุ่มได้ตรงนี้
        spacing = 100   # ระยะห่างในแนวตั้งระหว่างแต่ละปุ่ม (ป้องกันปุ่มทับกัน)
        btn_width = 300
        btn_height = 46

        for i, text in enumerate(self.menu_items):
            btn = MenuButton(
                text=text,
                x=start_x,
                y=start_y + (i * spacing),  # ตัวแปร i จะช่วยดันพิกัด Y ลงมาทีละแถว
                width=btn_width,
                height=btn_height,
                font=self.font,
                blue_img_path="assets/images/name_bg.png"
            )
            self.buttons.append(btn)
        
        
        
        
        '''
        self.btn_mode1 = Button(
            (SCREEN_WIDTH // 2 - 260, 320, 520, 65),
            "โหมด 1: เล่นเอง (รับบททนายแตน vs อัยการสุ่ม Action)",
            BLUE_LAWYER
        )
        self.btn_mode2 = Button(
            (SCREEN_WIDTH // 2 - 260, 405, 520, 65),
            "โหมด 2: AI เล่นอัตโนมัติ (โหลด Q-table Model)",
            PURPLE_PROSECUTOR
        )
        '''
    def handle_event(self, event):
        
        for i, btn in enumerate(self.buttons):
            if btn.is_clicked(event):
                selected_text = self.menu_items[i]
                print(f"Selected: {selected_text}")
                
                # [ADDED]: กำหนดเงื่อนไขการทำงานเมื่อคลิกแต่ละปุ่ม
                if selected_text == "Exit Game":
                    pygame.quit()
                    exit()
                elif selected_text == "Play":
                    print("เปลี่ยนไปหน้าเลือกบท/เล่นเกม...")
                    from scenes.exidence_scene import exidence
                    self.app.change_scene(exidence(self.app))
                    # สมมติเปลี่ยน Scene: self.app.change_scene(GameScene(self.app))
                elif selected_text == "AI Play":
                    print("เปลี่ยนไปหน้า AI เล่นเกม...")
                    from scenes.ai_judge_scene import judge_ai
                    self.app.change_scene(judge_ai(self.app))
                elif selected_text == "Q-Table":
                    from scenes.qtable_scene import QTableScene
                    self.app.change_scene(QTableScene(self.app))
        '''
        if self.btn_mode1.handle_event(event):
            from scenes.exidence_scene import exidence
            self.app.change_scene(exidence(self.app))
        elif self.btn_mode2.handle_event(event):
            from scenes.courtroom_scene import CourtroomScene
            self.app.change_scene(CourtroomScene(self.app, mode=2))
        '''
    def update(self, dt_ms):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update(mouse_pos)
    def draw(self, surface):

        if self.bg_image:
            surface.blit(self.bg_image,(0,0))
        else:
            surface.fill(DARK_BG)

        draw_slanted_background(surface)
        for btn in self.buttons:
            btn.draw(surface)

        #sub = self.app.font_md.render("เลือกโหมดการเล่น (Pygame + Q-Learning JSON Model)", True, WHITE)
        #surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 240)))
        if self.logo_image:
            surface.blit(self.logo_image, (880, 50))

        '''
        self.btn_mode1.draw(surface, self.app.font_md, self.app.font_sm)
        self.btn_mode2.draw(surface, self.app.font_md, self.app.font_sm)
        '''

