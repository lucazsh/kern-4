from . import utils
from .devices import kern_devices
from . import input 
from .ui import mapping, manual, training, settings
import time
import curses
import threading
from datetime import datetime

# arrows: ← ↑ → ↓ ● ○ (so I can copy them more easilly)
class kern_ui:
    def __init__(self, stdscr, config):
        self.stdscr = stdscr
        self.config = config
        self.running = True
        
        curses.curs_set(0)
        stdscr.nodelay(1)
        stdscr.timeout(100)
        
        self.init_colors()
        
        self.devices = []
        self.selected_device_idx = 0
        
        self.training_active = False
        self.training_thread = None
        self.training_stop_event = threading.Event()
        self.training_env = None
        
        self.motor_mapping = config.get('motor_mapping', [None, None, None, None])
        if len(self.motor_mapping) < 4:
            self.motor_mapping = [None, None, None, None]
        self.device_states = {}
        self.staged_targets = {}
        self.accumulation_counter = 0
        self.aggregation_threshold = 400
        self.angle_to_steps_scale = 100.0
        self.gear_ratios = [25.0, 42.25, 31.36, 25.0] # You can change them if you're gonna use other gear ratios
        self.current_panel = 0
        self.log_messages = []
        self.log_scroll = 0
        self.device_scroll = 0
        self.menu_scroll = 0
        targets = utils.load_targets()
        for k, v in targets.items():
            self.device_states[k] = {
                'current_steps': int(v),
                'target_steps': int(v),
                'lock': threading.Lock()
            }

        self.kern_settings = settings.kern_s(self.stdscr, self.config, self)
        self.menu_items = [
            ("1", "Scan & Add Devices", lambda: kern_devices.scan_devices(self)),
            ("2", "Configure Motor Mapping", lambda: mapping.configuration(self)),
            ("3", "Test Motor Mapping", self.test_mapping),
            ("4", "Set Speed/Acceleration", self.set_speed_accel),
            ("5", "Manual Motor Control", lambda: manual.control(self).control()),
            ("6", "Start AI Training", self.start_ai),
            ("7", "Stop AI Training", self.stop_ai),
            ("8", "Disconnect All Devices", lambda: kern_devices.disconnect_all(self)),
            ("9", "View System Log", self.view_log),
            ("0", "Settings & Config", self.kern_settings.show_settings),
            ("Q", "Quit Application", self.quit_app),
        ]
        
        self.selected_menu_idx = 0

    def init_colors(self):
        try:
            self.has_256_colors = utils.init_color_256()
            
            theme_name = self.config.get('theme', 'dark_mode')
            if theme_name not in utils.THEMES:
                theme_name = 'dark_mode'
            
            theme = utils.THEMES[theme_name]
            
            if self.has_256_colors:
                colors = theme['colors_256']
            else:
                colors = theme['colors_16']
            
            bg = self.config.get('bg_color', 0)
            
            if not self.has_256_colors:
                curses.init_pair(1, colors['primary'], bg)
                curses.init_pair(2, colors['accent'], bg)
                curses.init_pair(3, colors['error'], bg)
                curses.init_pair(4, colors['warn'], bg)
                curses.init_pair(5, colors['secondary'], bg)
                curses.init_pair(6, colors['highlight'], bg)
                curses.init_pair(7, colors['border'], bg)
                
                self.COLOR_NORMAL = curses.color_pair(1)
                self.COLOR_ACCENT = curses.color_pair(2) | curses.A_BOLD
                self.COLOR_ERROR = curses.color_pair(3) | curses.A_BOLD
                self.COLOR_WARN = curses.color_pair(4) | curses.A_BOLD
                self.COLOR_INFO = curses.color_pair(5)
                self.COLOR_HIGHLIGHT = curses.color_pair(6) | curses.A_BOLD
                self.COLOR_BORDER = curses.color_pair(7)
            else:
                self.COLOR_NORMAL = curses.color_pair(colors['primary'])
                self.COLOR_ACCENT = curses.color_pair(colors['accent']) | curses.A_BOLD
                self.COLOR_ERROR = curses.color_pair(colors['error']) | curses.A_BOLD
                self.COLOR_WARN = curses.color_pair(colors['warn']) | curses.A_BOLD
                self.COLOR_INFO = curses.color_pair(colors['secondary'])
                self.COLOR_HIGHLIGHT = curses.color_pair(colors['highlight']) | curses.A_BOLD
                self.COLOR_BORDER = curses.color_pair(colors['border'])
            
            if self.has_256_colors:
                self.COLOR_HEADER = curses.color_pair(200) | curses.A_BOLD
            else:
                curses.init_pair(50, 0, 7)
                self.COLOR_HEADER = curses.color_pair(50) | curses.A_BOLD
            
            self.current_theme_name = theme['name']
            
        except Exception as e:
            self.COLOR_NORMAL = curses.A_NORMAL
            self.COLOR_ACCENT = curses.A_BOLD
            self.COLOR_ERROR = curses.A_REVERSE
            self.COLOR_WARN = curses.A_UNDERLINE
            self.COLOR_INFO = curses.A_DIM
            self.COLOR_HIGHLIGHT = curses.A_BOLD
            self.COLOR_BORDER = curses.A_NORMAL
            self.COLOR_HEADER = curses.A_REVERSE | curses.A_BOLD
            self.current_theme_name = "Default"
            self.has_256_colors = False
    
    def draw_header(self):
        h, w = self.stdscr.getmaxyx()
        
        title = "==== KERN-4 v0.2 ====" # I don't know how else to style it
        status = f"Devices: {len(self.devices)} | Training: {'ACTIVE' if self.training_active else 'IDLE'} | Theme: {getattr(self, 'current_theme_name', 'Default')}"
        
        try:
            self.stdscr.addstr(0, max(0, (w - len(title)) // 2), title, self.COLOR_ACCENT)
            self.stdscr.addstr(1, 2, status, self.COLOR_INFO)
            self.stdscr.addstr(1, w - 22, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                             self.COLOR_NORMAL)
        except:
            pass
    
    def draw_menu(self, start_row, start_col, width, height):
        try:
            self.stdscr.addstr(start_row, start_col, "┌" + "─" * (width - 2) + "┐")
            for i in range(1, height - 1):
                self.stdscr.addstr(start_row + i, start_col, "│")
                self.stdscr.addstr(start_row + i, start_col + width - 1, "│")
            self.stdscr.addstr(start_row + height - 1, start_col, "└" + "─" * (width - 2) + "┘")
            
            title = " MAIN MENU "
            self.stdscr.addstr(start_row, start_col + 2, title, self.COLOR_ACCENT)
            
            display_items = self.menu_items[self.menu_scroll:self.menu_scroll + height - 3]
            
            for i, (key, label, func) in enumerate(display_items):
                row = start_row + i + 2
                if row >= start_row + height - 1:
                    break
                
                actual_idx = self.menu_scroll + i
                is_selected = (actual_idx == self.selected_menu_idx)
                
                prefix = "→ " if is_selected else "  "
                text = f"{prefix}[{key}] {label}"
                
                attr = self.COLOR_ACCENT if is_selected else self.COLOR_NORMAL
                self.stdscr.addstr(row, start_col + 2, text[:width - 4], attr)
            
            if len(self.menu_items) > height - 3:
                total_items = len(self.menu_items)
                visible_items = height - 3
                indicator = f" {self.menu_scroll + 1}-{min(self.menu_scroll + visible_items, total_items)}/{total_items} "
                self.stdscr.addstr(start_row + height - 1, start_col + width - len(indicator) - 1, 
                                 indicator, self.COLOR_INFO)
        except:
            pass
    
    def draw_devices(self, start_row, start_col, width, height):
        try:
            self.stdscr.addstr(start_row, start_col, "┌" + "─" * (width - 2) + "┐")
            for i in range(1, height - 1):
                self.stdscr.addstr(start_row + i, start_col, "│")
                self.stdscr.addstr(start_row + i, start_col + width - 1, "│")
            self.stdscr.addstr(start_row + height - 1, start_col, "└" + "─" * (width - 2) + "┘")
            
            title = " CONNECTED DEVICES "
            self.stdscr.addstr(start_row, start_col + 2, title, self.COLOR_ACCENT)
            
            if not self.devices:
                self.stdscr.addstr(start_row + 2, start_col + 2, 
                                 "No devices connected", self.COLOR_WARN)
                self.stdscr.addstr(start_row + 3, start_col + 2, 
                                 "Press [1] to scan for devices", self.COLOR_INFO)
            else:
                row = start_row + 2
                for i, dev in enumerate(self.devices[self.device_scroll:]):
                    if row >= start_row + height - 1:
                        break
                    
                    status = "●" if dev.connected else "○"
                    color = self.COLOR_ACCENT if dev.connected else self.COLOR_ERROR
                    
                    info = f"{status} {dev.port} @ {dev.baud}"
                    self.stdscr.addstr(row, start_col + 2, info[:width - 4], color)
                    row += 1
                    
                    if dev.connected and row < start_row + height - 1:
                        pos_str = f"  X:{dev.positions['X']:6d} Y:{dev.positions['Y']:6d} Z:{dev.positions['Z']:6d}"
                        self.stdscr.addstr(row, start_col + 2, pos_str[:width - 4], 
                                         self.COLOR_NORMAL)
                        row += 1
        except:
            pass
    
    def draw_training(self, start_row, start_col, width, height):
        try:
            self.stdscr.addstr(start_row, start_col, "┌" + "─" * (width - 2) + "┐")
            for i in range(1, height - 1):
                self.stdscr.addstr(start_row + i, start_col, "│")
                self.stdscr.addstr(start_row + i, start_col + width - 1, "│")
            self.stdscr.addstr(start_row + height - 1, start_col, "└" + "─" * (width - 2) + "┘")
            
            title = " AI TRAINING STATUS "
            self.stdscr.addstr(start_row, start_col + 2, title, self.COLOR_ACCENT)
            
            row = start_row + 2
            
            if self.training_active:
                self.stdscr.addstr(row, start_col + 2, 
                                 "Status: ACTIVE", self.COLOR_ACCENT)
                row += 1
                self.stdscr.addstr(row, start_col + 2, 
                                 f"PyBullet: {'GUI' if hasattr(self, 'training_env') and self.training_env and self.training_env.gui else 'HEADLESS'}", 
                                 self.COLOR_INFO)
                row += 2
                
                self.stdscr.addstr(row, start_col + 2, "Motor Mapping:", self.COLOR_NORMAL)
                row += 1
                for i in range(4):
                    if self.motor_mapping[i]:
                        port, axis = self.motor_mapping[i].split(':')
                        mapping = f"  M{i+1} → {port}:{axis}"
                    else:
                        mapping = f"  M{i+1} → (unassigned)"
                    
                    color = self.COLOR_ACCENT if self.motor_mapping[i] else self.COLOR_WARN
                    self.stdscr.addstr(row, start_col + 2, mapping[:width - 4], color)
                    row += 1
            else:
                self.stdscr.addstr(row, start_col + 2, 
                                 "Status: IDLE", self.COLOR_WARN)
                row += 2
                self.stdscr.addstr(row, start_col + 2, 
                                 "Press [6] to start training", self.COLOR_INFO)
        except:
            pass
    
    def draw_log(self, start_row, start_col, width, height):
        try:
            self.stdscr.addstr(start_row, start_col, "┌" + "─" * (width - 2) + "┐")
            for i in range(1, height - 1):
                self.stdscr.addstr(start_row + i, start_col, "│")
                self.stdscr.addstr(start_row + i, start_col + width - 1, "│")
            self.stdscr.addstr(start_row + height - 1, start_col, "└" + "─" * (width - 2) + "┘")
            
            title = " SYSTEM LOG "
            self.stdscr.addstr(start_row, start_col + 2, title, self.COLOR_ACCENT)
            
            max_messages = height - 3
            if self.log_messages:
                display_messages = self.log_messages[-(self.log_scroll + max_messages):-self.log_scroll if self.log_scroll > 0 else None]
                
                row = start_row + 2
                for msg in display_messages[-max_messages:]:
                    if row >= start_row + height - 1:
                        break
                    
                    if "[ERROR]" in msg:
                        color = self.COLOR_ERROR
                    elif "[WARNING]" in msg:
                        color = self.COLOR_WARN
                    else:
                        color = self.COLOR_NORMAL
                    
                    self.stdscr.addstr(row, start_col + 2, msg[:width - 4], color)
                    row += 1
            else:
                self.stdscr.addstr(start_row + 2, start_col + 2, 
                                 "No log messages", self.COLOR_INFO)
        except:
            pass
    
    def draw_footer(self):
        h, w = self.stdscr.getmaxyx()
        
        hints = "↑↓: Navigate | ENTER: Select | TAB: Switch Panel | Q: Quit" # TAB doesn't does nothing yet so... (just for fun)
        
        try:
            self.stdscr.addstr(h - 1, 2, hints[:w - 4], self.COLOR_INFO)
        except:
            pass
    
    def draw(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        
        self.draw_header()
        
        header_height = 3
        footer_height = 1
        available_height = h - header_height - footer_height
        
        menu_width = max(30, w // 3)
        log_width = max(30, w // 3)
        middle_width = w - menu_width - log_width
        
        menu_height = available_height
        devices_height = available_height // 2
        training_height = available_height - devices_height
        log_height = available_height
        
        self.draw_menu(header_height, 0, menu_width, menu_height)
        self.draw_devices(header_height, menu_width, middle_width, devices_height)
        self.draw_training(header_height + devices_height, menu_width, middle_width, training_height)
        self.draw_log(header_height, menu_width + middle_width, log_width, log_height)
        
        self.draw_footer()
        self.stdscr.refresh()

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] [{level}] {message}")
        if len(self.log_messages) > 1000:
            self.log_messages = self.log_messages[-1000:]

    def start_ai(self):
        self.stdscr.clear()
        training.kern_train.start_training(self)
        self.draw()

    def stop_ai(self):
        self.stdscr.clear()
        training.kern_train.stop_training(self)
        self.draw()

    def test_mapping(self):
        self.log("Testing motor mapping...")
        
        for i in range(4):
            if self.motor_mapping[i] is None:
                continue
            
            mapping_str = self.motor_mapping[i]
            if ':' not in mapping_str:
                self.log(f"Motor {i+1}: Invalid mapping format '{mapping_str}'", "ERROR")
                continue
            
            port, axis = mapping_str.split(':', 1)
            dev = None
            for d in self.devices:
                if d.port == port:
                    dev = d
                    break
            
            if dev is None:
                self.log(f"Motor {i+1}: Device {port} not found", "ERROR")
                continue
            
            dev.move_axis(axis, 100)
            self.log(f"Motor {i+1} → {port}:{axis} test sent", "INFO")
            time.sleep(0.1)
    
    def set_speed_accel(self):
        for dev in self.devices:
            dev.set_speed(800) # TODO: change the value in settings, NOT HERE
            dev.set_acceleration(400) # same here...
        
        self.log("Set speed=800, accel=400 for all devices", "INFO") # yeah...
    
    def view_log(self):
        self.log_scroll = min(len(self.log_messages), self.log_scroll + 10)

    def quit_app(self):
        if self.training_active:
            self.training_stop_event.set()
            time.sleep(0.5)
        
        for dev in self.devices:
            dev.disconnect()
        
        self.running = False
    
    def update(self):
        updated = False
        for dev in self.devices:
            messages = dev.process_queue()
            if messages:
                updated = True
                for msg in messages:
                    self.log(f"[{dev.port}] {msg}")
        return updated
    
    def run(self):
        self.log("Kern-4 UI initialized")
        last_draw = 0
        
        while self.running:
            key = self.stdscr.getch()
            if key != -1:
                input.handler(self, key)
            
            state_updated = self.update()
            
            if (key != -1) or state_updated or self.training_active or (time.time() - last_draw >= 1.0):
                self.draw()
                last_draw = time.time()
            
            if key == -1:
                time.sleep(0.01)