# scenes/menu_scene.py
import os
import pygame
from config import *
from ui import Button
from scenes.base_scene import BaseScene

class MenuScene(BaseScene):
    def __init__(self, app):
        super().__init__(app)

        self.bg_image = None
        bg_path = "assets/images/title_back.png"
        if os.path.exists(bg_path):
            # โหลดภาพและปรับขนาดให้พอดีกับหน้าจอเกม (1280x720 ตาม config)
            raw_img = pygame.image.load(bg_path).convert()
            self.bg_image = pygame.transform.scale(raw_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
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

    def handle_event(self, event):
        if self.btn_mode1.handle_event(event):
            from scenes.exidence_scene import exidence
            self.app.change_scene(exidence(self.app))
        elif self.btn_mode2.handle_event(event):
            from scenes.courtroom_scene import CourtroomScene
            self.app.change_scene(CourtroomScene(self.app, mode=2))

    def draw(self, surface):

        if self.bg_image:
            surface.blit(self.bg_image,(0,0))
        else:
            surface.fill(DARK_BG)

        sub = self.app.font_md.render("เลือกโหมดการเล่น (Pygame + Q-Learning JSON Model)", True, WHITE)
        surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 240)))
        self.btn_mode1.draw(surface, self.app.font_md, self.app.font_sm)
        self.btn_mode2.draw(surface, self.app.font_md, self.app.font_sm)
        

