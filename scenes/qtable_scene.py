# scenes/qtable_scene.py
# หน้าแสดง Q-table ทั้งหมดจาก model_q_table.json (เลื่อนได้)
#   เมาส์วีล / ↑ ↓ / PageUp PageDown / ลาก scrollbar | T = ฝึกโมเดลใหม่ | R = โหลดใหม่ | ESC = กลับเมนู
import os
import json
import pygame
from config import *
from ui import Button
from scenes.base_scene import BaseScene

MODEL_PATH = "Model/model_q_table.json"
MODEL_DIRS = [".", "models","Model"]   # โฟลเดอร์ที่ค้นหาไฟล์ Q-table (*.json ที่มี key "q_table")
EVIDENCE_PATH = "evidence.json"
FONT_PATH = "assets/fonts/TorsilpThamnganMangThoe.ttf"

# เลย์เอาต์ (จอ 1280x720, แถบหัวของ main.py อยู่ y 0-60)
LEFT = 40
LABEL_W = 270
COL_W = 150
HEAD_Y, HEAD_H = 140, 58
ROWS_Y = HEAD_Y + HEAD_H + 6
ROWS_BOTTOM = 700
ROW_H = 42
SB_X, SB_W = 1240, 10

COL_BAD = (150, 55, 62)
COL_MID = (172, 150, 58)
COL_GOOD = (46, 140, 92)
GOLD = (255, 215, 70)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def heat(t):
    t = max(0.0, min(1.0, t))
    return _lerp(COL_BAD, COL_MID, t * 2) if t < 0.5 else _lerp(COL_MID, COL_GOOD, (t - 0.5) * 2)


def fit(font, text, max_w):
    if font.size(text)[0] <= max_w:
        return text
    while text and font.size(text + "…")[0] > max_w:
        text = text[:-1]
    return text + "…"


