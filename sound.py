# sound.py
import os
import pygame

class SoundManager:
    def __init__(self, sound_paths=None):
        self.enabled = True
        self.sounds = {}
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception:
                self.enabled = False
                return

        if sound_paths:
            for key, path in sound_paths.items():
                if path and os.path.exists(path):
                    try:
                        self.sounds[key] = pygame.mixer.Sound(path)
                    except Exception:
                        pass

    def toggle(self):
        self.enabled = not self.enabled

    def play(self, key):
        if self.enabled and key in self.sounds:
            try:
                self.sounds[key].play()
            except Exception:
                pass
