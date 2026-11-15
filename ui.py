# ui.py
import pygame
from config import WHITE, GRAY

class Button:
    def __init__(self, rect, text, color, text_color=WHITE, subtext=""):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.subtext = subtext
        self.color = color
        self.text_color = text_color
        self.hovered = False
        self.disabled = False

    def draw(self, surface, font, small_font):
        bg = GRAY if self.disabled else (
            tuple(min(255, c + 25) for c in self.color) if self.hovered else self.color
        )
        draw_rect = self.rect.move(0, -3) if (self.hovered and not self.disabled) else self.rect
        pygame.draw.rect(surface, bg, draw_rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, draw_rect, 2, border_radius=8)

        lbl = font.render(self.text, True, self.text_color)
        if self.subtext:
            surface.blit(lbl, (draw_rect.x + 12, draw_rect.y + 8))
            sub = small_font.render(self.subtext, True, (230, 230, 230))
            surface.blit(sub, (draw_rect.x + 12, draw_rect.y + 34))
        else:
            lbl_rect = lbl.get_rect(center=draw_rect.center)
            surface.blit(lbl, lbl_rect)

    def handle_event(self, event):
        if self.disabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False
