# animation.py
import os
import random
import pygame
from config import *

class SpriteSheet:
    def __init__(self, image_path):
        self.sheet = None
        if image_path and os.path.exists(image_path):
            self.sheet = pygame.image.load(image_path).convert_alpha()

    def get_image(self, x, y, width, height):
        """ตัดภาพ (Crop) ตามพิกัด X, Y และขนาด Width, Height"""
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        if self.sheet:
            image.blit(self.sheet, (0, 0), (x, y, width, height))
        return image


class Character:
    """Object ตัวละครที่โหลด Sprite Sheet แบบ Palette และรัน Animation จนถึงเฟรมสุดท้ายได้"""
    def __init__(self, name, sheet_path, anim_config, fallback_color=(100, 100, 150)):
        self.name = name
        self.fallback_color = fallback_color
        self.spritesheet = SpriteSheet(sheet_path)
        self.animations = {}
        self.has_sprites = False

        if self.spritesheet.sheet and anim_config:
            self.load_animations(anim_config)

        self.current_anim = "idle"
        self.frame_index = 0
        self.timer = 0
        self.frame_duration = 120
        self.is_looping = True
        self.is_finished = False

    def load_animations(self, config):
        for anim_name, frames in config.items():
            anim_frames = []
            for f in frames:
                img = self.spritesheet.get_image(f["x"], f["y"], f["w"], f["h"])
                if "scale" in f:
                    img = pygame.transform.scale(img, tuple(f["scale"]))
                anim_frames.append(img)
            if anim_frames:
                self.animations[anim_name] = anim_frames
                self.has_sprites = True

    def set_animation(self, name, loop=True, force_restart=False):
        """สั่งเปลี่ยนท่าทาง (Animation) พร้อมเลือกว่าจะวนลูปหรือหยุดที่เฟรมสุดท้าย"""
        if name not in self.animations:
            return
        if self.current_anim != name or force_restart:
            self.current_anim = name
            self.frame_index = 0
            self.timer = 0
            self.is_looping = loop
            self.is_finished = False

    def update(self, dt_ms):
        if not self.has_sprites or self.is_finished:
            return
        frames = self.animations.get(self.current_anim, [])
        if not frames:
            return

        self.timer += dt_ms
        if self.timer >= self.frame_duration:
            self.timer = 0
            self.frame_index += 1
            if self.frame_index >= len(frames):
                if self.is_looping:
                    self.frame_index = 0
                else:
                    self.frame_index = len(frames) - 1
                    self.is_finished = True

    def draw(self, surface, x, y, extra_offset_x=0):
        if self.has_sprites and self.current_anim in self.animations:
            frames = self.animations[self.current_anim]
            img = frames[min(self.frame_index, len(frames) - 1)]
            surface.blit(img, (x + extra_offset_x, y))
        else:
            # Fallback Placeholder กรณีที่ยังไม่ได้วางไฟล์ Sprite Sheet จริง
            rect = pygame.Rect(x + extra_offset_x, y, 120, 175)
            pygame.draw.rect(surface, self.fallback_color, rect, border_radius=12)
            pygame.draw.rect(surface, WHITE, rect, 2, border_radius=12)
            font = pygame.font.SysFont(None, 22)
            lbl = font.render(f"{self.name} ({self.current_anim})", True, WHITE)
            surface.blit(lbl, (rect.x + 8, rect.y + 75))


class AnimationManager:
    """จัดการ Effects หน้าจอ, กล่องข้อความ Typewriter, หลอด HP และคลัง Character Objects"""
    def __init__(self, char_configs=None):
        self.characters = {}
        fallback_colors = {
            "judge": GOLD_JUDGE,
            "prosecutor": PURPLE_PROSECUTOR,
            "lawyer": BLUE_LAWYER,
            "defendant": (90, 150, 140),
            "witness": (180, 120, 75),
        }

        if char_configs:
            for char_id, cfg in char_configs.items():
                if isinstance(cfg, dict):
                    sheet_path = cfg.get("sheet_path", "")
                    anims = cfg.get("animations", {})
                else:
                    sheet_path = str(cfg)
                    anims = {}
                self.characters[char_id] = Character(
                    name=char_id,
                    sheet_path=sheet_path,
                    anim_config=anims,
                    fallback_color=fallback_colors.get(char_id, GRAY)
                )

        self.display_hp = 5.0
        self.lag_hp = 5.0
        self.full_text = ""
        self.visible_chars = 0
        self.text_timer = 0

        self.shake_timer = 0
        self.shake_intensity = 0
        self.flash_timer = 0
        self.flash_color = WHITE

    def get_character(self, char_id):
        return self.characters.get(char_id)

    def set_character_anim(self, char_id, anim_name, loop=True, force_restart=False):
        char = self.characters.get(char_id)
        if char:
            char.set_animation(anim_name, loop=loop, force_restart=force_restart)

    def set_dialogue(self, text):
        self.full_text = text
        self.visible_chars = 0
        self.text_timer = 0

    def is_dialogue_done(self):
        return self.visible_chars >= len(self.full_text)

    def skip_dialogue(self):
        self.visible_chars = len(self.full_text)

    def trigger_shake(self, intensity=8, duration_ms=300):
        self.shake_intensity = intensity
        self.shake_timer = duration_ms

    def trigger_flash(self, color=WHITE, duration_ms=200):
        self.flash_color = color
        self.flash_timer = duration_ms

    def get_shake_offset(self):
        if self.shake_timer > 0:
            return (
                random.randint(-self.shake_intensity, self.shake_intensity),
                random.randint(-self.shake_intensity, self.shake_intensity),
            )
        return (0, 0)

    def update(self, dt_ms, target_hp):
        for char in self.characters.values():
            char.update(dt_ms)

        self.display_hp += (target_hp - self.display_hp) * min(1.0, dt_ms * 0.015)
        if self.lag_hp > self.display_hp:
            self.lag_hp = max(self.display_hp, self.lag_hp - dt_ms * 0.003)
        else:
            self.lag_hp = self.display_hp

        if self.visible_chars < len(self.full_text):
            self.text_timer += dt_ms
            if self.text_timer >= 22:
                self.visible_chars += max(1, self.text_timer // 22)
                self.text_timer %= 22

        if self.shake_timer > 0:
            self.shake_timer = max(0, self.shake_timer - dt_ms)
        if self.flash_timer > 0:
            self.flash_timer = max(0, self.flash_timer - dt_ms)

    def draw_character(self, surface, char_id, x, y, tick_ms=0, extra_param=0):
        char = self.characters.get(char_id)
        offset_x = int(extra_param) if char_id == "defendant" else 0
        if char:
            char.draw(surface, x, y, extra_offset_x=offset_x)

    def draw_hp_bar(self, surface, x, y, w, h, max_hp=5):
        pygame.draw.rect(surface, (45, 48, 60), (x, y, w, h), border_radius=6)
        lag_w = int(w * max(0.0, min(1.0, self.lag_hp / max_hp)))
        cur_w = int(w * max(0.0, min(1.0, self.display_hp / max_hp)))
        if lag_w > 0:
            pygame.draw.rect(surface, YELLOW_WARN, (x, y, lag_w, h), border_radius=6)
        if cur_w > 0:
            col = GREEN_SUCCESS if self.display_hp > 2.0 else RED_DANGER
            pygame.draw.rect(surface, col, (x, y, cur_w, h), border_radius=6)
        pygame.draw.rect(surface, WHITE, (x, y, w, h), 2, border_radius=6)
