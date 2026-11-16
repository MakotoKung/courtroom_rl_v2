# main.py
import os
import sys
import json
import pygame

from config import *
from ui import Button
from sound import SoundManager
from animation import AnimationManager
from train_model import train_and_export
from scenes.menu_scene import MenuScene


class AceAttorneyApp:
    """Scene Manager หลักสำหรับสลับฉากและจัดการทรัพยากรกลางของเกม"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("อัยการปีศาจดา vs ทนายแตน — Courtroom RL")
        self.clock = pygame.time.Clock()

        # โหลดฟอนต์ภาษาไทย
        self.font_lg = self._load_thai_font(28, bold=True)
        self.font_md = self._load_thai_font(20, bold=False)
        self.font_sm = self._load_thai_font(15, bold=False)

        # โหลดเนื้อหาเกมจาก JSON
        with open("game_data.json", "r", encoding="utf-8") as f:
            self.data = json.load(f)

        # โหลดหรือสร้างโมเดล Q-table JSON อัตโนมัติ (อิงชื่อไฟล์ตาม main_2.py ล่าสุด)
        model_path = "model_q_table.json"
        if not os.path.exists(model_path):
            train_and_export(episodes=15000, output_file=model_path)

        with open(model_path, "r", encoding="utf-8") as f:
            model_json = json.load(f)
        self.q_prosecutor = model_json.get("prosecutor_q_table", {})
        self.q_lawyer = model_json.get("lawyer_q_table", {})

        # ระบบ Sound & Sprite Animation Manager กลาง (ใช้ร่วมกันทุก Scene)
        self.sound = SoundManager(self.data.get("assets", {}).get("sounds"))
        self.anim = AnimationManager(self.data.get("assets", {}).get("characters"))

        # ปุ่ม Global Header (ใช้ได้ทุก Scene)
        self.btn_sound = Button((1020, 15, 115, 36), "เสียง: เปิด", PANEL_BG)
        self.btn_menu = Button((1145, 15, 115, 36), "เมนูหลัก", PANEL_BG)

        # เริ่มต้นที่ฉาก MenuScene
        self.current_scene = None
        self.change_scene(MenuScene(self))

    def _load_thai_font(self, size, bold=False):
        candidates = ["Tahoma", "Leelawadee UI", "Angsana New", "Thonburi", "Garuda", "DejaVu Sans"]
        for name in candidates:
            path = pygame.font.match_font(name, bold=bold)
            if path:
                return pygame.font.Font(path, size)
        return pygame.font.SysFont(None, size, bold=bold)

    def change_scene(self, new_scene):
        """ฟังก์ชันสลับฉาก (Scene Transition)"""
        
        if self.current_scene:
            self.current_scene.on_exit()
        self.current_scene = new_scene
        if self.current_scene:
            self.current_scene.on_enter()

    def run(self):
        while True:
            dt_ms = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.btn_sound.handle_event(event):
                    self.sound.toggle()
                if self.btn_menu.handle_event(event):
                    self.change_scene(MenuScene(self))

                if self.current_scene:
                    self.current_scene.handle_event(event)

            if self.current_scene:
                self.current_scene.update(dt_ms)

            # วาดลง Canvas กลาง
            canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            canvas.fill(DARK_BG)

            # Header Bar กลาง
            header_txt = self.font_lg.render(self.data.get("case_title", "Courtroom RL"), True, GOLD_JUDGE)
            canvas.blit(header_txt, (30, 18))
            self.btn_sound.text = "เสียง: เปิด" if self.sound.enabled else "เสียง: ปิด"
            self.btn_sound.draw(canvas, self.font_sm, self.font_sm)
            self.btn_menu.draw(canvas, self.font_sm, self.font_sm)

            # วาดเนื้อหาของ Scene ปัจจุบัน
            if self.current_scene:
                self.current_scene.draw(canvas)

            # Flash Effect กลาง
            if self.anim.flash_timer > 0:
                fl = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                fl.fill((*self.anim.flash_color, 90))
                canvas.blit(fl, (0, 0))

            # Screen Shake Offset กลาง
            shake_x, shake_y = self.anim.get_shake_offset()
            self.screen.fill(BLACK)
            self.screen.blit(canvas, (shake_x, shake_y))
            pygame.display.flip()


if __name__ == "__main__":
    app = AceAttorneyApp()
    app.run()
