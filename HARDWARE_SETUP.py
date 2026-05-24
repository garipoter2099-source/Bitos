"""
Bitos OS - Hardware Setup & Drivers
Инструкция по подключению и установке драйверов
"""

# ============================================
# ИНСТРУКЦИЯ ПО ПОДКЛЮЧЕНИЮ АППАРАТУРЫ
# ============================================

"""
НЕОБХОДИМЫЕ КОМПОНЕНТЫ:
========================

1. ESP32 Development Board (30-pin or 36-pin)
2. SSD1306 OLED Display 128x64 (I2C)
3. 4 кнопки (Push Buttons)
4. 1 LED (3mm, любой цвет)
5. 1 Динамик (8Ω, 0.5W)
6. Резисторы: 10kΩ (4шт), 220Ω (1шт)
7. Конденсаторы: 100µF, 10µF (опционально)
8. USB кабель для программирования
9. Макетная плата (breadboard)
10. Провода (jumper wires)

ЭЛЕКТРОСХЕМА:
=============

ДИСПЛЕЙ SSD1306 (I2C):
┌─────────────┐
│ SSD1306     │
├─────────────┤
│ VCC  ──────→ 3.3V (ESP32)
│ GND  ──────→ GND (ESP32)
│ SCL  ──────→ GPIO22 (ESP32)
│ SDA  ──────→ GPIO21 (ESP32)
└─────────────┘

КНОПКИ (с Pull-Up резисторами 10kΩ к 3.3V):
┌──────────────┐
│ BUTTON_UP    │──┬──→ GPIO32
│              │  │
│              │ 10kΩ ──→ 3.3V
│              │  │
│              │ GND ──→ GND
└──────────────┘

┌──────────────┐
│ BUTTON_DOWN  │──┬──→ GPIO33
│              │  │
│              │ 10kΩ ──→ 3.3V
│              │  │
│              │ GND ──→ GND
└──────────────┘

┌──────────────┐
│ BUTTON_SEL   │──┬──→ GPIO25
│              │  │
│              │ 10kΩ ──→ 3.3V
│              │  │
│              │ GND ──→ GND
└──────────────┘

┌──────────────┐
│ BUTTON_BACK  │──┬──→ GPIO26
│              │  │
│              │ 10kΩ ──→ 3.3V
│              │  │
│              │ GND ──→ GND
└──────────────┘

LED:
┌──────┐
│ LED+ │──→ 220Ω резистор ──→ GPIO2
│ LED- │──────────────────→ GND
└──────┘

ДИНАМИК:
┌──────────┐
│ SPEAKER+ │──→ GPIO27 (PWM)
│ SPEAKER- │──→ GND
└──────────┘

БАТАРЕЯ (опционально):
┌──────────┐
│ BAT+ (4V)│──→ GPIO35 (ADC)
│ BAT- (0V)│──→ GND
└──────────┘

ТАБЛИЦА ПОДКЛЮЧЕНИЙ:
====================

ESP32 PIN | КОМПОНЕНТ        | НАЗНАЧЕНИЕ
----------|------------------|----------------------
GPIO21    | SSD1306 SDA      | I2C Data
GPIO22    | SSD1306 SCL      | I2C Clock
GPIO32    | Button UP        | Вверх по меню
GPIO33    | Button DOWN      | Вниз по меню
GPIO25    | Button SELECT    | Выбрать
GPIO26    | Button BACK      | Назад
GPIO27    | Speaker          | Звук (PWM)
GPIO2     | LED              | Индикатор
GPIO35    | Battery ADC      | Уровень батареи
3.3V      | VCC (все)        | Питание
GND       | GND (все)        | Земля

УСТАНОВКА НА МАКЕТНОЙ ПЛАТЕ:
============================

1. Установить ESP32 в центр макетной платы
2. Подключить дисплей SSD1306 по I2C (GPIO21, GPIO22)
3. Установить 4 кнопки с резисторами 10kΩ к 3.3V
4. Подключить LED с резистором 220Ω к GPIO2
5. Подключить динамик к GPIO27
6. Опционально: подключить батарею к GPIO35 через делитель напряжения
7. Убедиться, что все GND подключены к общей земле
"""

