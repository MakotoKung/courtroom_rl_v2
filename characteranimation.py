import os
import pygame

class CharacterAnimator:
    def __init__(self, char_name=""):
        self.char_name = char_name  
        self.actions = {}
        
        self.current_action = None
        self.frames = []
        self.frame_index = 0
        self.timer = 0
        self.frame_duration = 100  
        self.is_loop = True
        self.is_finished = False

    def add_action(self, action_name, image_path, total_frames, duration=100, custom_width=None, custom_height=None):
        """
        เพิ่ม action พร้อมรองรับการกำหนดขนาด frame_width และ frame_height เองได้
        - custom_width: กำหนดความกว้างของแต่ละเฟรมเอง (ถ้าไม่ใส่จะหารอัตโนมัติ)
        - custom_height: กำหนดความสูงของแต่ละเฟรมเอง (ถ้าไม่ใส่จะใช้ความสูงเต็มภาพ)
        """
        if not os.path.exists(image_path):
            print(f"Error [{self.char_name}]: ไม่พบไฟล์ภาพที่ path -> {image_path}")
            return

        sheet = pygame.image.load(image_path).convert_alpha()
        sheet_w = sheet.get_width()
        sheet_h = sheet.get_height()
        
        # ถ้าระบุขนาดมาเอง ให้ใช้ค่านั้น ถ้าไม่ระบุให้คำนวณจากความกว้างรวม
        frame_w = custom_width if custom_width is not None else (sheet_w // total_frames)
        frame_h = custom_height if custom_height is not None else sheet_h
        
        # ตัดภาพแยกเป็นเฟรม (Crop)
        frame_list = []
        for i in range(total_frames):
            x = i * frame_w
            y = 0  # ถ้าภาพ Sprite Sheet เรียงแถวเดียว ใช้ y = 0
            
            # ป้องกันกรณีคำนวณเกินขอบเขตภาพ
            if x + frame_w > sheet_w:
                print(f"Warning [{self.char_name}]: เฟรมที่ {i} เกินขอบเขตความกว้างของภาพ!")
            
            frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), (x, y, frame_w, frame_h))
            frame_list.append(frame)
            
        # บันทึกเก็บไว้ใน Dictionary ตามชื่อ Action
        self.actions[action_name] = {
            "frames": frame_list,
            "duration": duration
        }

    def play_ani(self, action_name, loop=True):
        """สั่งเล่นแอนิเมชันของ Action นั้นๆ"""
        if action_name not in self.actions:
            print(f"Error [{self.char_name}]: ไม่พบ Action ชื่อ '{action_name}'")
            return

        if self.current_action != action_name:
            self.current_action = action_name
            self.is_loop = loop
            
            data = self.actions[action_name]
            self.frames = data["frames"]
            self.frame_duration = data["duration"]
            
            self.frame_index = 0
            self.timer = 0
            self.is_finished = False

    def set_scale(self, scale_factor):
        """
        ปรับขยายขนาดเฟรมทั้งหมดตามสัดส่วน (Scale)
        เช่น scale_factor = 0.5 (ย่อเหลือ 50%), 2.0 (ขยาย 2 เท่า)
        """
        for action_name in self.actions:
            scaled_frames = []
            for frame in self.actions[action_name]["frames"]:
                w = int(frame.get_width() * scale_factor)
                h = int(frame.get_height() * scale_factor)
                # ใช้ smoothscale เพื่อให้ภาพย่อ/ขยายแล้วยังเนียนสวย
                scaled_frame = pygame.transform.scale(frame, (w, h))
                scaled_frames.append(scaled_frame)
            
            # อัปเดตเฟรมที่ย่อแล้วกลับเข้าไป
            self.actions[action_name]["frames"] = scaled_frames
        
        # ถ้ากำลังเล่น Action ไหนอยู่ ให้รีเฟรชเฟรมปัจจุบันด้วย
        if self.current_action in self.actions:
            self.frames = self.actions[self.current_action]["frames"]

    def update(self, dt_ms):
        """อัปเดตเฟรมแอนิเมชัน"""
        if not self.frames or self.is_finished:
            return
            
        self.timer += dt_ms
        if self.timer >= self.frame_duration:
            self.timer = 0
            self.frame_index += 1
            
            if self.frame_index >= len(self.frames):
                if self.is_loop:
                    self.frame_index = 0  
                else:
                    self.frame_index = len(self.frames) - 1  
                    self.is_finished = True

    def draw(self, surface, x, y):
        """วาดตัวละครลงบนหน้าจอ"""
        if self.frames and self.current_action:
            current_frame = self.frames[self.frame_index]
            surface.blit(current_frame, (x, y))

    def draw_name_tag(self, surface, font, x, y, bg_color=(30, 30, 50), text_color=(255, 255, 255)):
        """วาดป้ายชื่อตัวละคร"""
        if not self.char_name:
            return
            
        name_surface = font.render(self.char_name, True, text_color)
        padding_x, padding_y = 15, 8
        box_width = name_surface.get_width() + (padding_x * 2)
        box_height = name_surface.get_height() + (padding_y * 2)
        
        box_rect = pygame.Rect(x, y, box_width, box_height)
        pygame.draw.rect(surface, bg_color, box_rect, border_radius=6)
        pygame.draw.rect(surface, (200, 200, 200), box_rect, 2, border_radius=6) 
        
        surface.blit(name_surface, (x + padding_x, y + padding_y))