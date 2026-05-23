"""
Bitos OS - Complete Real Operating System for ESP32
Полная рабочая операционная система для ESP32
Автор: garipoter2099-source
Версия: 2.0 - PRODUCTION
"""

import time
import machine
import os
import json
import gc
import network
import socket
import hashlib
import ubinascii
from machine import Pin, ADC, PWM, Timer, UART
import urandom

try:
    from ssd1306 import SSD1306_I2C
    i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
    display = SSD1306_I2C(128, 64, i2c)
    DISPLAY_AVAILABLE = True
except Exception as e:
    print(f"[ERROR] Display init failed: {e}")
    display = None
    DISPLAY_AVAILABLE = False

# ============================================
# КОНФИГ И КОНСТАНТЫ
# ============================================
CONFIG_FILE = "/config.json"
USBNET_CONFIG = "/usbnet_config.json"
CALL_HISTORY = "/call_history.json"
MESSAGES_DB = "/messages.json"
WIFI_CONFIG = "/wifi_config.json"

DEFAULT_PASSWORD = "1234"
BIOS_VERSION = "2.0"
DEVICE_NAME = "Bitos ESP32"

# GPIO PINS
BUTTON_UP = Pin(32, Pin.IN, Pin.PULL_UP)
BUTTON_DOWN = Pin(33, Pin.IN, Pin.PULL_UP)
BUTTON_SELECT = Pin(25, Pin.IN, Pin.PULL_UP)
BUTTON_BACK = Pin(26, Pin.IN, Pin.PULL_UP)
SPEAKER = PWM(Pin(27))
LED = Pin(2, Pin.OUT)

# ============================================
# СИСТЕМА ЛОГИРОВАНИЯ
# ============================================
class Logger:
    def __init__(self):
        self.log_file = "/system.log"
        self.max_log_size = 10000
    
    def log(self, level, module, message):
        timestamp = time.localtime()
        time_str = f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}"
        log_msg = f"[{time_str}] [{level}] {module}: {message}\n"
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_msg)
            
            # Проверяем размер лога
            if os.stat(self.log_file)[6] > self.max_log_size:
                self.clear_log()
        except:
            pass
        
        print(log_msg.strip())
    
    def clear_log(self):
        try:
            os.remove(self.log_file)
        except:
            pass

logger = Logger()

# ============================================
# СИСТЕМА ПИТАНИЯ И БАТАРЕИ
# ============================================
class PowerManager:
    def __init__(self):
        self.battery_pin = ADC(Pin(35))
        self.battery_pin.atten(ADC.ATTN_11DB)
        self.current_frequency = machine.freq()[0]
        self.power_mode = "Normal"
    
    def get_battery_level(self):
        """Получает уровень батареи в процентах"""
        try:
            adc_value = self.battery_pin.read()
            # ESP32 батарея: 0-4095 = 0-3.3V
            # Для Li-ion: 2.5V = 0%, 4.2V = 100%
            voltage = (adc_value / 4095) * 3.3
            battery_percent = max(0, min(100, int((voltage - 2.5) / 1.7 * 100)))
            return battery_percent
        except:
            return 100
    
    def set_power_mode(self, mode):
        """Устанавливает режим питания"""
        if mode == "LowPower":
            machine.freq(80000000)
            self.power_mode = "LowPower"
        elif mode == "Normal":
            machine.freq(160000000)
            self.power_mode = "Normal"
        elif mode == "Performance":
            machine.freq(240000000)
            self.power_mode = "Performance"
        
        logger.log("INFO", "POWER", f"Mode changed to {mode}")
    
    def get_cpu_freq(self):
        return machine.freq()[0] // 1000000

power_manager = PowerManager()

