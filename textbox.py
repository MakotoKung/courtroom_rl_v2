import pygame
from config import *

class Textbox:
    def __init__(self, x, y, width, height, font):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = GLOBAL_FONT
        
        self.speaker = ""
        self.text = ""
        self.displayed_text = ""
        self.char_index = 0
        
        # ตัวควบคุม Typewriter Effect
        self.timer = 0
        self.speed = 30  # ความเร็วในการพิมพ์ (มิลลิวินาทีต่อตัวอักษร)
        self.is_finished = True

    def set_text(self, speaker, text):
        self.speaker = speaker
        self.text = text
        self.displayed_text = ""
        self.char_index = 0
        self.timer = 0
        self.is_finished = False

    def update(self, dt_ms):
        """ระบบ Typewriter แบบ while loop ป้องกันอาการสะดุดเมื่อเฟรมตก"""
        if not self.is_finished:
            self.timer += dt_ms
            while self.timer >= self.speed and not self.is_finished:
                self.timer -= self.speed
                self.char_index += 1
                if self.char_index <= len(self.text):
                    self.displayed_text = self.text[:self.char_index]
                else:
                    self.is_finished = True
                    break

    def skip_to_end(self):
        self.displayed_text = self.text
        self.is_finished = True

    def draw(self, surface):
        # 1. วาดกรอบหลักของ Textbox
        box_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, (15, 20, 35, 230), box_rect, border_radius=8)       # พื้นหลังมืดโปร่งแสง
        pygame.draw.rect(surface, (70, 130, 180), box_rect, 2, border_radius=8)    # ขอบกล่องสีฟ้าเหล็ก (Steel Blue)

        # 2. วาดกรอบชื่อผู้พูดและชื่อผู้พูด (โทนสีฟ้า)
        if self.speaker:
            name_font = pygame.font.SysFont(None, 24)
            name_surf = name_font.render(self.speaker, True, (255, 255, 255)) # ตัวหนังสือขาว
            
            # คำนวณขนาดกรอบชื่อผู้พูด
            name_w = name_surf.get_width() + 50
            name_h = 30
            name_rect = pygame.Rect(self.x + 28, self.y - 32, name_w, name_h) #Position name
            
            # วาดพื้นหลังกรอบชื่อผู้พูดสีฟ้า + ขอบขอบฟ้าอ่อน
            pygame.draw.rect(surface, (30, 100, 180), name_rect, border_radius=6)     # พื้นหลังสีฟ้า
            pygame.draw.rect(surface, (100, 180, 255), name_rect, 2, border_radius=6) # ขอบสีฟ้าสว่าง
            surface.blit(name_surf, (name_rect.x + 12, name_rect.y + 5))

        # 3. วาดข้อความบทพูด
        text_surf = self.font.render(self.displayed_text, True, (255, 255, 255))
        surface.blit(text_surf, (self.x + 25, self.y + 25))

        # 4. วาดปุ่มคำสั่งควบคุมที่มุมขวาล่างของ Textbox (สไตล์ Badge ตามเรฟ)
        hint_font = pygame.font.SysFont(None, 18)
        
        h_text1 = hint_font.render("SPACE : Next", True, (220, 220, 220))
        h_text2 = hint_font.render("TAB : Evidence", True, (220, 220, 220))
        
        pad_x, pad_y = 10, 6
        
        w2 = h_text2.get_width() + pad_x * 2
        h2 = h_text2.get_height() + pad_y * 2
        x2 = self.x + self.width - w2 - 15
        y2 = self.y + self.height - h2 - 12
        
        w1 = h_text1.get_width() + pad_x * 2
        h1 = h_text1.get_height() + pad_y * 2
        x1 = x2 - w1 - 10
        y1 = y2
        
        # วาด Badge ปุ่ม Space
        badge1 = pygame.Rect(x1, y1, w1, h1)
        pygame.draw.rect(surface, (25, 45, 80), badge1, border_radius=4)
        pygame.draw.rect(surface, (70, 130, 200), badge1, 1, border_radius=4)
        surface.blit(h_text1, (x1 + pad_x, y1 + pad_y))
        
        # วาด Badge ปุ่ม Tab
        badge2 = pygame.Rect(x2, y2, w2, h2)
        pygame.draw.rect(surface, (25, 45, 80), badge2, border_radius=4)
        pygame.draw.rect(surface, (70, 130, 200), badge2, 1, border_radius=4)
        surface.blit(h_text2, (x2 + pad_x, y2 + pad_y))