# ============================================
# УСТАНОВКА ДРАЙВЕРОВ И ЗАВИСИМОСТЕЙ
# ============================================

"""
ШАГИ УСТАНОВКИ:
================

1. УСТАНОВКА MICROPYTHON НА ESP32:
   
   # Скачать последнюю версию MicroPython для ESP32
   wget https://micropython.org/download/esp32/
   
   # Стереть флэш память
   esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
   
   # Прошить MicroPython
   esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 \
   esp32-20230426-v1.20.0.bin

2. УСТАНОВКА НЕОБХОДИМЫХ БИБЛИОТЕК:
   
   # Установить ampy для загрузки файлов
   pip install adafruit-ampy
   
   # Или используйте WebREPL для загрузки

3. ЗАГРУЗКА ДРАЙВЕРА SSD1306:
   
   # Скачать драйвер SSD1306
   wget https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_SSD1306/main/adafruit_ssd1306.py
   
   # Загрузить на ESP32
   ampy --port /dev/ttyUSB0 put adafruit_ssd1306.py
   ampy --port /dev/ttyUSB0 put ssd1306.py

4. ЗАГРУЗКА ГЛАВНОЙ ОС:
   
   ampy --port /dev/ttyUSB0 put bitos_complete.py
   ampy --port /dev/ttyUSB0 put boot.py

5. ЗАПУСК:
   
   # Перезагрузить ESP32
   ampy --port /dev/ttyUSB0 run bitos_complete.py
"""

# ============================================
# ДРАЙВЕР SSD1306 (128x64)
# ============================================

"""
Оптимизированный драйвер для SSD1306 OLED дисплея
"""

