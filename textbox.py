import pygame
from config import GLOBAL_FONT

class Textbox:
    def __init__(self, x, y, width, height, font, bg_color=(20, 20, 30, 220), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.bg_color = bg_color
        self.text_color = text_color
        self.font = GLOBAL_FONT

        
        self.speaker_name = ""
        self.full_text = ""          # ข้อความทั้งหมด
        self.displayed_text = ""     # ข้อความที่กำลังแสดงทีละตัว
        
        # ควบคุมเอฟเฟกต์พิมพ์ทีละตัวอักษร
        self.char_index = 0
        self.timer = 0
        self.char_speed = 30         # ความเร็วในการพิมพ์ (มิลลิวินาทีต่อ 1 ตัวอักษร ยิ่งน้อยยิ่งพิมพ์เร็ว)
        self.is_finished = False     # เช็คว่าพิมพ์จบประโยคหรือยัง

    def set_text(self, speaker, text):
        """ตั้งค่าชื่อผู้พูดและข้อความใหม่ พร้อมรีเซ็ตเอฟเฟกต์พิมพ์"""
        self.speaker_name = speaker
        self.full_text = text
        self.displayed_text = ""
        self.char_index = 0
        self.timer = 0
        self.is_finished = False

    def update(self, dt_ms):
        """อัปเดตให้ตัวหนังสือค่อยๆ เด้งขึ้นมาทีละตัว"""
        if self.is_finished:
            return

        self.timer += dt_ms
        if self.timer >= self.char_speed:
            self.timer = 0
            if self.char_index < len(self.full_text):
                self.displayed_text += self.full_text[self.char_index]
                self.char_index += 1
            else:
                self.is_finished = True

    def skip_to_end(self):
        """ฟังก์ชันสำหรับกดข้ามเพื่อให้แสดงข้อความทั้งหมดทันที"""
        self.displayed_text = self.full_text
        self.char_index = len(self.full_text)
        self.is_finished = True

    def draw(self, surface):
        # สร้าง Surface โปร่งใสสำหรับกล่องข้อความ
        box_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # วาดพื้นหลังและขอบกล่อง
        pygame.draw.rect(box_surface, self.bg_color, (0, 0, self.rect.width, self.rect.height), border_radius=12)
        pygame.draw.rect(box_surface, (200, 200, 200), (0, 0, self.rect.width, self.rect.height), 2, border_radius=12)
        
        # วาดชื่อผู้พูด
        if self.speaker_name:
            name_surface = self.font.render(self.speaker_name, True, (255, 220, 100))
            box_surface.blit(name_surface, (20, -30))
            
        # วาดข้อความที่กำลังพิมพ์
        text_surface = self.font.render(self.displayed_text, True, self.text_color)
        box_surface.blit(text_surface, (25, 25))
        
        # แปะลงบนหน้าจอหลัก
        surface.blit(box_surface, (self.rect.x, self.rect.y))