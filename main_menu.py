"""
Bitos OS - Main Menu
Главное меню системы
Автор: garipoter2099-source
"""

import time
import machine
import gc

try:
    from ssd1306 import SSD1306_I2C
    i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
    display = SSD1306_I2C(128, 64, i2c)
except Exception as e:
    print(f"Display error: {e}")
    display = None

class MainMenu:
    def __init__(self):
        self.width = 128
        self.height = 64
        self.menu_items = [
            {"name": "Settings", "icon": "⚙", "id": 1},
            {"name": "Phone", "icon": "☎", "id": 2},
            {"name": "Browser", "icon": "🌐", "id": 3},
            {"name": "USBNet Chat", "icon": "💬", "id": 4},
            {"name": "Modules", "icon": "📦", "id": 5},
            {"name": "Files", "icon": "📁", "id": 6},
            {"name": "Camera", "icon": "📷", "id": 7},
        ]
        self.selected = 0
        self.time_str = "10:30"
        self.wifi_status = "Connected"
        self.battery = 100
        self.volume = 75
        
    def draw_header(self):
        """Рисует верхнюю панель"""
        if not display:
            return
        
        display.text(self.time_str, 5, 2, 1)
        display.text(self.wifi_status[:5], 55, 2, 1)
        display.text(f"Bat:{self.battery}%", 85, 2, 1)
        display.hline(0, 12, 128, 1)
    
    def draw_menu(self):
        """Рисует главное меню"""
        if not display:
            return
        
        display.fill(0)
        self.draw_header()
        
        items_per_screen = 4
        start_idx = (self.selected // items_per_screen) * items_per_screen
        
        for i in range(items_per_screen):
            idx = start_idx + i
            if idx >= len(self.menu_items):
                break
            
            item = self.menu_items[idx]
            y = 18 + i * 11
            
            if idx == self.selected:
                display.fill_rect(1, y - 2, 126, 11, 1)
                display.text(f"{item['icon']} {item['name']}", 12, y, 0)
            else:
                display.text(f"  {item['icon']} {item['name']}", 12, y, 1)
        
        display.show()
    
    def move_down(self):
        if self.selected < len(self.menu_items) - 1:
            self.selected += 1
    
    def move_up(self):
        if self.selected > 0:
            self.selected -= 1
    
    def select_item(self):
        """Выбрать пункт меню"""
        item = self.menu_items[self.selected]
        print(f"[MENU] Selected: {item['name']}")
        
        if item['id'] == 1:
            import settings
            settings.run()
        elif item['id'] == 2:
            import phone_app
            phone_app.run()
        elif item['id'] == 3:
            import browser
            browser.run()
        elif item['id'] == 4:
            import usbnet_chat
            usbnet_chat.run()
        elif item['id'] == 5:
            import modules_panel
            modules_panel.run()
        elif item['id'] == 6:
            import file_manager
            file_manager.run()
        elif item['id'] == 7:
            import camera_app
            camera_app.run()
    
    def run(self):
        """Главный цикл меню"""
        print("[MAIN_MENU] Starting main menu...")
        
        while True:
            self.draw_menu()
            time.sleep(0.2)
            gc.collect()
            
            # TODO: Обработка физических кнопок
            # Пока просто показываем меню

def run():
    """Точка входа"""
    menu = MainMenu()
    menu.run()

if __name__ == "__main__":
    run()
