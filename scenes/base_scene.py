# scenes/base_scene.py
class BaseScene:
    def __init__(self, app):
        self.app = app

    def on_enter(self):
        """ทำงานเมื่อสลับเข้ามาที่ฉากนี้"""
        pass

    def on_exit(self):
        """ทำงานก่อนออกจากฉากนี้"""
        pass

    def handle_event(self, event):
        pass

    def update(self, dt_ms):
        pass

    def draw(self, surface):
        pass
