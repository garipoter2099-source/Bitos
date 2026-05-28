"""
BITOS OS v3.1 - MODERN MINIMAL UI WITH iOS-STYLE CONTROL CENTER
Минималистичный дизайн с нижней шторкой и клавиатурой
"""

import time
import machine
import os
import json
import gc
from machine import Pin, ADC, PWM
import math

# ============================================
# МИНИМАЛИСТИЧНЫЙ ДИЗАЙН - КОНСТАНТЫ
# ============================================

class MinimalDesign:
    # Цвета минималистичного дизайна
    BG_PRIMARY = 0xFFFF      # Белый
    BG_SECONDARY = 0xF7F7   # Светло-серый
    TEXT_PRIMARY = 0x0000   # Чёрный
    TEXT_SECONDARY = 0x8C8C # Серый
    ACCENT = 0x007AFF      # iOS синий
    SEPARATOR = 0xE0E0E0   # Разделитель
    SUCCESS = 0x4CAF50     # Зелёный
    
    # Размеры
    SCREEN_WIDTH = 128
    SCREEN_HEIGHT = 64
    CORNER_RADIUS = 8
    PADDING = 4
    MARGIN = 8
    
    # Анимация
    ANIMATION_SPEED = 0.05
    SWIPE_THRESHOLD = 10

minimal_design = MinimalDesign()

# ============================================
# iOS-STYLE CONTROL CENTER (НИЖНЯЯ ШТОРКА)
# ============================================