class QTableScene(BaseScene):
    def __init__(self, app):
        super().__init__(app)
        self.f_title = pygame.font.Font(FONT_PATH, 34)
        self.f_md = pygame.font.Font(FONT_PATH, 22)
        self.f_sm = pygame.font.Font(FONT_PATH, 18)
        self.f_xs = pygame.font.Font(FONT_PATH, 15)

        self.btn_back = Button((30, 66, 130, 34), "ย้อนกลับ", PANEL_BG)
        self.scroll = 0
        self.dragging = False
        self.drag_off = 0
        self.dd_open = False
        self.dd_rect = pygame.Rect(640, 66, 600, 34)
        self.files = []
        self.cur = MODEL_PATH
        self.scan()
        self.load()

    # ---------- file list ----------
    def scan(self):
        found = []
        for d in MODEL_DIRS:
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if not fn.lower().endswith(".json"):
                    continue
                p = os.path.normpath(os.path.join(d, fn))
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "q_table" in data:
                            found.append(p)
                except Exception:
                    pass
        self.files = found
        if self.files and self.cur not in self.files:
            self.cur = self.files[0]

    def _item_rect(self, i):
        return pygame.Rect(self.dd_rect.x, self.dd_rect.bottom + 2 + i * 32, self.dd_rect.w, 30)

    def _select(self, p):
        self.cur = p
        self.dd_open = False
        self.load()

    # ---------- data ----------
    def load(self):
        self.meta, self.rows, self.cols, self.error = {}, [], [], ""
        self.names = {}
        if os.path.exists(EVIDENCE_PATH):
            with open(EVIDENCE_PATH, "r", encoding="utf-8") as f:
                self.names = {e["id"]: e.get("name", e["id"]) for e in json.load(f)}
        if not os.path.exists(self.cur):
            self.error = f"ไม่พบ {self.cur}  กด T เพื่อฝึกโมเดล"
            return
        with open(self.cur, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.meta = data.get("meta", {})
        q = data.get("q_table", {})
        if not q:
            self.error = "Q-table ว่าง  กด T เพื่อฝึกโมเดล"
            return
        ids = list(self.names.keys()) or list(next(iter(q.values())).keys())
        self.cols = [i for i in ids if any(i in v for v in q.values())]

        states = sorted(q.keys(), key=lambda k: (int(k.split("|")[0]), -int(k.split("|")[1])))
        cps = sorted({int(k.split("|")[0]) for k in states})
        vals = [v for s in q.values() for v in s.values()]
        self.vmin, self.vmax = min(vals), max(vals)
        for k in states:
            idx, hp = (int(x) for x in k.split("|"))
            qs = q[k]
            best = max(self.cols, key=lambda c: qs.get(c, float("-inf")))
            self.rows.append({"idx": idx, "hp": hp, "cp": cps.index(idx) + 1, "q": qs, "best": best})
        self.scroll = 0

    def train_now(self):
        from train_model import train_and_export
        train_and_export(output_file=self.cur)
        self.scan()
        self.load()

    # ---------- scroll ----------
    @property
    def view_h(self):
        return ROWS_BOTTOM - ROWS_Y

    @property
    def max_scroll(self):
        return max(0, len(self.rows) * ROW_H - self.view_h)

    def _clamp(self):
        self.scroll = max(0, min(self.max_scroll, self.scroll))

    def _thumb(self):
        total = len(self.rows) * ROW_H
        h = max(36, int(self.view_h * self.view_h / total))
        y = ROWS_Y + int((self.view_h - h) * (self.scroll / self.max_scroll)) if self.max_scroll else ROWS_Y
        return pygame.Rect(SB_X, y, SB_W, h)

    # ---------- events ----------
    def handle_event(self, event):
        # dropdown ได้สิทธิ์ก่อน
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.dd_rect.collidepoint(event.pos):
                self.dd_open = not self.dd_open
                if self.dd_open:
                    self.scan()
                return
            if self.dd_open:
                for i, p in enumerate(self.files):
                    if self._item_rect(i).collidepoint(event.pos):
                        self._select(p)
                        return
                self.dd_open = False
                return
        if self.dd_open and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.dd_open = False
            return
        if self.btn_back.handle_event(event):
            self._back()
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._back()
            elif event.key == pygame.K_t:
                self.train_now()
            elif event.key == pygame.K_r:
                self.scan()
                self.load()
            elif event.key == pygame.K_DOWN:
                self.scroll += ROW_H
            elif event.key == pygame.K_UP:
                self.scroll -= ROW_H
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll += self.view_h
            elif event.key == pygame.K_PAGEUP:
                self.scroll -= self.view_h
            elif event.key == pygame.K_HOME:
                self.scroll = 0
            elif event.key == pygame.K_END:
                self.scroll = self.max_scroll
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * ROW_H
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.max_scroll:
            th = self._thumb()
            if th.inflate(14, 0).collidepoint(event.pos):
                self.dragging, self.drag_off = True, event.pos[1] - th.y
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging and self.max_scroll:
            th = self._thumb()
            span = self.view_h - th.h
            self.scroll = int((event.pos[1] - self.drag_off - ROWS_Y) / span * self.max_scroll)
        self._clamp()

    def _back(self):
        from scenes.menu_scene import MenuScene
        self.app.change_scene(MenuScene(self.app))

    # ---------- draw ----------
    def _hp_pips(self, surface, x, y, hp):
        for i in range(5):
            r = pygame.Rect(x + i * 13, y, 10, 16)
            pygame.draw.rect(surface, (20, 30, 50), r, border_radius=2)
            pygame.draw.rect(surface, (90, 110, 140), r, 1, border_radius=2)
            if i < hp:
                pygame.draw.rect(surface, (50, 150, 255), r.inflate(-4, -4), border_radius=1)

    def draw(self, surface):
        surface.fill(DARK_BG)
        self.btn_back.draw(surface, self.f_sm, self.f_sm)
        surface.blit(self.f_title.render("Q-Table ที่โมเดลเรียนรู้", True, GOLD_JUDGE), (180, 60))

        self._draw_dropdown_button(surface)
        if self.error:
            msg = self.f_md.render(self.error, True, (230, 200, 120))
            surface.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
            self._draw_dropdown_list(surface)
            return

        # สรุป meta
        m = self.meta
        parts = [f"states {len(self.rows)}", f"actions {len(self.cols)}"]
        if "episodes" in m: parts.append(f"episodes {m['episodes']:,}")
        if "alpha" in m: parts.append(f"α {m['alpha']}")
        if "gamma" in m: parts.append(f"γ {m['gamma']}")
        if "win_rate" in m: parts.append(f"ชนะ {m['win_rate']:.0%}")
        if "mistakes_per_game" in m: parts.append(f"ผิด/เกม {m['mistakes_per_game']:.2f}")
        surface.blit(self.f_sm.render("   |   ".join(parts), True, (170, 180, 200)), (LEFT, 108))

        # หัวตาราง (ตรึงไว้ ไม่เลื่อน)
        pygame.draw.rect(surface, (38, 44, 62), (LEFT, HEAD_Y, LABEL_W + COL_W * len(self.cols), HEAD_H), border_radius=8)
        surface.blit(self.f_sm.render("จุดตรวจ / HP", True, (200, 210, 230)), (LEFT + 16, HEAD_Y + 18))
        for j, c in enumerate(self.cols):
            x = LEFT + LABEL_W + j * COL_W
            t1 = self.f_md.render(f"E{j + 1}", True, GOLD_JUDGE)
            surface.blit(t1, (x + COL_W // 2 - t1.get_width() // 2, HEAD_Y + 4))
            nm = fit(self.f_xs, self.names.get(c, c), COL_W - 10)
            t2 = self.f_xs.render(nm, True, (200, 210, 230))
            surface.blit(t2, (x + COL_W // 2 - t2.get_width() // 2, HEAD_Y + 33))

        # แถวข้อมูล (ตัดขอบด้วย clip เพื่อให้เลื่อนได้)
        mouse = pygame.mouse.get_pos()
        area = pygame.Rect(LEFT, ROWS_Y, LABEL_W + COL_W * len(self.cols), self.view_h)
        surface.set_clip(area)
        span = (self.vmax - self.vmin) or 1.0
        prev_cp = None
        for i, r in enumerate(self.rows):
            y = ROWS_Y + i * ROW_H - self.scroll
            if y + ROW_H < ROWS_Y or y > ROWS_BOTTOM:
                continue
            row_rect = pygame.Rect(LEFT, y, area.w, ROW_H - 4)
            hovered = row_rect.collidepoint(mouse) and area.collidepoint(mouse)
            pygame.draw.rect(surface, (44, 50, 70) if hovered else PANEL_BG, row_rect, border_radius=6)
            if r["cp"] != prev_cp:  # แถบสีน้ำเงินบอกจุดตรวจใหม่
                pygame.draw.rect(surface, (50, 150, 255), (LEFT, y, 4, ROW_H - 4), border_radius=2)
            prev_cp = r["cp"]

            surface.blit(self.f_sm.render(f"C{r['cp']}  idx {r['idx']}", True, (225, 230, 240)), (LEFT + 16, y + 9))
            self._hp_pips(surface, LEFT + 150, y + 10, r["hp"])
            surface.blit(self.f_xs.render(f"HP {r['hp']}", True, (150, 165, 190)), (LEFT + 222, y + 12))

            for j, c in enumerate(self.cols):
                v = r["q"].get(c)
                cell = pygame.Rect(LEFT + LABEL_W + j * COL_W + 4, y + 2, COL_W - 8, ROW_H - 8)
                is_best = c == r["best"]
                pygame.draw.rect(surface, heat((v - self.vmin) / span) if v is not None else (60, 60, 70), cell, border_radius=6)
                if is_best:
                    pygame.draw.rect(surface, GOLD, cell, 3, border_radius=6)
                if v is not None:
                    t = self.f_md.render(f"{v:.1f}", True, (255, 255, 255))
                    surface.blit(t, t.get_rect(center=cell.center))
        surface.set_clip(None)

        # scrollbar
        if self.max_scroll:
            pygame.draw.rect(surface, (38, 44, 62), (SB_X, ROWS_Y, SB_W, self.view_h), border_radius=5)
            pygame.draw.rect(surface, (110, 160, 230) if self.dragging else (80, 120, 190), self._thumb(), border_radius=5)

        # คำอธิบายด้านล่าง
        hint = "ขอบทอง = action ที่ดีที่สุดของ state   |   เลื่อน: เมาส์วีล / ↑↓ / ลาก scrollbar   |   T ฝึกใหม่   R โหลดใหม่"
        surface.blit(self.f_xs.render(hint, True, (140, 152, 175)), (LEFT, 702))
        self._draw_dropdown_list(surface)

    def _draw_dropdown_button(self, surface):
        r = self.dd_rect
        pygame.draw.rect(surface, PANEL_BG, r, border_radius=6)
        pygame.draw.rect(surface, (110, 160, 230) if self.dd_open else (80, 90, 120), r, 2, border_radius=6)
        label = fit(self.f_sm, f"ไฟล์: {self.cur}" if self.files else "ไม่พบไฟล์ Q-table", r.w - 50)
        surface.blit(self.f_sm.render(label, True, (225, 230, 240)), (r.x + 12, r.y + 5))
        cx, cy = r.right - 20, r.centery
        pts = [(cx - 6, cy + 3), (cx + 6, cy + 3), (cx, cy - 4)] if self.dd_open else [(cx - 6, cy - 3), (cx + 6, cy - 3), (cx, cy + 4)]
        pygame.draw.polygon(surface, (200, 210, 230), pts)

    def _draw_dropdown_list(self, surface):
        if not self.dd_open:
            return
        mouse = pygame.mouse.get_pos()
        n = max(1, len(self.files))
        bg = pygame.Rect(self.dd_rect.x - 4, self.dd_rect.bottom - 2, self.dd_rect.w + 8, n * 32 + 8)
        pygame.draw.rect(surface, (24, 28, 44), bg, border_radius=8)
        pygame.draw.rect(surface, (110, 160, 230), bg, 2, border_radius=8)
        if not self.files:
            surface.blit(self.f_sm.render("ไม่พบไฟล์ .json ที่มี q_table", True, (170, 180, 200)), (bg.x + 12, bg.y + 8))
        for i, p in enumerate(self.files):
            r = self._item_rect(i)
            if p == self.cur:
                pygame.draw.rect(surface, (50, 80, 140), r, border_radius=5)
            elif r.collidepoint(mouse):
                pygame.draw.rect(surface, (44, 50, 70), r, border_radius=5)
            surface.blit(self.f_sm.render(fit(self.f_sm, p, r.w - 20), True, (225, 230, 240)), (r.x + 10, r.y + 4))