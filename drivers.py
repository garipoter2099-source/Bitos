"""
Bitos OS - Adaptive Universal Drivers
Адаптивные универсальные драйверы для всех устройств
Поддержка различных разрешений экрана и устройств
"""

import machine
import os
import json
import gc

# ============================================
# ДЕТЕКТИРОВАНИЕ ОБОРУДОВАНИЯ
# ============================================

class HardwareDetector:
    """Автоматическое определение оборудования"""
    
    def __init__(self):
        self.detected_devices = {}
        self.screen_config = None
        self.camera_type = None
        self.detect_all()
    
    def detect_i2c_devices(self):
        """Сканирует I2C устройства"""
        try:
            i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
            devices = i2c.scan()
            
            device_names = {}
            for addr in devices:
                if addr == 0x3c or addr == 0x3d:
                    device_names[addr] = "SSD1306_OLED"
                elif addr == 0x68:
                    device_names[addr] = "MPU6050_IMU"
                elif addr == 0x77:
                    device_names[addr] = "BMP280_SENSOR"
                elif addr == 0x48:
                    device_names[addr] = "ADS1115_ADC"
                else:
                    device_names[addr] = f"UNKNOWN_0x{addr:02x}"
            
            self.detected_devices['i2c'] = device_names
            return device_names
        except Exception as e:
            print(f"I2C scan error: {e}")
            return {}
    
    def detect_camera(self):
        """Определяет тип камеры"""
        try:
            import camera
            camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
            self.camera_type = "OV2640"
            self.detected_devices['camera'] = self.camera_type
            return self.camera_type
        except:
            pass
        
        try:
            import camera
            camera.init(0, format=camera.RGB565)
            self.camera_type = "OV7670"
            self.detected_devices['camera'] = self.camera_type
            return self.camera_type
        except:
            self.camera_type = None
            return None
    
    def detect_screen(self):
        """Определяет разрешение экрана"""
        i2c_devices = self.detected_devices.get('i2c', {})
        
        # Стандартные SSD1306
        if 0x3c in i2c_devices or 0x3d in i2c_devices:
            self.screen_config = {
                'type': 'SSD1306',
                'width': 128,
                'height': 64,
                'color_depth': 1,
                'address': 0x3c if 0x3c in i2c_devices else 0x3d
            }
        
        # Другие варианты
        elif 0x78 in i2c_devices:  # SH1106
            self.screen_config = {
                'type': 'SH1106',
                'width': 128,
                'height': 64,
                'color_depth': 1,
                'address': 0x78
            }
        
        else:
            self.screen_config = {
                'type': 'GENERIC',
                'width': 128,
                'height': 64,
                'color_depth': 1
            }
        
        self.detected_devices['screen'] = self.screen_config
        return self.screen_config
    
    def detect_all(self):
        """Определяет всё оборудование"""
        self.detect_i2c_devices()
        self.detect_screen()
        self.detect_camera()
        return self.detected_devices

hardware = HardwareDetector()

# ============================================
# АДАПТИВНЫЙ ДРАЙВЕР ЭКРАНА
# ============================================