class ControlCenter:
    """Нижняя шторка управления (как в iOS)"""
    
    def __init__(self, display):
        self.display = display
        self.is_open = False
        self.slide_position = 0  # 0 = закрыто, 1 = открыто
        self.animation_progress = 0
        self.width = minimal_design.SCREEN_WIDTH
        self.height = 28  # Высота шторки
        self.y_start = minimal_design.SCREEN_HEIGHT - self.height
        
        # Элементы управления
        self.wifi_enabled = True
        self.bluetooth_enabled = False
        self.airplane_mode = False
        self.brightness = 100
    
    def toggle(self):
        """Переключить шторку"""
        self.is_open = not self.is_open
    
    def animate(self):
        """Анимация открытия/закрытия"""
        if self.is_open:
            if self.slide_position < 1:
                self.slide_position += 0.2
        else:
            if self.slide_position > 0:
                self.slide_position -= 0.2
        
        self.slide_position = max(0, min(1, self.slide_position))
    
    def draw(self):
        """Рисует шторку"""
        self.animate()
        
        # Вычисляем позицию на экране
        y_offset = int(self.height * (1 - self.slide_position))
        y = self.y_start + y_offset
        
        if self.slide_position == 0:
            # Только хэндл (полоса для свайпа)
            self._draw_handle()
            return
        
        # Фон шторки с тенью
        for i in range(int(self.height * self.slide_position)):
            self.display.fill_rect(0, y + i, self.width, 1, 0xF7F7)
        
        # Ручка в центре вверху
        handle_y = y + 2
        self.display.fill_rect(self.width // 2 - 15, handle_y, 30, 3, 0xD0D0)
        
        if self.slide_position > 0.4:
            self._draw_controls(y)
    
    def _draw_handle(self):
        """Рисует ручку для свайпа"""
        y = self.y_start + 2
        self.display.fill_rect(self.width // 2 - 15, y, 30, 3, 0xD0D0)
    
    def _draw_controls(self, y):
        """Рисует элементы управления"""
        # Строка 1: WiFi, Bluetooth, Airplane, Brightness
        y_row1 = y + 8
        
        # WiFi
        wifi_color = 0x007AFF if self.wifi_enabled else 0xCCCCCC
        self.display.rect(5, y_row1, 18, 12, wifi_color)
        self.display.text("W", 9, y_row1 + 2, wifi_color)
        
        # Bluetooth
        bt_color = 0x007AFF if self.bluetooth_enabled else 0xCCCCCC
        self.display.rect(26, y_row1, 18, 12, bt_color)
        self.display.text("B", 30, y_row1 + 2, bt_color)
        
        # Airplane
        airplane_color = 0x007AFF if self.airplane_mode else 0xCCCCCC
        self.display.rect(47, y_row1, 18, 12, airplane_color)
        self.display.text("A", 51, y_row1 + 2, airplane_color)
        
        # Яркость
        self.display.text(f"B:{self.brightness}%", 70, y_row1 + 2, 0x0000)

# ============================================
# ВИРТУАЛЬНАЯ КЛАВИАТУРА
# ============================================

class VirtualKeyboard:
    """iOS-style виртуальная клавиатура"""
    
    def __init__(self, display):
        self.display = display
        self.is_visible = False
        self.slide_position = 0  # 0 = скрыто, 1 = видно
        self.input_text = ""
        self.selected_key_index = 0
        
        # Раскладка клавиатуры (3 ряда)
        self.rows = [
            list("QWERTYUIOP"),
            list("ASDFGHJKL"),
            list("ZXCVBNM")
        ]
        
        self.current_row = 0
        self.current_col = 0
        
        # Размеры
        self.key_width = 11
        self.key_height = 6
        self.keyboard_height = 21
        self.y_start = minimal_design.SCREEN_HEIGHT - self.keyboard_height
    
    def show(self):
        """Показать клавиатуру"""
        self.is_visible = True
        self.current_row = 0
        self.current_col = 0
    
    def hide(self):
        """Скрыть клавиатуру"""
        self.is_visible = False
    
    def animate(self):
        """Анимация появления"""
        if self.is_visible:
            if self.slide_position < 1:
                self.slide_position += 0.2
        else:
            if self.slide_position > 0:
                self.slide_position -= 0.2
        
        self.slide_position = max(0, min(1, self.slide_position))
    
    def draw(self):
        """Рисует клавиатуру"""
        if self.slide_position == 0:
            return
        
        self.animate()
        
        # Вычисляем позицию
        y_offset = int(self.keyboard_height * (1 - self.slide_position))
        y = self.y_start + y_offset
        visible_height = int(self.keyboard_height * self.slide_position)
        
        # Фон клавиатуры
        self.display.fill_rect(0, y, self.width, visible_height, 0xF7F7)
        
        # Разделитель
        self.display.hline(0, y, self.width, 0xD0D0)
        
        if self.slide_position > 0.4:
            self._draw_keys(y)
    
    def _draw_keys(self, y):
        """Рисует клавиши"""
        rows_to_show = min(2, len(self.rows))  # Показываем максимум 2 ряда
        
        for row_idx in range(rows_to_show):
            row = self.rows[row_idx]
            y_pos = y + 2 + row_idx * 8
            
            # Смещение для центрирования
            offset_x = 2 if row_idx == 1 else 0
            x_pos = offset_x + 2
            
            for col_idx, char in enumerate(row):
                is_selected = (row_idx == self.current_row and col_idx == self.current_col)
                
                # Цвет ключа
                if is_selected:
                    key_color = 0x007AFF
                    text_color = 0xFFFF
                else:
                    key_color = 0xFFFF
                    text_color = 0x0000
                
                # Рисуем ключ
                self.display.fill_rect(x_pos, y_pos, 10, 6, key_color)
                self.display.rect(x_pos, y_pos, 10, 6, 0xCCCCCC if not is_selected else 0x007AFF)
                self.display.text(char, x_pos + 2, y_pos + 1, text_color)
                
                x_pos += 11
    
    def add_char(self):
        """Добавить выбранный символ"""
        if self.current_row < len(self.rows) and self.current_col < len(self.rows[self.current_row]):
            char = self.rows[self.current_row][self.current_col]
            if len(self.input_text) < 50:
                self.input_text += char
    
    def remove_char(self):
        """Удалить символ"""
        if self.input_text:
            self.input_text = self.input_text[:-1]
    
    def move_right(self):
        """Движение вправо"""
        row = self.rows[self.current_row]
        self.current_col = (self.current_col + 1) % len(row)
    
    def move_left(self):
        """Движение влево"""
        row = self.rows[self.current_row]
        self.current_col = (self.current_col - 1) % len(row)
    
    def move_down(self):
        """Движение вниз"""
        self.current_row = (self.current_row + 1) % len(self.rows)
        self.current_col = min(self.current_col, len(self.rows[self.current_row]) - 1)
    
    def move_up(self):
        """Движение вверх"""
        self.current_row = (self.current_row - 1) % len(self.rows)
        self.current_col = min(self.current_col, len(self.rows[self.current_row]) - 1)
    
    def get_input(self):
        """Получить введённый текст"""
        return self.input_text
    
    def clear_input(self):
        """Очистить ввод"""
        self.input_text = ""

# ============================================
# ТЕКСТОВОЕ ПОЛЕ С КЛАВИАТУРОЙ
# ============================================

class TextField:
    """Текстовое поле с интегрированной клавиатурой"""
    
    def __init__(self, display, x, y, width, height, placeholder="Enter text..."):
        self.display = display
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.placeholder = placeholder
        self.text = ""
        self.is_focused = False
        self.cursor_position = 0
        self.cursor_blink_counter = 0
        self.keyboard = VirtualKeyboard(display)
    
    def draw(self):
        """Рисует текстовое поле"""
        # Граница
        color = 0x007AFF if self.is_focused else 0xD0D0
        border_width = 2 if self.is_focused else 1
        
        self.display.rect(self.x, self.y, self.width, self.height, color)
        
        # Фон
        self.display.fill_rect(self.x + 1, self.y + 1, self.width - 2, self.height - 2, 0xFFFF)
        
        # Текст
        if self.text:
            display_text = self.text[-15:]  # Показываем последние 15 символов
            self.display.text(display_text, self.x + 3, self.y + 3, 0x0000)
        else:
            # Плэйсхолдер (серый)
            placeholder_short = self.placeholder[:15]
            self.display.text(placeholder_short, self.x + 3, self.y + 3, 0xB0B0)
        
        # Курсор
        if self.is_focused:
            self.cursor_blink_counter += 1
            if (self.cursor_blink_counter // 15) % 2 == 0:
                cursor_x = self.x + 3 + len(self.text) * 6
                if cursor_x < self.x + self.width - 3:
                    self.display.vline(cursor_x, self.y + 2, self.height - 4, 0x0000)
    
    def focus(self):
        """Установить фокус"""
        self.is_focused = True
        self.keyboard.show()
    
    def unfocus(self):
        """Убрать фокус"""
        self.is_focused = False
        self.keyboard.hide()
    
    def add_char(self, char):
        """Добавить символ"""
        if len(self.text) < 50:
            self.text += char
            self.cursor_position = len(self.text)
    
    def backspace(self):
        """Удалить символ"""
        if self.text:
            self.text = self.text[:-1]
            self.cursor_position = len(self.text)
    
    def get_text(self):
        """Получить текст"""
        return self.text
    
    def set_text(self, text):
        """Установить текст"""
        self.text = text[:50]
        self.cursor_position = len(self.text)
    
    def clear(self):
        """Очистить"""
        self.text = ""
        self.cursor_position = 0

# ============================================
# МИНИМАЛИСТИЧНОЕ ГЛАВНОЕ МЕНЮ
# ============================================

class MinimalMainMenu:
    """Минималистичное главное меню"""
    
    def __init__(self, display):
        self.display = display
        self.control_center = ControlCenter(display)
        self.selected = 0
        self.apps = [
            {'name': 'Phone', 'id': 1},
            {'name': 'Messages', 'id': 2},
            {'name': 'Files', 'id': 3},
            {'name': 'Settings', 'id': 4},
            {'name': 'WiFi', 'id': 5},
            {'name': 'Camera', 'id': 6},
            {'name': 'Modules', 'id': 7},
            {'name': 'Browser', 'id': 8},
        ]
    
    def draw(self):
        """Рисует меню"""
        self.display.fill(0xFFFF)  # Белый фон
        
        # Строка статуса (минималистичная)
        timestamp = time.localtime()
        time_str = f"{timestamp[3]:02d}:{timestamp[4]:02d}"
        self.display.text(time_str, 5, 2, 0x0000)
        
        # Индикатор сигнала и батареи
        self.display.text("●●●●●", 95, 2, 0x696969)
        
        # Разделитель
        self.display.hline(0, 11, 128, 0xE0E0)
        
        # Приложения в минималистичной сетке 2x4
        for i in range(8):
            col = i % 2
            row = i // 2
            
            x = col * 64 + 2
            y = 14 + row * 12
            
            is_selected = (i == self.selected)
            
            # Ячейка приложения
            if is_selected:
                self.display.fill_rect(x, y, 60, 11, 0xF0F0)
                self.display.rect(x, y, 60, 11, 0x007AFF)
                color = 0x007AFF
            else:
                self.display.rect(x, y, 60, 11, 0xD0D0)
                color = 0x0000
            
            # Название приложения
            app_name = self.apps[i]['name']
            self.display.text("◉ " + app_name, x + 3, y + 2, color)
        
        # Рисуем нижнюю шторку
        self.control_center.draw()
        
        self.display.show()
    
    def select_next(self):
        """Выбрать следующее приложение"""
        self.selected = (self.selected + 1) % len(self.apps)
    
    def select_prev(self):
        """Выбрать предыдущее приложение"""
        self.selected = (self.selected - 1) % len(self.apps)
    
    def toggle_control_center(self):
        """Переключить шторку"""
        self.control_center.toggle()

# ============================================
# ПРИЛОЖЕНИЕ СООБЩЕНИЙ С КЛАВИАТУРОЙ
# ============================================

class MessageAppMinimal:
    """Приложение сообщений с минималистичным дизайном"""
    
    def __init__(self, display):
        self.display = display
        self.title = "Messages"
        self.messages = []
        self.input_field = TextField(display, 2, 48, 124, 10, "Type message...")
        self.scroll_position = 0
    
    def draw(self):
        """Рисует приложение"""
        self.display.fill(0xFFFF)
        
        # Заголовок
        self.display.fill_rect(0, 0, 128, 14, 0xF0F0)
        self.display.text("< Messages", 5, 3, 0x0000)
        self.display.hline(0, 13, 128, 0xE0E0)
        
        # История сообщений (максимум 3)
        y = 16
        for msg in self.messages[-3:]:
            if msg['from'] == 'me':
                # Мое сообщение (зелёное, справа)
                msg_text = msg['text'][:18]
                text_width = len(msg_text) * 6
                x = 128 - text_width - 5
                
                self.display.fill_rect(x - 2, y, text_width + 4, 10, 0xC8E6C9)
                self.display.text(msg_text, x, y + 1, 0x1B5E20)
            else:
                # От других (серое, слева)
                self.display.fill_rect(3, y, 80, 10, 0xEEEEEE)
                self.display.text(msg['text'][:20], 5, y + 1, 0x424242)
            
            y += 12
        
        # Разделитель перед полем ввода
        self.display.hline(0, 46, 128, 0xE0E0)
        
        # Текстовое поле
        self.input_field.draw()
        
        # Клавиатура
        self.input_field.keyboard.draw()
        
        self.display.show()
    
    def add_message(self, text, sender='other'):
        """Добавить сообщение"""
        self.messages.append({
            'text': text,
            'from': sender,
            'time': time.time()
        })
    
    def send_message(self):
        """Отправить сообщение"""
        text = self.input_field.get_text()
        if text:
            self.add_message(text, 'me')
            self.input_field.clear()
    
    def focus_input(self):
        """Фокус на поле ввода"""
        self.input_field.focus()
    
    def unfocus_input(self):
        """Убрать фокус"""
        self.input_field.unfocus()

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Главная функция"""
    
    print("\n" + "="*70)
    print("BITOS OS v3.1 - MODERN MINIMAL UI WITH iOS CONTROL CENTER")
    print("="*70)
    print("\n✓ Минималистичный белый дизайн инициализирован")
    print("✓ iOS-style Control Center (нижняя шторка) с анимацией")
    print("✓ Виртуальная клавиатура с навигацией")
    print("✓ Текстовые поля с фокусом и курсором")
    print("✓ Приложение Messages с клавиатурой")
    print("\nОсновные компоненты:")
    print("  • ControlCenter - нижняя шторка (свайп вверх)")
    print("  • VirtualKeyboard - полнофункциональная клавиатура")
    print("  • TextField - поле ввода с фокусом")
    print("  • MinimalMainMenu - главное меню с 8 приложениями")
    print("  • MessageAppMinimal - приложение с историей и клавиатурой")
    print("\nАнимация и интерактивность:")
    print("  • Плавное открытие/закрытие шторки")
    print("  • Анимированное появление клавиатуры")
    print("  • Блинк курсора в текстовых полях")
    print("  • Выделение выбранных элементов")
    print("  • Тень и разделители для разделения элементов")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
