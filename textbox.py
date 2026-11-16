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
        self.speed = 20  # ความเร็วในการพิมพ์ (มิลลิวินาทีต่อตัวอักษร)
        self.is_finished = True

        #name_bg
        self.name_bg_image = None
        self.name_bg_image = pygame.image.load("assets/images/name_bg.png").convert_alpha()
        self.tab_btn_img = None
        self.tab_btn_img = pygame.image.load("assets/images/tab.png").convert_alpha()
        self.space_btn_img = None
        self.space_btn_img = pygame.image.load("assets/images/space.png").convert_alpha()

        try:
            self.typing_sound = pygame.mixer.Sound("assets/sounds/se003 (Message Display) (Male).wav")
        except Exception:
            self.typing_sound = None

        self.is_playing_sound = False
        self.typing_sound.set_volume(0.05)

    def set_text(self, speaker, text):
        self.speaker = speaker
        self.text = text
        self.displayed_text = ""
        self.char_index = 0
        self.timer = 0
        self.is_finished = False

        if self.typing_sound and not self.is_playing_sound:
            self.typing_sound.play(loops=-1)
            self.is_playing_sound = True

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

        if self.is_playing_sound and self.is_finished:
            self.typing_sound.stop()
            self.is_playing_sound = False

    def skip_to_end(self):
        self.displayed_text = self.text
        self.is_finished = True

        if self.is_playing_sound:
            self.typing_sound.stop()
            self.is_playing_sound = False

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
            name_h = 35
            name_rect = pygame.Rect(self.x + 30, self.y - 25, name_w, name_h) #Position name
            # y- มากยิ่งลอย
            # x+ มากไปขวา
            # วาดพื้นหลังกรอบชื่อผู้พูดสีฟ้า + ขอบขอบฟ้าอ่อน
            if self.name_bg_image:
                scaled_name_bg = pygame.transform.scale(self.name_bg_image, (name_rect.width, name_rect.height))
                surface.blit(scaled_name_bg, (name_rect.x, name_rect.y))
            else:
            # ระบบสำรอง (ถ้าไม่ใส่รูป ให้ใช้วาดสี่เหลี่ยมสีเดิม)
                pygame.draw.rect(surface, (30, 100, 180), name_rect, border_radius=6)     
                pygame.draw.rect(surface, (100, 180, 255), name_rect, 2, border_radius=6)
            surface.blit(name_surf, (name_rect.x + 25, name_rect.y + 10)) #ปรับตำแหน่งตัวหนังสือให้ตรงกลางกรอบชื่อผู้พูด

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
        hint_font = pygame.font.SysFont(None, 18)
        
        # ข้อความต่อท้ายรูปปุ่ม
        lbl_next = hint_font.render(": Next", True, (220, 220, 220))
        lbl_evidence = hint_font.render(": Evidence", True, (220, 220, 220))
        
        # กำหนดขนาดที่จะแสดงผลของรูปปุ่ม (ปรับความกว้างสูงได้ตามความเหมาะสมกับรูปจริง)
        btn_w, btn_h = 60, 24 
        
        # คำนวณตำแหน่งเริ่มจากขวาสุดของ Textbox วิ่งย้อนมาทางซ้าย
        right_margin = self.x + self.width - 15
        y_pos = self.y + self.height - btn_h - 12
        
        # --- วาดปุ่ม TAB (อยู่ขวาสุด) ---
        # 1. ตำแหน่งข้อความ ": Evidence"
        w_ev = lbl_evidence.get_width()
        x_ev_text = right_margin - w_ev
        
        # 2. ตำแหน่งรูปปุ่ม Tab (อยู่หน้าข้อความ ": Evidence")
        x_tab_img = x_ev_text - btn_w - 5
        
        # --- วาดปุ่ม SPACE (อยู่ถัดมาทางซ้ายของ Tab) ---
        # 1. ตำแหน่งข้อความ ": Next"
        w_next = lbl_next.get_width()
        x_next_text = x_tab_img - w_next - 15
        
        # 2. ตำแหน่งรูปปุ่ม Space (อยู่หน้าข้อความ ": Next")
        x_space_img = x_next_text - btn_w - 5

        # --- ทำการ Blit (แปะภาพและตัวหนังสือลงจอ) ---
        # วาดปุ่ม SPACE
        if self.space_btn_img:
            scaled_space = pygame.transform.scale(self.space_btn_img, (btn_w, btn_h))
            surface.blit(scaled_space, (x_space_img, y_pos))
        surface.blit(lbl_next, (x_next_text, y_pos +6))

        # วาดปุ่ม TAB
        if self.tab_btn_img:
            scaled_tab = pygame.transform.scale(self.tab_btn_img, (btn_w, btn_h))
            surface.blit(scaled_tab, (x_tab_img, y_pos))
        surface.blit(lbl_evidence, (x_ev_text, y_pos +6))
        '''
        badge1 = pygame.Rect(x1, y1, w1, h1)
        if self.space_bg_image:
            scaled_space_bg = pygame.transform.scale(self.space_bg_image, (badge1.width, badge1.height))
            surface.blit(scaled_space_bg, (badge1.x, badge1.y))
        else:
            pygame.draw.rect(surface, (25, 45, 80), badge1, border_radius=4)
            pygame.draw.rect(surface, (70, 130, 200), badge1, 1, border_radius=4)
        surface.blit(h_text1, (x1 + pad_x, y1 + pad_y))
        
        # วาด Badge ปุ่ม Tab
        badge2 = pygame.Rect(x2, y2, w2, h2)
        if self.tab_bg_image:
            scaled_tab_bg = pygame.transform.scale(self.tab_bg_image, (badge2.width, badge2.height))
            surface.blit(scaled_tab_bg, (badge2.x, badge2.y))
        else:
            pygame.draw.rect(surface, (25, 45, 80), badge2, border_radius=4)
            pygame.draw.rect(surface, (70, 130, 200), badge2, 1, border_radius=4)
        surface.blit(h_text2, (x2 + pad_x, y2 + pad_y))
        '''