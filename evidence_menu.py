import os
import pygame
from config import *

class EvidenceMenu:
    def __init__(self, evidence_db):
        """
        evidence_db: รายการหลักฐาน
        """
        self.can_present = False
        self.evidence_db = evidence_db
        self.selected_index = 0
        self.is_open = False
        self.title_font = pygame.font.Font("assets/fonts/TorsilpThamnganMangThoe.ttf", 30) # ฟอนต์ชื่อใหญ่
        self.desc_font = pygame.font.Font("assets/fonts/TorsilpThamnganMangThoe.ttf", 24)  # ฟอนต์รายละเอียด

        # โหลด Asset พื้นหลัง UI หลัก (recordnew.png)
        self.bg_panel = None
        if os.path.exists("assets/images/recordnew.png"):
            img = pygame.image.load("assets/images/recordnew.png").convert_alpha()
            self.bg_panel = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))

    def toggle(self):
        self.is_open = not self.is_open
        self.selected_index = 0
        print(f"Evidence Menu is_open status: {self.is_open}")

    def handle_event(self, event):
        if not self.is_open:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                if self.evidence_db:
                    self.selected_index = (self.selected_index + 1) % len(self.evidence_db)
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                if self.evidence_db:
                    self.selected_index = (self.selected_index - 1) % len(self.evidence_db)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                if self.evidence_db and self.can_present:  # <--- ต้องได้รับอนุญาต (can_present = True) ถึงจะยื่นได้
                    chosen_item = self.evidence_db[self.selected_index]
                    self.is_open = False
                    return chosen_item["id"]
            elif event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE:
                self.is_open = False

        return None

    def draw(self, surface, title_font, font_md):
        if not self.is_open:
            return

        # 1. วาดภาพพื้นหลัง UI หลัก (recordu.png)
        if self.bg_panel:
            surface.blit(self.bg_panel, (0, 0))
        else:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 210))
            surface.blit(overlay, (0, 0))

        if not self.evidence_db:
            empty_surf = self.title_font.render("No Evidence Available", True, (200, 200, 200))
            surface.blit(empty_surf, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
            return

        # ดึงข้อมูลหลักฐานชิ้นที่กำลังเลือก
        current_item = self.evidence_db[self.selected_index]

        # 2. วาดกรอบพื้นหลัง "สีเทา" สำหรับรูปภาพหลักฐานชิ้นใหญ่
        img_box_rect = pygame.Rect(50, 140, 280, 320)
        pygame.draw.rect(surface, (211, 211, 211), img_box_rect)
        
        # วาดรูปภาพหลักฐานชิ้นใหญ่ตรงกลางกรอบสีเทา
        if os.path.exists(current_item.get("image", "")):
            item_img = pygame.image.load(current_item["image"]).convert_alpha()
            item_img = pygame.transform.scale(item_img, (210, 240))
            surface.blit(item_img, (img_box_rect.x + 30, img_box_rect.y + 30))

        # ==========================================
        # [จุดที่ปรับแก้ 1] ขยับชื่อหลักฐานไปทางขวาเพิ่มขึ้น (จาก 370 เป็น 410)
        # ==========================================
        name_surf = self.title_font.render(current_item.get("name", "Unknown"), True, (20, 20, 20))
        surface.blit(name_surf, (370, 140))

        # *(ลบโค้ดสร้างกล่องพื้นหลัง Description ออกตามที่ขอเรียบร้อย)*

        # ==========================================
        # [จุดที่ปรับแก้ 2] ขยับคำอธิบาย (Description) ไปทางขวาเพิ่มขึ้น (จาก 370 เป็น 410)
        # ==========================================
        desc_lines = current_item.get("desc_lines", [])
        line_y_positions = [270, 340, 415]
        
        for idx, line_text in enumerate(desc_lines):
            if idx < len(line_y_positions):
                line_surf = self.desc_font.render(line_text, True, (40, 40, 40))
                surface.blit(line_surf, (370, line_y_positions[idx]))

        # 3. วาดสล็อตไอเทมด้านล่าง (สีดำเทา / ฟ้าอ่อนตอนเลือก)
        slot_start_x = 75
        slot_y = 520
        slot_size = 90
        slot_gap = 18

        for i, item in enumerate(self.evidence_db):
            slot_x = slot_start_x + i * (slot_size + slot_gap)
            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
            
            if i == self.selected_index:
                # ช่องที่กำลังถูกเลือก: พื้นหลังสีฟ้าอ่อน + กรอบสีเหลือง
                pygame.draw.rect(surface, (100, 160, 220), slot_rect, border_radius=4)
                pygame.draw.rect(surface, (255, 220, 0), slot_rect, 4, border_radius=4)
            else:
                # ช่องปกติที่ไม่ได้เลือก: พื้นหลังสีดำเทาเข้ม
                pygame.draw.rect(surface, (45, 50, 60), slot_rect, border_radius=4)
                pygame.draw.rect(surface, (129, 133, 137), slot_rect, 2, border_radius=4)

            # วาดรูปไอคอนหลักฐานเล็กๆ ลงในสล็อต
            if os.path.exists(item.get("image", "")):
                icon_img = pygame.image.load(item["image"]).convert_alpha()
                icon_img = pygame.transform.scale(icon_img, (76, 76))
                surface.blit(icon_img, (slot_x + 7, slot_y + 7))

        # 4. ข้อความช่วยเหลือด้านล่าง
        if self.can_present:
            tip_text = "[A / D] เลือกหลักฐาน   |   [ENTER] ยื่นหลักฐาน   |   [TAB] ปิดหน้าต่าง"
        else:
            tip_text = "[A / D] เลือกหลักฐาน (โหมดดูข้อมูล)   |   [TAB] ปิดหน้าต่าง"
        tip_surf = self.desc_font.render(tip_text, True, (255, 255, 255))
        surface.blit(tip_surf, (75, 645))