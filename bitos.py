"""
Bitos OS - Complete Operating System for ESP32
Полная операционная система для ESP32
Автор: garipoter2099-source
"""

import time
import machine
import os
import json
import gc

try:
    from ssd1306 import SSD1306_I2C
    i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
    display = SSD1306_I2C(128, 64, i2c)
except Exception as e:
    print(f"Display error: {e}")
    display = None

# ============================================
# BOOTLOADER
# ============================================
class BootLoader:
    def __init__(self):
        self.width = 128
        self.height = 64
        self.squares = 100
        self.progress = 0
        
    def draw_loading_screen(self):
        """Рисует экран загрузки с 100 чёрными квадратиками"""
        if display is None:
            return
            
        display.fill(0)
        
        cols = 10
        rows = 10
        square_size = 10
        padding = 2
        
        total_width = cols * (square_size + padding) - padding
        total_height = rows * (square_size + padding) - padding
        start_x = (self.width - total_width) // 2
        start_y = (self.height - total_height) // 2
        
        for i in range(self.squares):
            row = i // cols
            col = i % cols
            x = start_x + col * (square_size + padding)
            y = start_y + row * (square_size + padding)
            
            if i < self.progress:
                display.fill_rect(x, y, square_size, square_size, 1)
            else:
                display.rect(x, y, square_size, square_size, 1)
        
        percent = int((self.progress / 100) * 100)
        display.text(f"{percent}%", 58, 5, 1)
        display.show()
    
    def boot_animation(self):
        """Полная анимация загрузки"""
        print("[BOOT] Starting Bitos OS...")
        
        # Фаза 1: Загрузка файлов
        for i in range(101):
            self.progress = i
            self.draw_loading_screen()
            time.sleep(0.05)
        
        time.sleep(1)
        gc.collect()
        
        # Фаза 2: Инициализация системы
        if display:
            for num in range(1, 11):
                display.fill(0)
                display.text("Bitos OS", 40, 10, 1)
                display.text(f"Init: {num * 10}%", 40, 30, 1)
                display.text("[" + "=" * num + " " * (10-num) + "]", 30, 45, 1)
                display.show()
                time.sleep(0.3)
        
        time.sleep(1)
        gc.collect()
        
        # Фаза 3: Финальная заставка
        if display:
            display.fill(0)
            display.text("BITOS", 40, 20, 1)
            display.text("v1.0.0", 50, 35, 1)
            display.show()
        time.sleep(5)
        
        print("[BOOT] Bootloader completed!")

# ============================================
# SETTINGS
# ============================================
class Settings:
    def __init__(self):
        self.config_file = "/config.json"
        self.settings = {
            "language": "English",
            "wifi_ssid": "",
            "brightness": 100,
            "volume": 75,
            "password": "1234",
            "password_enabled": True,
            "bluetooth": True,
            "device_name": "Bitos ESP32",
        }
        self.load_settings()
        self.selected = 0
    
    def load_settings(self):
        try:
            if self.config_file in os.listdir('/'):
                with open(self.config_file, 'r') as f:
                    saved = json.load(f)
                    self.settings.update(saved)
        except:
            pass
    
    def save_settings(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f)
        except:
            pass
    
    def draw_menu(self):
        if not display:
            return
        
        display.fill(0)
        display.text("SETTINGS", 38, 2, 1)
        display.hline(0, 12, 128, 1)
        
        menu_items = ["Language", "WiFi", "Brightness", "Volume", "Password", "Device Info", "Back"]
        
        for i, item in enumerate(menu_items[:4]):
            y = 18 + i * 11
            if i == self.selected:
                display.fill_rect(1, y - 2, 126, 11, 1)
                display.text(f"> {item}", 15, y, 0)
            else:
                display.text(f"  {item}", 15, y, 1)
        
        display.show()