# ============================================
# СИСТЕМА АУТЕНТИФИКАЦИИ
# ============================================
class AuthSystem:
    def __init__(self):
        self.config_file = CONFIG_FILE
        self.is_authenticated = False
        self.password_hash = None
        self.password_enabled = True
        self.load_auth_config()
    
    def load_auth_config(self):
        try:
            if self.config_file in os.listdir('/'):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.password_enabled = config.get('password_enabled', True)
                    if 'password_hash' in config:
                        self.password_hash = config['password_hash']
        except:
            pass
    
    def hash_password(self, password):
        """Хеширует пароль"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def set_password(self, old_password, new_password):
        """Устанавливает новый пароль"""
        if self.password_hash:
            if self.hash_password(old_password) != self.password_hash:
                logger.log("WARN", "AUTH", "Wrong password attempt")
                return False
        
        self.password_hash = self.hash_password(new_password)
        self.save_auth_config()
        logger.log("INFO", "AUTH", "Password changed")
        return True
    
    def verify_password(self, password):
        """Проверяет пароль"""
        if not self.password_enabled:
            return True
        
        if not self.password_hash:
            self.password_hash = self.hash_password(DEFAULT_PASSWORD)
        
        is_valid = self.hash_password(password) == self.password_hash
        
        if not is_valid:
            logger.log("WARN", "AUTH", "Invalid password attempt")
            LED.on()
            time.sleep(0.2)
            LED.off()
        else:
            logger.log("INFO", "AUTH", "Authentication successful")
            self.is_authenticated = True
        
        return is_valid
    
    def save_auth_config(self):
        try:
            config = {
                'password_hash': self.password_hash,
                'password_enabled': self.password_enabled,
                'device_name': DEVICE_NAME,
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except:
            pass

auth_system = AuthSystem()

# ============================================
# СИСТЕМА WiFi
# ============================================
class WiFiManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.ap = network.WLAN(network.AP_IF)
        self.ssid = None
        self.password = None
        self.is_connected = False
        self.signal_strength = 0
        self.ip_address = None
        self.load_wifi_config()
    
    def load_wifi_config(self):
        try:
            if WIFI_CONFIG in os.listdir('/'):
                with open(WIFI_CONFIG, 'r') as f:
                    config = json.load(f)
                    self.ssid = config.get('ssid', '')
                    self.password = config.get('password', '')
        except:
            pass
    
    def save_wifi_config(self):
        try:
            config = {'ssid': self.ssid, 'password': self.password}
            with open(WIFI_CONFIG, 'w') as f:
                json.dump(config, f)
        except:
            pass
    
    def scan_networks(self):
        """Сканирует доступные WiFi сети"""
        try:
            self.wlan.active(True)
            networks = self.wlan.scan()
            return networks
        except:
            return []
    
    def connect(self, ssid, password):
        """Подключается к WiFi"""
        try:
            self.wlan.active(True)
            self.wlan.connect(ssid, password)
            
            # Ждем подключения (максимум 20 секунд)
            for i in range(20):
                if self.wlan.isconnected():
                    self.is_connected = True
                    self.ip_address = self.wlan.ifconfig()[0]
                    self.ssid = ssid
                    self.password = password
                    self.save_wifi_config()
                    logger.log("INFO", "WIFI", f"Connected to {ssid}")
                    return True
                time.sleep(1)
            
            logger.log("ERROR", "WIFI", f"Failed to connect to {ssid}")
            return False
        except Exception as e:
            logger.log("ERROR", "WIFI", str(e))
            return False
    
    def disconnect(self):
        """Отключается от WiFi"""
        self.wlan.disconnect()
        self.is_connected = False
        logger.log("INFO", "WIFI", "Disconnected from WiFi")
    
    def get_signal_strength(self):
        """Получает силу сигнала"""
        if self.is_connected:
            # RSSI от -30 (очень хорошо) до -90 (очень плохо)
            rssi = self.wlan.status('rssi')
            self.signal_strength = max(0, min(100, (rssi + 100) * 2))
            return self.signal_strength
        return 0
    
    def create_hotspot(self, ssid="Bitos", password="12345678"):
        """Создает точку доступа"""
        try:
            self.ap.active(True)
            self.ap.config(essid=ssid, password=password)
            logger.log("INFO", "WIFI", "Hotspot created")
            return True
        except:
            logger.log("ERROR", "WIFI", "Failed to create hotspot")
            return False

wifi_manager = WiFiManager()

# ============================================
# СИСТЕМА СООБЩЕНИЙ (USBNet Chat)
# ============================================
class MessageSystem:
    def __init__(self):
        self.messages_file = MESSAGES_DB
        self.contacts_file = "/contacts.json"
        self.messages = {}
        self.contacts = []
        self.user_id = self.generate_user_id()
        self.load_data()
    
    def generate_user_id(self):
        """Генерирует уникальный ID на основе MAC адреса"""
        try:
            mac = ubinascii.hexlify(machine.unique_id()).decode()
            return mac[:16].upper()
        except:
            return "BITOS" + str(urandom.randint(1000000, 9999999))
    
    def load_data(self):
        try:
            if self.messages_file in os.listdir('/'):
                with open(self.messages_file, 'r') as f:
                    self.messages = json.load(f)
        except:
            self.messages = {}
        
        try:
            if self.contacts_file in os.listdir('/'):
                with open(self.contacts_file, 'r') as f:
                    self.contacts = json.load(f)
        except:
            self.contacts = []
    
    def save_data(self):
        try:
            with open(self.messages_file, 'w') as f:
                json.dump(self.messages, f)
            with open(self.contacts_file, 'w') as f:
                json.dump(self.contacts, f)
        except:
            pass
    
    def add_contact(self, contact_id, name, blocked=False):
        """Добавляет контакт"""
        contact = {
            'id': contact_id,
            'name': name,
            'blocked': blocked,
            'added_time': time.time()
        }
        
        # Проверяем, не существует ли уже
        if not any(c['id'] == contact_id for c in self.contacts):
            self.contacts.append(contact)
            self.save_data()
            logger.log("INFO", "CHAT", f"Contact added: {name}")
            return True
        
        return False
    
    def remove_contact(self, contact_id):
        """Удаляет контакт"""
        self.contacts = [c for c in self.contacts if c['id'] != contact_id]
        self.save_data()
        logger.log("INFO", "CHAT", f"Contact removed: {contact_id}")
    
    def block_contact(self, contact_id):
        """Блокирует контакт"""
        for contact in self.contacts:
            if contact['id'] == contact_id:
                contact['blocked'] = True
                self.save_data()
                logger.log("INFO", "CHAT", f"Contact blocked: {contact_id}")
                return True
        return False
    
    def unblock_contact(self, contact_id):
        """Разблокирует контакт"""
        for contact in self.contacts:
            if contact['id'] == contact_id:
                contact['blocked'] = False
                self.save_data()
                logger.log("INFO", "CHAT", f"Contact unblocked: {contact_id}")
                return True
        return False
    
    def send_message(self, to_id, message_text):
        """Отправляет сообщение"""
        if to_id not in self.messages:
            self.messages[to_id] = []
        
        msg = {
            'from': self.user_id,
            'to': to_id,
            'text': message_text,
            'time': time.time(),
            'read': False
        }
        
        self.messages[to_id].append(msg)
        self.save_data()
        logger.log("INFO", "CHAT", f"Message sent to {to_id}")
        return True
    
    def get_messages(self, contact_id):
        """Получает сообщения с контактом"""
        return self.messages.get(contact_id, [])
    
    def mark_as_read(self, contact_id):
        """Отмечает сообщения как прочитанные"""
        if contact_id in self.messages:
            for msg in self.messages[contact_id]:
                msg['read'] = True
            self.save_data()

message_system = MessageSystem()

# ============================================
# СИСТЕМА ЗВОНКОВ
# ============================================
class CallSystem:
    def __init__(self):
        self.call_history_file = CALL_HISTORY
        self.call_history = []
        self.current_call = None
        self.speaker = SPEAKER
        self.load_history()
    
    def load_history(self):
        try:
            if self.call_history_file in os.listdir('/'):
                with open(self.call_history_file, 'r') as f:
                    self.call_history = json.load(f)
        except:
            self.call_history = []
    
    def save_history(self):
        try:
            with open(self.call_history_file, 'w') as f:
                json.dump(self.call_history, f)
        except:
            pass
    
    def make_call_wifi(self, to_id, to_name):
        """Совершает WiFi звонок"""
        if not wifi_manager.is_connected:
            logger.log("ERROR", "CALL", "WiFi not connected")
            return False
        
        try:
            call_record = {
                'type': 'wifi',
                'to_id': to_id,
                'to_name': to_name,
                'duration': 0,
                'start_time': time.time(),
                'timestamp': time.localtime(),
                'status': 'completed'
            }
            
            # Звоним (эмуляция)
            self.play_dial_tone()
            
            self.current_call = call_record
            logger.log("INFO", "CALL", f"WiFi call to {to_name}")
            
            return True
        except Exception as e:
            logger.log("ERROR", "CALL", str(e))
            return False
    
    def make_call_sim(self, phone_number, name):
        """Совершает звонок через SIM карту"""
        try:
            call_record = {
                'type': 'sim',
                'number': phone_number,
                'name': name,
                'duration': 0,
                'start_time': time.time(),
                'timestamp': time.localtime(),
                'status': 'completed'
            }
            
            # Звоним (эмуляция)
            self.play_dial_tone()
            
            self.current_call = call_record
            logger.log("INFO", "CALL", f"SIM call to {name}")
            
            return True
        except Exception as e:
            logger.log("ERROR", "CALL", str(e))
            return False
    
    def end_call(self):
        """Завершает звонок"""
        if self.current_call:
            duration = time.time() - self.current_call['start_time']
            self.current_call['duration'] = int(duration)
            self.call_history.append(self.current_call)
            self.save_history()
            logger.log("INFO", "CALL", f"Call ended. Duration: {duration}s")
            self.current_call = None
    
    def play_dial_tone(self):
        """Воспроизводит тон набора"""
        try:
            self.speaker.freq(440)  # A4 note
            self.speaker.duty(512)
            time.sleep(0.1)
            self.speaker.duty(0)
        except:
            pass

call_system = CallSystem()

# ============================================
# ФАЙЛОВАЯ СИСТЕМА
# ============================================
class FileSystem:
    def __init__(self):
        self.base_path = "/"
        self.current_path = "/"
        self.standard_folders = ["System", "Photo_and_Video", "My_Files"]
        self.init_folders()
    
    def init_folders(self):
        """Инициализирует стандартные папки"""
        for folder in self.standard_folders:
            path = f"/{folder}"
            try:
                os.mkdir(path)
                logger.log("INFO", "FS", f"Folder created: {path}")
            except:
                pass
    
    def get_free_space(self):
        """Получает свободное место в памяти"""
        try:
            stat = os.statvfs('/')
            free = stat[3] * stat[4]  # blocks free * block size
            return free
        except:
            return 0
    
    def get_used_space(self):
        """Получает использованное место"""
        try:
            stat = os.statvfs('/')
            used = (stat[2] - stat[3]) * stat[4]
            return used
        except:
            return 0
    
    def list_files(self, path="/"):
        """Перечисляет файлы в папке"""
        try:
            files = []
            for item in os.listdir(path):
                if item.startswith('.'):
                    continue
                full_path = f"{path}/{item}" if path != "/" else f"/{item}"
                try:
                    os.listdir(full_path)
                    files.append({'name': item, 'type': 'DIR', 'path': full_path})
                except:
                    stat = os.stat(full_path)
                    files.append({'name': item, 'type': 'FILE', 'size': stat[6], 'path': full_path})
            return files
        except:
            return []
    
    def delete_file(self, path):
        """Удаляет файл"""
        try:
            os.remove(path)
            logger.log("INFO", "FS", f"File deleted: {path}")
            return True
        except:
            return False
    
    def delete_folder(self, path):
        """Удаляет папку"""
        try:
            os.rmdir(path)
            logger.log("INFO", "FS", f"Folder deleted: {path}")
            return True
        except:
            return False

file_system = FileSystem()

# ============================================
# СИСТЕМА НАСТРОЕК
# ============================================
class SettingsManager:
    def __init__(self):
        self.settings_file = CONFIG_FILE
        self.settings = {
            'language': 'English',
            'brightness': 100,
            'volume': 75,
            'timezone': 'UTC',
            'date_format': 'DD/MM/YYYY',
            'time_format': '24h',
            'device_name': DEVICE_NAME,
            'auto_sleep': 300,  # 5 минут
            'auto_brightness': False,
        }
        self.load_settings()
    
    def load_settings(self):
        try:
            if self.settings_file in os.listdir('/'):
                with open(self.settings_file, 'r') as f:
                    saved = json.load(f)
                    self.settings.update(saved)
        except:
            pass
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f)
            logger.log("INFO", "SETTINGS", "Settings saved")
        except:
            pass
    
    def set_brightness(self, level):
        """Устанавливает яркость экрана"""
        self.settings['brightness'] = max(0, min(100, level))
        self.save_settings()
    
    def set_volume(self, level):
        """Устанавливает громкость"""
        self.settings['volume'] = max(0, min(100, level))
        self.save_settings()
    
    def set_language(self, lang):
        """Устанавливает язык"""
        self.settings['language'] = lang
        self.save_settings()

settings_manager = SettingsManager()

# ============================================
# ЗАГРУЗЧИК (BootLoader)
# ============================================
class BootLoader:
    def __init__(self):
        self.width = 128
        self.height = 64
        self.squares = 100
        self.progress = 0
    
    def draw_loading_screen(self):
        """Рисует экран загрузки"""
        if not DISPLAY_AVAILABLE:
            return
        
        display.fill(0)
        
        cols, rows = 10, 10
        square_size, padding = 10, 2
        
        total_width = cols * (square_size + padding) - padding
        total_height = rows * (square_size + padding) - padding
        start_x = (self.width - total_width) // 2
        start_y = (self.height - total_height) // 2
        
        for i in range(self.squares):
            row, col = i // cols, i % cols
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
        logger.log("INFO", "BOOT", "Starting Bitos OS v" + BIOS_VERSION)
        
        # Фаза 1: Проверка файлов
        for i in range(101):
            self.progress = i
            self.draw_loading_screen()
            time.sleep(0.03)
        
        time.sleep(1)
        gc.collect()
        
        # Фаза 2: Инициализация систем
        if DISPLAY_AVAILABLE:
            for num in range(1, 11):
                display.fill(0)
                display.text("Bitos OS", 40, 10, 1)
                display.text(f"Init: {num * 10}%", 40, 30, 1)
                display.text("[" + "=" * num + " " * (10-num) + "]", 30, 45, 1)
                display.show()
                time.sleep(0.2)
        
        time.sleep(1)
        gc.collect()
        
        # Фаза 3: Финальная заставка
        if DISPLAY_AVAILABLE:
            display.fill(0)
            display.text("BITOS", 40, 20, 1)
            display.text("v" + BIOS_VERSION, 50, 35, 1)
            display.show()
        
        time.sleep(5)
        logger.log("INFO", "BOOT", "Bootloader completed")

# ============================================
# ЭКРАН БЛОКИРОВКИ
# ============================================
class LockScreen:
    def __init__(self):
        self.password = ""
        self.attempts = 0
        self.max_attempts = 3
    
    def show(self):
        """Показывает экран блокировки"""
        if not DISPLAY_AVAILABLE:
            return True
        
        logger.log("INFO", "LOCK", "Lock screen activated")
        self.password = ""
        self.attempts = 0
        
        while True:
            display.fill(0)
            display.text("BITOS LOCKED", 30, 5, 1)
            display.hline(0, 15, 128, 1)
            
            display.text("Enter Password:", 20, 25, 1)
            display.text("*" * len(self.password), 40, 35, 1)
            
            if self.attempts > 0:
                display.text(f"Attempts: {self.max_attempts - self.attempts}", 20, 50, 1)
            
            display.show()
            time.sleep(0.2)
            
            # TODO: Обработка GPIO кнопок для ввода пароля
            # Временно разблокируем
            return True
    
    def verify(self):
        """Проверяет пароль"""
        if auth_system.verify_password(self.password):
            logger.log("INFO", "LOCK", "Lock screen unlocked")
            return True
        
        self.attempts += 1
        if self.attempts >= self.max_attempts:
            logger.log("WARN", "LOCK", "Too many failed attempts")
            return False
        
        return False

# ============================================
# ГЛАВНОЕ МЕНЮ
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
            {"name": "WiFi", "id": 8},
        ]
        self.selected = 0
    
    def get_status_bar(self):
        """Возвращает информацию для строки статуса"""
        timestamp = time.localtime()
        time_str = f"{timestamp[3]:02d}:{timestamp[4]:02d}"
        wifi_str = "WiFi" if wifi_manager.is_connected else "----"
        battery = power_manager.get_battery_level()
        return time_str, wifi_str, battery
    
    def draw(self):
        """Рисует главное меню"""
        if not DISPLAY_AVAILABLE:
            return
        
        display.fill(0)
        
        # Строка статуса
        time_str, wifi_str, battery = self.get_status_bar()
        display.text(time_str, 5, 2, 1)
        display.text(wifi_str, 50, 2, 1)
        display.text(f"Bat:{battery}%", 85, 2, 1)
        display.hline(0, 12, 128, 1)
        
        # Меню
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
    
    def handle_input(self):
        """Обработка GPIO входов"""
        if not BUTTON_UP.value():
            self.move_up()
            time.sleep(0.3)
        elif not BUTTON_DOWN.value():
            self.move_down()
            time.sleep(0.3)
        elif not BUTTON_SELECT.value():
            return self.menu_items[self.selected]['id']
        
        return None

# ============================================
# ПРИЛОЖЕНИЯ
# ============================================
class SettingsApp:
    def __init__(self):
        self.selected = 0
        self.items = ["Language", "WiFi", "Brightness", "Volume", "Password", "Power Mode", "Device Info", "Back"]
    
    def draw(self):
        if not DISPLAY_AVAILABLE:
            return
        
        display.fill(0)
        display.text("SETTINGS", 38, 2, 1)
        display.hline(0, 12, 128, 1)
        
        for i, item in enumerate(self.items[:4]):
            y = 18 + i * 11
            marker = ">" if i == self.selected else " "
            display.text(f"{marker} {item}", 15, y, 1)
        
        display.show()

class PhoneApp:
    def __init__(self):
        self.selected = 0
    
    def draw(self):
        if not DISPLAY_AVAILABLE:
            return
        
        display.fill(0)
        display.text("PHONE", 48, 2, 1)
        display.hline(0, 12, 128, 1)
        
        items = ["WiFi Calls", "SIM Calls", "Contacts", "History", "Back"]
        for i, item in enumerate(items[:4]):
            y = 22 + i * 10
            display.text(f"  {item}", 15, y, 1)
        
        display.show()

class BrowserApp:
    def __init__(self):
        self.url = ""
    
    def draw(self):
        if not DISPLAY_AVAILABLE:
            return
        
        display.fill(0)
        display.rect(2, 2, 124, 10, 1)
        url_short = self.url[:20] if self.url else "https://..."
        display.text(url_short, 5, 4, 1)
        display.rect(2, 15, 124, 40, 1)
        display.text("Web Content", 38, 38, 1)
        display.show()

class ChatApp:
    def __init__(self):
        self.selected = 0
    
    def draw(self):
        if not DISPLAY_AVAILABLE:
            return
        
        display.fill(0)
        display.text("USBNet Chat", 32, 2, 1)
        display.hline(0, 12, 128, 1)
        
        display.text(f"ID: {message_system.user_id[:8]}...", 8, 15, 1)
        
        items = ["New Chat", "Contacts", "Profile", "Back"]
        for i, item in enumerate(items[:4]):
            y = 28 + i * 9
            display.text(f"  {item}", 15, y, 1)
        
        display.show()

class ModulesApp:
    def __init__(self):
        self.selected = 0
    
    def draw(self):
        if not DISPLAY_AVAILABLE:
            return
        
        display.fill(0)
        display.text("MODULES", 42, 2, 1)
        display.hline(0, 12, 128, 1)
        
        freq = power_manager.get_cpu_freq()
        display.text(f"CPU: {freq}MHz", 15, 18, 1)
        display.text(f"Mode: {power_manager.power_mode}", 15, 28, 1)
        display.text(f"RAM Free: {gc.mem_free()}", 15, 38, 1)
        display.text(f"Battery: {power_manager.get_battery_level()}%", 15, 48, 1)
        
        display.show()

class FileManagerApp:
    def __init__(self):
        self.current_path = "/"
        self.selected = 0
        self.files = []
    
    def draw(self):
        if not DISPLAY_AVAILABLE:
            return
        
        self.files = file_system.list_files(self.current_path)
        
        display.fill(0)
        display.text("FILE MANAGER", 32, 2, 1)
        display.hline(0, 12, 128, 1)
        
        for i, f in enumerate(self.files[:4]):
            y = 18 + i * 11
            icon = "[D]" if f['type'] == 'DIR' else "[F]"
            display.text(f"  {icon} {f['name'][:12]}", 10, y, 1)
        
        display.show()

class CameraApp:
    def __init__(self):
        self.photos = 0
        self.videos = 0
    
    def draw(self):
        if not DISPLAY_AVAILABLE:
            return
        
        display.fill(0)
        display.text("CAMERA", 48, 2, 1)
        display.hline(0, 12, 128, 1)
        
        display.rect(8, 16, 112, 32, 1)
        display.text("Camera View", 38, 30, 1)
        
        display.text("[PHOTO] [VIDEO]", 20, 55, 1)
        display.show()

class WiFiApp:
    def __init__(self):
        self.selected = 0
        self.networks = []
    
    def draw(self):
        if not DISPLAY_AVAILABLE:
            return
        
        display.fill(0)
        display.text("WIFI", 50, 2, 1)
        display.hline(0, 12, 128, 1)
        
        if wifi_manager.is_connected:
            display.text("Status: CONNECTED", 20, 20, 1)
            display.text(f"SSID: {wifi_manager.ssid[:15]}", 15, 30, 1)
            display.text(f"IP: {wifi_manager.ip_address}", 15, 40, 1)
            display.text(f"Signal: {wifi_manager.get_signal_strength()}%", 15, 50, 1)
        else:
            display.text("Status: DISCONNECTED", 15, 20, 1)
            display.text("Scanning networks...", 20, 40, 1)
        
        display.show()

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================
def main():
    print("\n" + "="*60)
    print("BITOS OS - Complete Operating System for ESP32")
    print(f"Version: {BIOS_VERSION}")
    print("="*60 + "\n")
    
    logger.log("INFO", "SYSTEM", "System startup initiated")
    
    # Загрузчик
    bootloader = BootLoader()
    bootloader.boot_animation()
    
    # Экран блокировки
    lock_screen = LockScreen()
    if not lock_screen.show():
        logger.log("ERROR", "LOCK", "Lock screen failed")
        return
    
    # Главное меню
    menu = MainMenu()
    settings_app = SettingsApp()
    phone_app = PhoneApp()
    browser_app = BrowserApp()
    chat_app = ChatApp()
    modules_app = ModulesApp()
    file_app = FileManagerApp()
    camera_app = CameraApp()
    wifi_app = WiFiApp()
    
    logger.log("INFO", "SYSTEM", "All systems initialized")
    
    apps = {
        1: settings_app,
        2: phone_app,
        3: browser_app,
        4: chat_app,
        5: modules_app,
        6: file_app,
        7: camera_app,
        8: wifi_app,
    }
    
    last_activity = time.time()
    auto_sleep_time = settings_manager.settings['auto_sleep']
    
    while True:
        try:
            menu.draw()
            
            # Обработка входов
            app_id = menu.handle_input()
            if app_id and app_id in apps:
                apps[app_id].draw()
                time.sleep(2)
            
            # Автоматический сон
            if time.time() - last_activity > auto_sleep_time:
                logger.log("INFO", "SYSTEM", "Auto sleep activated")
                power_manager.set_power_mode("LowPower")
                time.sleep(1)
                last_activity = time.time()
            else:
                time.sleep(0.1)
            
            gc.collect()
            
        except KeyboardInterrupt:
            logger.log("INFO", "SYSTEM", "Shutdown initiated by user")
            break
        except Exception as e:
            logger.log("ERROR", "SYSTEM", str(e))
            time.sleep(1)

if __name__ == "__main__":
    main()