class SSD1306:
    def __init__(self, width, height, i2c, addr=0x3c):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pixel_rate = 1
        self.pages = self.height // 8
        self.buf = bytearray(self.pages * self.width)
        self.init_display()

    def init_display(self):
        """Инициализирует дисплей"""
        for cmd in (
            0xae,        # SSD1306_DISPLAYOFF
            0x20, 0x00,  # SSD1306_MEMORYMODE
            0x40,        # SSD1306_STARTSCANLINE
            0x81, 0xcf,  # SSD1306_SETCONTRAST
            0xa1,        # SSD1306_SEGREMAP
            0xa6,        # SSD1306_NORMALDISPLAY
            0xa8, 0x3f,  # SSD1306_SETMULTIPLEX
            0xd3, 0x00,  # SSD1306_DISPLAYOFFSET
            0xd5, 0x80,  # SSD1306_SETCLOCKDIV
            0xd9, 0xf1,  # SSD1306_SETPRECHARGE
            0xda, 0x12,  # SSD1306_SETCOMDECSCAN
            0xdb, 0x40,  # SSD1306_SETVCOMDETECT
            0x8d, 0x14,  # SSD1306_CHARGEPUMP
            0xaf,        # SSD1306_DISPLAYON
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def write_cmd(self, cmd):
        """Отправляет команду на дисплей"""
        self.i2c.writeto(self.addr, b'\x00' + bytes([cmd]))

    def write_data(self, buf):
        """Отправляет данные на дисплей"""
        self.i2c.writeto(self.addr, b'\x40' + buf)

    def show(self):
        """Отображает буфер на экране"""
        for page in range(self.pages):
            self.write_cmd(0xb0 | page)
            self.write_cmd(0x00)
            self.write_cmd(0x10)
            self.write_data(self.buf[page * self.width:(page + 1) * self.width])

    def fill(self, col):
        """Заполняет весь экран цветом"""
        self.buf[:] = (0xff if col else 0x00) * len(self.buf)

    def pixel(self, x, y, col):
        """Устанавливает пиксель"""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = (y // 8) * self.width + x
            if col:
                self.buf[index] |= (1 << (y % 8))
            else:
                self.buf[index] &= ~(1 << (y % 8))

    def hline(self, x, y, w, col):
        """Рисует горизонтальную линию"""
        for i in range(w):
            self.pixel(x + i, y, col)

    def vline(self, x, y, h, col):
        """Рисует вертикальную линию"""
        for i in range(h):
            self.pixel(x, y + i, col)

    def line(self, x1, y1, x2, y2, col):
        """Рисует линию (Bresenham)"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            self.pixel(x1, y1, col)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def rect(self, x, y, w, h, col):
        """Рисует прямоугольник"""
        self.hline(x, y, w, col)
        self.hline(x, y + h - 1, w, col)
        self.vline(x, y, h, col)
        self.vline(x + w - 1, y, h, col)

    def fill_rect(self, x, y, w, h, col):
        """Рисует заполненный прямоугольник"""
        for i in range(h):
            self.hline(x, y + i, w, col)

    def text(self, string, x, y, col):
        """Выводит текст (5x8 шрифт)"""
        for char in string:
            self.char(char, x, y, col)
            x += 6

    def char(self, char, x, y, col):
        """Выводит один символ"""
        # Простой 5x7 шрифт
        font = {
            ' ': b'\x00\x00\x00\x00\x00',
            '0': b'\x7e\x81\x81\x81\x7e',
            '1': b'\x00\x41\xff\x01\x00',
            '2': b'\x83\x85\x89\x91\x61',
            '3': b'\x81\x89\x95\xa5\x43',
            '4': b'\x0c\x14\x24\xff\x04',
            '5': b'\xf9\x89\x89\x89\x79',
            '6': b'\x3e\x49\x89\x89\x06',
            '7': b'\x80\x8f\x90\xa0\xc0',
            '8': b'\x66\x99\x99\x99\x66',
            '9': b'\x60\x99\x99\x99\x7e',
            'A': b'\x7e\x89\x89\x89\x7e',
            'B': b'\xff\x89\x99\xa5\x42',
            'C': b'\x7e\x81\x81\x81\x42',
            'D': b'\xff\x81\x81\x81\x7e',
            'E': b'\xff\x89\x89\x89\x81',
            'F': b'\xff\x88\x88\x88\x80',
        }
        
        if char not in font:
            return
        
        char_data = font[char]
        for i, byte in enumerate(char_data):
            for bit in range(8):
                if byte & (1 << bit):
                    self.pixel(x + i, y + bit, col)

# ============================================
# КОНФИГУРАЦИЯ РАЗРЕШЕНИЯ ЭКРАНА
# ============================================

DISPLAY_CONFIG = {
    'width': 128,
    'height': 64,
    'i2c_scl': 22,
    'i2c_sda': 21,
    'i2c_freq': 400000,  # 400 kHz
    'i2c_addr': 0x3c,    # или 0x3d
}

# ============================================
# ИНИЦИАЛИЗАЦИЯ ДИСПЛЕЯ
# ============================================

def init_display():
    """Инициализирует дисплей с правильными параметрами"""
    import machine
    from ssd1306 import SSD1306_I2C
    
    # Инициализируем I2C на правильных пинах
    i2c = machine.I2C(
        scl=machine.Pin(DISPLAY_CONFIG['i2c_scl']),
        sda=machine.Pin(DISPLAY_CONFIG['i2c_sda']),
        freq=DISPLAY_CONFIG['i2c_freq']
    )
    
    # Проверяем подключение дисплея
    devices = i2c.scan()
    if DISPLAY_CONFIG['i2c_addr'] not in devices:
        print(f"WARNING: Display not found at 0x{DISPLAY_CONFIG['i2c_addr']:02x}")
        print(f"Found devices: {[hex(d) for d in devices]}")
    
    # Инициализируем дисплей
    display = SSD1306_I2C(
        DISPLAY_CONFIG['width'],
        DISPLAY_CONFIG['height'],
        i2c,
        addr=DISPLAY_CONFIG['i2c_addr']
    )
    
    return display

# ============================================
# ТЕСТ ДИСПЛЕЯ
# ============================================

def test_display():
    """Тестирует дисплей"""
    display = init_display()
    
    # Тест 1: Заполнение
    print("Test 1: Fill...")
    display.fill(1)
    display.show()
    time.sleep(1)
    display.fill(0)
    display.show()
    
    # Тест 2: Прямоугольники
    print("Test 2: Rectangles...")
    display.rect(10, 10, 50, 30, 1)
    display.rect(70, 10, 50, 30, 1)
    display.show()
    time.sleep(1)
    display.fill(0)
    
    # Тест 3: Линии
    print("Test 3: Lines...")
    display.hline(0, 20, 128, 1)
    display.vline(64, 0, 64, 1)
    display.show()
    time.sleep(1)
    display.fill(0)
    
    # Тест 4: Текст
    print("Test 4: Text...")
    display.text("BITOS OS v2.0", 20, 10, 1)
    display.text("Display Test OK", 15, 30, 1)
    display.text("128x64 OLED", 30, 50, 1)
    display.show()
    time.sleep(2)
    display.fill(0)
    
    print("All tests completed!")

# ============================================
# КАЛИБРОВКА КНОПОК
# ============================================

def test_buttons():
    """Тестирует кнопки"""
    from machine import Pin
    import time
    
    buttons = {
        'UP': Pin(32, Pin.IN, Pin.PULL_UP),
        'DOWN': Pin(33, Pin.IN, Pin.PULL_UP),
        'SELECT': Pin(25, Pin.IN, Pin.PULL_UP),
        'BACK': Pin(26, Pin.IN, Pin.PULL_UP),
    }
    
    print("Button test started. Press any button...")
    start = time.time()
    
    while time.time() - start < 30:  # 30 секунд
        for name, btn in buttons.items():
            if not btn.value():  # Кнопка нажата (LOW)
                print(f"Button {name} pressed!")
                time.sleep(0.3)  # Debounce
        time.sleep(0.1)
    
    print("Button test completed!")

# ============================================
# ШПАРГАЛКА ПО ПОДКЛЮЧЕНИЮ
# ============================================

"""
ЧЕКЛИСТ ПОДКЛЮЧЕНИЯ:
====================

□ ESP32 подключена к USB
□ SSD1306 подключен на GPIO21 (SDA) и GPIO22 (SCL)
□ Все 4 кнопки подключены (GPIO32, 33, 25, 26)
□ LED подключен на GPIO2
□ Динамик подключен на GPIO27
□ Батарея (опционально) подключена на GPIO35
□ Все земли объединены

ТИПИЧНЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ:
============================

1. Дисплей не работает:
   - Проверить адрес I2C (0x3c или 0x3d)
   - Проверить контакты SCL/SDA
   - Проверить напряжение 3.3V

2. Кнопки не реагируют:
   - Проверить резисторы pull-up 10kΩ
   - Проверить контакты GPIO
   - Проверить, не перепутаны ли пины

3. Динамик не звучит:
   - Проверить подключение на GPIO27
   - Проверить, включена ли PWM
   - Проверить громкость в настройках

4. LED не светит:
   - Проверить полярность (+ на GPIO2, - на GND)
   - Проверить резистор 220Ω
   - Проверить GPIO2 на спецификации платы

ПОЛЕЗНЫЕ КОМАНДЫ:
=================

# Проверить подключение I2C устройств
ampy --port /dev/ttyUSB0 run -c "
import machine
i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
print('I2C devices:', [hex(x) for x in i2c.scan()])
"

# Проверить GPIO
ampy --port /dev/ttyUSB0 run -c "
from machine import Pin
btn = Pin(32, Pin.IN, Pin.PULL_UP)
print('GPIO32 value:', btn.value())
"

# Проверить батарею
ampy --port /dev/ttyUSB0 run -c "
from machine import ADC, Pin
adc = ADC(Pin(35))
print('Battery ADC:', adc.read())
"
"""