# ============================================
# USBNET CHAT
# ============================================
class USBNetChat:
    def __init__(self):
        self.config_file = "/usbnet_config.json"
        self.user_id = self.generate_unique_id()
        self.user_config = {
            "user_id": self.user_id,
            "username": "Bitos User",
            "contacts": [],
        }
        self.load_config()
        self.selected = 0
    
    def generate_unique_id(self):
        try:
            import ubinascii
            mac = ubinascii.hexlify(machine.unique_id()).decode()
            return mac[:16].upper()
        except:
            return "BITOS0000000001"
    
    def load_config(self):
        try:
            if self.config_file in os.listdir('/'):
                with open(self.config_file, 'r') as f:
                    saved = json.load(f)
                    self.user_config.update(saved)
        except:
            self.save_config()
    
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.user_config, f)
        except:
            pass
    
    def draw_menu(self):
        if not display:
            return
        
        display.fill(0)
        display.text("USBNet Chat", 32, 2, 1)
        display.hline(0, 12, 128, 1)
        
        id_short = self.user_config['user_id'][:8]
        display.text(f"ID: {id_short}...", 8, 15, 1)
        
        for i, item in enumerate(["New Chat", "Contacts", "My Profile", "Back"]):
            y = 28 + i * 9
            if i == self.selected:
                display.fill_rect(1, y - 2, 126, 10, 1)
                display.text(f"> {item}", 20, y, 0)
            else:
                display.text(f"  {item}", 20, y, 1)
        
        display.show()

# ============================================
# FILE MANAGER
# ============================================
class FileManager:
    def __init__(self):
        self.current_path = "/"
        self.selected = 0
        self.init_folders()
        self.items = []
        self.load_directory()
    
    def init_folders(self):
        for folder in ["System", "Photo_and_Video", "My_Files"]:
            try:
                os.mkdir(f"/{folder}")
            except:
                pass
    
    def load_directory(self):
        self.items = []
        try:
            for item in os.listdir(self.current_path):
                if item.startswith('.'):
                    continue
                path = f"{self.current_path}/{item}" if self.current_path != "/" else f"/{item}"
                try:
                    os.listdir(path)
                    file_type = "FOLDER"
                except:
                    file_type = "FILE"
                self.items.append({"name": item, "type": file_type, "path": path})
        except:
            pass
        
        if self.current_path != "/":
            self.items.insert(0, {"name": ".. (Back)", "type": "BACK", "path": "/"})
    
    def draw_menu(self):
        if not display:
            return
        
        display.fill(0)
        display.text("File Manager", 32, 2, 1)
        display.hline(0, 12, 128, 1)
        
        for i in range(3):
            if i >= len(self.items):
                break
            item = self.items[i]
            y = 28 + i * 12
            icon = "[D]" if item['type'] == "FOLDER" else "[F]"
            name_short = item['name'][:15]
            
            if i == self.selected:
                display.fill_rect(1, y - 2, 126, 11, 1)
                display.text(f"{icon} {name_short}", 15, y, 0)
            else:
                display.text(f"{icon} {name_short}", 15, y, 1)
        
        display.show()

# ============================================
# CAMERA APP
# ============================================
class CameraApp:
    def __init__(self):
        self.photos_path = "/Photo_and_Video"
        self.quality = 100
        self.fps = 30
        self.photo_count = 0
        self.video_count = 0
    
    def draw_menu(self):
        if not display:
            return
        
        display.fill(0)
        display.text("Camera", 48, 2, 1)
        display.hline(0, 12, 128, 1)
        
        display.rect(8, 16, 112, 32, 1)
        display.text("Camera View", 38, 30, 1)
        
        display.text(f"Q:{self.quality}% FPS:{self.fps}", 8, 53, 1)
        display.text("[PHOTO] [VIDEO]", 25, 60, 1)
        
        display.show()

# ============================================
# PHONE APP
# ============================================
class PhoneApp:
    def __init__(self):
        self.call_history = []
        self.contacts = []
        self.selected = 0
    
    def draw_menu(self):
        if not display:
            return
        
        display.fill(0)
        display.text("Phone", 48, 2, 1)
        display.hline(0, 12, 128, 1)
        
        for i, item in enumerate(["WiFi Calls", "SIM Calls", "Contacts", "Back"]):
            y = 22 + i * 10
            if i == self.selected:
                display.fill_rect(1, y - 2, 126, 10, 1)
                display.text(f"> {item}", 20, y, 0)
            else:
                display.text(f"  {item}", 20, y, 1)
        
        display.show()

