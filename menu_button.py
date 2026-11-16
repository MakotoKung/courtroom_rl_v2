import pygame

def draw_slanted_background(surface):
        screen_width, screen_height = surface.get_size()
        
        # กำหนดจุดพิกัดสำหรับวาดแผงสีเทาแบบเฉียง (Slanted Panel)
        points = [
            (screen_width * 0.80, 0),       # จุดบนซ้าย (กำหนดความเอียงของขอบบน)
            (screen_width, 0),              # จุดบนขวา
            (screen_width, screen_height),  # จุดล่างขวา
            (800, screen_height)              # จุดล่างซ้าย (เต็มขอบจอฝั่งซ้าย)
        ]
        
        # วาดพื้นหลังสีเทาเข้ม
        pygame.draw.polygon(surface, (45, 48, 52), points)
        
        # วาดเส้นขอบเฉียงสีเทาอ่อนด้านซ้ายเพื่อให้ดูมีมิติคมชัดขึ้น
        border_start = (screen_width * 0.80, 0)
        border_end = (800, screen_height)
        pygame.draw.line(surface, (180, 180, 180), border_start, border_end, 3)

class MenuButton:
    def __init__(self, text, x, y, width, height, font, blue_img_path=None):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        
        # โหลดรูปภาพพื้นหลังปุ่มสีฟ้า
        self.bg_image = None
        if blue_img_path:
            try:
                raw_img = pygame.image.load(blue_img_path).convert_alpha()
                self.bg_image = pygame.transform.scale(raw_img, (width, height))
            except Exception:
                pass
                
        self.is_hovered = False

    def update(self, mouse_pos):
        # เช็คว่าเมาส์ชี้อยู่ที่ปุ่มนี้หรือไม่
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        # 1. วาดพื้นหลังปุ่ม (ถ้ามีรูปสีฟ้าให้ใช้รูป, ถ้าไม่มีให้วาดสี่เหลี่ยมสีฟ้าสำรอง)
        if self.bg_image:
            surface.blit(self.bg_image, self.rect.topleft)
            # ถ้าต้องการให้ตอนเอาเมาส์ชี้ (Hover) มีกรอบสว่างขึ้น หรือเอฟเฟกต์เพิ่มเติม ใส่ตรงนี้ได้
            if self.is_hovered:
                pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=4)
        else:
            # สีฟ้าสำรองกรณีไม่มีรูป
            bg_color = (70, 130, 180) if not self.is_hovered else (100, 160, 220)
            pygame.draw.rect(surface, bg_color, self.rect, border_radius=6)
            pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=6)

        # 2. วาดข้อความทับลงไปตรงกลางปุ่ม
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return True
        return False