class AdaptiveDisplayDriver:
    """Универсальный драйвер экрана для любого разрешения"""
    
    def __init__(self, config=None):
        if config is None:
            config = hardware.screen_config
        
        self.type = config.get('type', 'SSD1306')
        self.width = config.get('width', 128)
        self.height = config.get('height', 64)
        self.color_depth = config.get('color_depth', 1)
        self.address = config.get('address', 0x3c)
        
        self.buffer = bytearray((self.width * self.height) // 8)
        self.init_display()
    
    def init_display(self):
        """Инициализирует дисплей"""
        try:
            if self.type == 'SSD1306':
                self._init_ssd1306()
            elif self.type == 'SH1106':
                self._init_sh1106()
        except Exception as e:
            print(f"Display init error: {e}")
    
    def _init_ssd1306(self):
        """Инициализация SSD1306"""
        self.i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
        
        init_cmds = [
            0xae,        # Display OFF
            0x20, 0x00,  # Memory mode
            0x40,        # Start line
            0x81, 0xcf,  # Contrast
            0xa1,        # Segment remap
            0xa6,        # Normal display
            0xa8, self.height - 1,  # Multiplex ratio
            0xd3, 0x00,  # Display offset
            0xd5, 0x80,  # Clock div
            0xd9, 0xf1,  # Precharge
            0xda, 0x12 if self.height == 32 else 0x12,  # COM decscan
            0xdb, 0x40,  # Vcomdetect
            0x8d, 0x14,  # Charge pump
            0xaf,        # Display ON
        ]
        
        for cmd in init_cmds:
            self.i2c.writeto(self.address, bytes([0x00, cmd]))
    
    def _init_sh1106(self):
        """Инициализация SH1106"""
        self.i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
        # SH1106 инициализация (похожа на SSD1306)
        self._init_ssd1306()
    
    def fill(self, color):
        """Заполняет весь буфер"""
        self.buffer[:] = (0xff if color else 0x00) * len(self.buffer)
    
    def pixel(self, x, y, color):
        """Устанавливает пиксель"""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = (y // 8) * self.width + x
            if color:
                self.buffer[index] |= (1 << (y % 8))
            else:
                self.buffer[index] &= ~(1 << (y % 8))
    
    def text(self, string, x, y, color):
        """Выводит текст с автоматическим масштабированием"""
        font_width = 6
        for i, char in enumerate(string):
            if x + (i + 1) * font_width > self.width:
                break
            self._draw_char(char, x + i * font_width, y, color)
    
    def _draw_char(self, char, x, y, color):
        """Рисует один символ"""
        # Простой 5x7 ASCII шрифт
        fonts = {
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
            'A': [0x7e, 0x89, 0x89, 0x89, 0x7e],
            'B': [0xff, 0x89, 0x99, 0xa5, 0x42],
            'C': [0x7e, 0x81, 0x81, 0x81, 0x42],
            '0': [0x7e, 0x81, 0x81, 0x81, 0x7e],
            '1': [0x00, 0x41, 0xff, 0x01, 0x00],
        }
        
        if char not in fonts:
            char = ' '
        
        pattern = fonts[char]
        for i, byte in enumerate(pattern):
            for bit in range(8):
                if byte & (1 << bit):
                    self.pixel(x + i, y + bit, color)
    
    def show(self):
        """Отображает буфер на экране"""
        if self.type == 'SSD1306':
            self._show_ssd1306()
    
    def _show_ssd1306(self):
        """Отправляет буфер на SSD1306"""
        pages = self.height // 8
        for page in range(pages):
            self.i2c.writeto(self.address, bytes([0x00, 0xb0 | page, 0x00, 0x10]))
            data = b'\x40' + self.buffer[page * self.width:(page + 1) * self.width]
            self.i2c.writeto(self.address, data)
    
    def get_resolution(self):
        """Возвращает разрешение"""
        return (self.width, self.height)

display_driver = AdaptiveDisplayDriver()

# ============================================
# АДАПТИВНЫЙ ДРАЙВЕР КАМЕРЫ
# ============================================

class AdaptiveCameraDriver:
    """Универсальный драйвер камеры"""
    
    def __init__(self):
        self.camera_type = hardware.camera_type
        self.is_available = self.camera_type is not None
        self.current_resolution = None
        self.current_quality = 100
        
        if self.is_available:
            self.init_camera()
    
    def init_camera(self):
        """Инициализирует камеру"""
        try:
            import camera
            
            if self.camera_type == "OV2640":
                camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
                camera.framesize(camera.FRAME_SVGA)
                self.current_resolution = (800, 600)
            
            elif self.camera_type == "OV7670":
                camera.init(0, format=camera.RGB565)
                camera.framesize(camera.FRAME_VGA)
                self.current_resolution = (640, 480)
            
            print(f"Camera initialized: {self.camera_type}")
        except Exception as e:
            print(f"Camera init error: {e}")
            self.is_available = False
    
    def set_resolution(self, width, height):
        """Устанавливает разрешение"""
        if not self.is_available:
            return False
        
        try:
            import camera
            
            if width <= 160 and height <= 120:
                camera.framesize(camera.FRAME_QQVGA)
            elif width <= 320 and height <= 240:
                camera.framesize(camera.FRAME_QVGA)
            elif width <= 640 and height <= 480:
                camera.framesize(camera.FRAME_VGA)
            else:
                camera.framesize(camera.FRAME_SVGA)
            
            self.current_resolution = (width, height)
            return True
        except:
            return False
    
    def set_quality(self, quality):
        """Устанавливает качество (0-100)"""
        if not self.is_available:
            return False
        
        try:
            import camera
            quality = max(0, min(100, quality))
            camera.quality(quality)
            self.current_quality = quality
            return True
        except:
            return False
    
    def capture(self):
        """Захватывает кадр"""
        if not self.is_available:
            return None
        
        try:
            import camera
            buf = camera.capture()
            return buf
        except:
            return None

camera_driver = AdaptiveCameraDriver()

# ============================================
# АДАПТИВНЫЙ ДРАЙВЕР ПРОЦЕССОРА
# ============================================

class AdaptiveProcessorDriver:
    """Управление процессором и памятью"""
    
    def __init__(self):
        self.max_freq = 240
        self.min_freq = 80
        self.current_freq = machine.freq()[0] // 1000000
        self.power_modes = {
            'LowPower': 80,
            'Normal': 160,
            'Performance': 240
        }
    
    def set_frequency(self, freq_mhz):
        """Устанавливает частоту процессора"""
        freq_mhz = max(self.min_freq, min(self.max_freq, freq_mhz))
        machine.freq(freq_mhz * 1000000)
        self.current_freq = freq_mhz
        return freq_mhz
    
    def set_power_mode(self, mode):
        """Устанавливает режим питания"""
        if mode in self.power_modes:
            freq = self.power_modes[mode]
            self.set_frequency(freq)
            return True
        return False
    
    def get_cpu_freq(self):
        """Получает текущую частоту"""
        return machine.freq()[0] // 1000000
    
    def get_ram_free(self):
        """Получает свободную память"""
        import gc
        return gc.mem_free()
    
    def get_ram_used(self):
        """Получает использованную память"""
        import gc
        return gc.mem_alloc()
    
    def optimize_memory(self):
        """Оптимизирует память"""
        import gc
        gc.collect()
        return self.get_ram_free()

processor_driver = AdaptiveProcessorDriver()

# ============================================
# АДАПТИВНЫЙ ДРАЙВЕР МОДУЛЕЙ
# ============================================

class AdaptiveModuleDriver:
    """Управление подключаемыми модулями"""
    
    def __init__(self):
        self.modules = {
            'WiFi': {'enabled': True, 'power': 'auto'},
            'Bluetooth': {'enabled': True, 'power': 'auto'},
            'USB': {'enabled': True, 'power': 'auto'},
            'SPI': {'enabled': True, 'power': 'auto'},
            'I2C': {'enabled': True, 'power': 'auto'},
            'GPIO': {'enabled': True, 'power': 'auto'},
            'ADC': {'enabled': True, 'power': 'auto'},
            'Camera': {'enabled': camera_driver.is_available, 'power': 'auto'},
        }
        self.load_config()
    
    def load_config(self):
        """Загружает конфиг модулей"""
        try:
            if '/modules_config.json' in os.listdir('/'):
                with open('/modules_config.json', 'r') as f:
                    config = json.load(f)
                    self.modules.update(config)
        except:
            pass
    
    def save_config(self):
        """Сохраняет конфиг модулей"""
        try:
            with open('/modules_config.json', 'w') as f:
                json.dump(self.modules, f)
        except:
            pass
    
    def enable_module(self, module_name):
        """Включает модуль"""
        if module_name in self.modules:
            self.modules[module_name]['enabled'] = True
            self.save_config()
            return True
        return False
    
    def disable_module(self, module_name):
        """Отключает модуль"""
        if module_name in self.modules:
            self.modules[module_name]['enabled'] = False
            self.save_config()
            return True
        return False
    
    def get_module_status(self, module_name):
        """Получает статус модуля"""
        if module_name in self.modules:
            return self.modules[module_name]['enabled']
        return False

modules_driver = AdaptiveModuleDriver()

# ============================================
# АДАПТИВНЫЙ ДРАЙВЕР ЭКРАНА (для телефона)
# ============================================

class ResponsiveDisplay:
    """Отзывчивый дизайн экрана (как на телефоне)"""
    
    def __init__(self, display_driver):
        self.driver = display_driver
        self.width = display_driver.width
        self.height = display_driver.height
        self.safe_area = self._calculate_safe_area()
    
    def _calculate_safe_area(self):
        """Вычисляет безопасную зону экрана"""
        margin = 2
        return {
            'x': margin,
            'y': margin,
            'width': self.width - 2 * margin,
            'height': self.height - 2 * margin
        }
    
    def draw_status_bar(self, time_str, signal, battery):
        """Рисует строку статуса (как на телефоне)"""
        # Очищаем область
        for y in range(12):
            for x in range(self.width):
                self.driver.pixel(x, y, 0)
        
        # Время слева
        self.driver.text(time_str, 2, 2, 1)
        
        # Сигнал в центре
        self.driver.text(signal, self.width // 2 - 10, 2, 1)
        
        # Батарея справа
        self.driver.text(f"Bat:{battery}%", self.width - 35, 2, 1)
        
        # Линия разделитель
        for x in range(self.width):
            self.driver.pixel(x, 12, 1)
    
    def draw_menu_item(self, y, text, selected, icon=""):
        """Рисует пункт меню"""
        height = 11
        
        if selected:
            # Подсветка
            for xx in range(self.width):
                for yy in range(height):
                    self.driver.pixel(xx, y + yy, 1)
            # Текст инверсный
            self.driver.text(f"{icon}{text}", 15, y + 2, 0)
        else:
            self.driver.text(f" {icon}{text}", 15, y + 2, 1)
    
    def draw_progress_bar(self, x, y, width, height, progress):
        """Рисует прогресс-бар"""
        # Контур
        for xx in range(width):
            self.driver.pixel(x + xx, y, 1)
            self.driver.pixel(x + xx, y + height - 1, 1)
        for yy in range(height):
            self.driver.pixel(x, y + yy, 1)
            self.driver.pixel(x + width - 1, y + yy, 1)
        
        # Заполнение
        fill_width = int((progress / 100) * (width - 2))
        for xx in range(fill_width):
            for yy in range(1, height - 1):
                self.driver.pixel(x + 1 + xx, y + yy, 1)
    
    def draw_notification(self, title, message):
        """Рисует уведомление (как попап на телефоне)"""
        self.driver.fill(0)
        
        # Заголовок
        self.driver.text(title, 20, 10, 1)
        
        # Сообщение
        self.driver.text(message[:20], 15, 25, 1)
        
        self.driver.show()

responsive_display = ResponsiveDisplay(display_driver)

# ============================================
# КОНФИГ СЕНСОРА/БАТАРЕИ
# ============================================

class AdaptiveSensorDriver:
    """Адаптивный драйвер сенсоров"""
    
    def __init__(self):
        self.battery_pin = None
        self.imu_available = False
        self.temp_sensor_available = False
        
        self._init_sensors()
    
    def _init_sensors(self):
        """Инициализирует сенсоры"""
        # Батарея
        try:
            self.battery_pin = machine.ADC(machine.Pin(35))
            self.battery_pin.atten(machine.ADC.ATTN_11DB)
        except:
            pass
        
        # IMU (MPU6050)
        if 0x68 in hardware.detected_devices.get('i2c', {}):
            self.imu_available = True
        
        # Температурный сенсор
        if 0x77 in hardware.detected_devices.get('i2c', {}):
            self.temp_sensor_available = True
    
    def get_battery_level(self):
        """Получает уровень батареи"""
        if not self.battery_pin:
            return 100
        
        try:
            adc_value = self.battery_pin.read()
            # Преобразование: 0-4095 → 0-100%
            voltage = (adc_value / 4095) * 3.3
            battery_percent = max(0, min(100, int((voltage - 2.5) / 1.7 * 100)))
            return battery_percent
        except:
            return 100
    
    def get_temperature(self):
        """Получает температуру (если доступно)"""
        if not self.temp_sensor_available:
            return None
        
        try:
            # BMP280 temperature
            return 25  # Placeholder
        except:
            return None

sensors_driver = AdaptiveSensorDriver()

# ============================================
# ГЛАВНЫЙ КЛАСС ДРАЙВЕРОВ
# ============================================

class BitosDrivers:
    """Главный класс всех адаптивных драйверов"""
    
    def __init__(self):
        self.display = display_driver
        self.camera = camera_driver
        self.processor = processor_driver
        self.modules = modules_driver
        self.sensors = sensors_driver
        self.responsive = responsive_display
        self.hardware = hardware
    
    def get_system_info(self):
        """Получает полную информацию о системе"""
        return {
            'hardware': self.hardware.detected_devices,
            'display': {
                'type': self.display.type,
                'resolution': self.display.get_resolution()
            },
            'camera': self.camera.camera_type,
            'processor': {
                'frequency': self.processor.get_cpu_freq(),
                'ram_free': self.processor.get_ram_free(),
                'ram_used': self.processor.get_ram_used()
            },
            'battery': self.sensors.get_battery_level(),
            'modules': self.modules.modules
        }
    
    def print_info(self):
        """Выводит информацию о системе"""
        info = self.get_system_info()
        print("\n=== BITOS SYSTEM INFO ===")
        print(f"Display: {info['display']['type']} {info['display']['resolution']}")
        print(f"Camera: {info['camera']}")
        print(f"CPU Freq: {info['processor']['frequency']} MHz")
        print(f"RAM Free: {info['processor']['ram_free']} bytes")
        print(f"Battery: {info['battery']}%")
        print("========================\n")

# Глобальный экземпляр
drivers = BitosDrivers()

# Выводим информацию при загрузке
drivers.print_info()
