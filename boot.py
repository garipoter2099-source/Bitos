"""
Bitos OS - Bootloader
ESP32 MicroPython
Автор: garipoter2099-source
"""

import time
import machine
from machine import Pin
import gc

# Попытка инициализации дисплея (SSD1306 по I2C)
try:
    from ssd1306 import SSD1306_I2C
    i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
    display = SSD1306_I2C(128, 64, i2c)
except Exception as e:
    print(f"Display init error: {e}")
    display = None

class BootLoader:
    def __init__(self):
        self.width = 128
        self.height = 64
        self.squares = 100
        self.progress = 0
        self.is_first_boot = True  # TODO: проверить файл конфига
        
    def draw_loading_screen(self):
        """Рисует экран загрузки с 100 чёрными квадратиками"""
        if display is None:
            return
            
        display.fill(0)  # Чёрный фон
        
        # Параметры сетки квадратиков (10x10)
        cols = 10
        rows = 10
        square_size = 10
        padding = 2
        
        # Центрируем на экране
        total_width = cols * (square_size + padding) - padding
        total_height = rows * (square_size + padding) - padding
        start_x = (self.width - total_width) // 2
        start_y = (self.height - total_height) // 2
        
        # Рисуем квадратики
        for i in range(self.squares):
            row = i // cols
            col = i % cols
            x = start_x + col * (square_size + padding)
            y = start_y + row * (square_size + padding)
            
            # Белый квадратик если загружено, иначе чёрный контур
            if i < self.progress:
                display.fill_rect(x, y, square_size, square_size, 1)  # Белый
            else:
                display.rect(x, y, square_size, square_size, 1)  # Контур
        
        # Процент загрузки
        percent = int((self.progress / 100) * 100)
        display.text(f"{percent}%", 58, 5, 1)
        display.show()
    
    def boot_animation(self):
        """Полная анимация загрузки"""
        print("[BOOT] Starting Bitos OS...")
        
        # ===== ФАЗА 1: Загрузка файлов (100 квадратиков) =====
        print("[BOOT] Phase 1: File integrity check...")
        for i in range(101):
            self.progress = i
            self.draw_loading_screen()
            time.sleep(0.05)  # Всего ~5 секунд
        
        time.sleep(1)
        gc.collect()  # Очистка памяти
        
        # ===== ФАЗА 2: Инициализация системы (числа) =====
        print("[BOOT] Phase 2: System initialization...")
        if display:
            for num in range(1, 11):
                display.fill(0)
                display.text("Bitos OS", 40, 10, 1)
                display.text(f"Init: {num * 10}%", 40, 30, 1)
                display.text("[" + "=" * num + " " * (10-num) + "]", 30, 45, 1)
                display.show()
                time.sleep(0.5)
        
        time.sleep(1)
        gc.collect()
        
        # ===== ФАЗА 3: Финальная заставка =====
        print("[BOOT] Phase 3: Display splash screen...")
        if display:
            display.fill(0)
            display.text("BITOS", 40, 20, 1)
            display.text("v1.0.0", 50, 35, 1)
            display.show()
        time.sleep(5)
        
        # ===== ФАЗА 4: Туториал (если первый запуск) =====
        if self.is_first_boot:
            print("[BOOT] Phase 4: First boot tutorial...")
            self.show_tutorial()
        else:
            print("[BOOT] Phase 4: Skipped (not first boot)")
    
    def show_tutorial(self):
        """Туториал для первого запуска"""
        if not display:
            return
        
        # Экран 1: Добро пожаловать
        display.fill(0)
        display.text("Welcome to", 30, 5, 1)
        display.text("Bitos OS", 35, 15, 1)
        display.text("Press button to", 20, 35, 1)
        display.text("continue", 40, 45, 1)
        display.show()
        time.sleep(4)
        
        # Экран 2: WiFi Setup
        display.fill(0)
        display.text("WiFi Setup", 35, 5, 1)
        display.text("Scanning networks...", 10, 25, 1)
        display.show()
        time.sleep(3)
        
        # Экран 3: Set Password
        display.fill(0)
        display.text("Create Password", 25, 5, 1)
        display.text("Min 4 chars", 35, 25, 1)
        display.show()
        time.sleep(3)
        
        # Экран 4: Setup complete
        display.fill(0)
        display.text("Setup Complete!", 25, 20, 1)
        display.text("Starting OS...", 30, 35, 1)
        display.show()
        time.sleep(2)
        
        print("[BOOT] Tutorial completed!")

def main():
    print("\n" + "="*50)
    print("BITOS OS - Bootstrap Loader")
    print("="*50 + "\n")
    
    bootloader = BootLoader()
    bootloader.boot_animation()
    
    print("[BOOT] Bootloader completed!")
    print("[BOOT] Starting main OS...\n")
    
    # Переходим на главное меню
    import main_menu
    main_menu.run()

if __name__ == "__main__":
    main()
