# config.py
import pygame

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (15, 15, 20)
GRAY = (110, 115, 125)
DARK_BG = (20, 22, 32)
PANEL_BG = (30, 34, 48)

GOLD_JUDGE = (230, 185, 65)
PURPLE_PROSECUTOR = (145, 70, 195)
BLUE_LAWYER = (45, 125, 220)
GREEN_SUCCESS = (55, 185, 105)
RED_DANGER = (220, 65, 75)
YELLOW_WARN = (240, 200, 70)
pygame.font.init()
GLOBAL_FONT = pygame.font.Font("assets/fonts/TorsilpThamnganMangThoe.ttf", 26)