# ============================================
# WEB BROWSER
# ============================================
class Browser:
    def __init__(self):
        self.current_url = ""
        self.tabs = []
        self.bookmarks = [
            {"title": "Google", "url": "https://google.com"},
            {"title": "GitHub", "url": "https://github.com"},
            {"title": "Wikipedia", "url": "https://wikipedia.org"},
        ]
    
    def draw_menu(self):
        if not display:
            return
        
        display.fill(0)
        display.rect(2, 2, 124, 10, 1)
        url_short = self.current_url[:20] if self.current_url else "https://..."
        display.text(url_short, 5, 4, 1)
        
        display.rect(2, 15, 124, 40, 1)
        display.text("Web Content", 38, 38, 1)
        
        display.text("[RELOAD] [HOME]", 25, 58, 1)
        
        display.show()

# ============================================
# MODULES PANEL
# ============================================
class ModulesPanel:
    def __init__(self):
        self.cpu_freq = machine.freq()[0] // 1000000
        self.max_cpu_freq = 240
        self.power_mode = "Normal"
        self.modules = {
            "WiFi": {"enabled": True},
            "Bluetooth": {"enabled": True},
            "USB": {"enabled": True},
            "SPI": {"enabled": True},
        }
        self.selected = 0
    
    def draw_menu(self):
        if not display:
            return
        
        display.fill(0)
        display.text("Modules Panel", 32, 2, 1)
        display.hline(0, 12, 128, 1)
        
        for i, (module, status) in enumerate(list(self.modules.items())[:4]):
            y = 18 + i * 11
            enabled = "ON" if status['enabled'] else "OFF"
            
            if i == self.selected:
                display.fill_rect(1, y - 2, 126, 11, 1)
                display.text(f"> {module}: {enabled}", 15, y, 0)
            else:
                display.text(f"  {module}: {enabled}", 15, y, 1)
        
        display.show()

# ============================================
# MAIN MENU
# ============================================
class MainMenu:
    def __init__(self):
        self.menu_items = [
            {"name": "Settings", "id": 1},
            {"name": "Phone", "id": 2},
            {"name": "Browser", "id": 3},
            {"name": "USBNet Chat", "id": 4},
            {"name": "Modules", "id": 5},
            {"name": "Files", "id": 6},
            {"name": "Camera", "id": 7},
        ]
        self.selected = 0
        self.time_str = "10:30"
        self.battery = 100
    
    def draw_menu(self):
        if not display:
            return
        
        display.fill(0)
        display.text(self.time_str, 5, 2, 1)
        display.text("WiFi", 55, 2, 1)
        display.text(f"Bat:{self.battery}%", 85, 2, 1)
        display.hline(0, 12, 128, 1)
        
        for i in range(4):
            if i >= len(self.menu_items):
                break
            item = self.menu_items[i]
            y = 18 + i * 11
            
            if i == self.selected:
                display.fill_rect(1, y - 2, 126, 11, 1)
                display.text(f"> {item['name']}", 12, y, 0)
            else:
                display.text(f"  {item['name']}", 12, y, 1)
        
        display.show()
    
    def move_down(self):
        if self.selected < len(self.menu_items) - 1:
            self.selected += 1
    
    def move_up(self):
        if self.selected > 0:
            self.selected -= 1
    
    def select_item(self):
        item_id = self.menu_items[self.selected]['id']
        
        if item_id == 1:
            app = Settings()
        elif item_id == 2:
            app = PhoneApp()
        elif item_id == 3:
            app = Browser()
        elif item_id == 4:
            app = USBNetChat()
        elif item_id == 5:
            app = ModulesPanel()
        elif item_id == 6:
            app = FileManager()
        elif item_id == 7:
            app = CameraApp()
        else:
            return
        
        app.draw_menu()
        time.sleep(3)

# ============================================
# MAIN FUNCTION
# ============================================
def main():
    print("\n" + "="*50)
    print("BITOS OS - Operating System for ESP32")
    print("="*50 + "\n")
    
    # Загрузчик
    bootloader = BootLoader()
    bootloader.boot_animation()
    
    # Главное меню
    menu = MainMenu()
    
    print("[SYSTEM] Starting main menu...")
    
    while True:
        menu.draw_menu()
        time.sleep(1)
        gc.collect()
        
        # TODO: Обработка физических кнопок (GPIO)

if __name__ == "__main__":
    main()
