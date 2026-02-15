from ..utils import THEMES, COLOR_NAMES, DEFAULT_CONFIG, init_color_256, save_config, load_config
from .. import stepper
import curses
import time

# arrows: ← ↑ → ↓ ←→ ● ○ (so I can copy them more easilly)
# I need better class names, cause what's this:
class kern_s:
    def __init__(self, stdscr, config, parent_ui=None):
        self.stdscr = stdscr
        self.config = config
        self.running = True
        self.parent_ui = parent_ui
        self.init_colors()

    def log(self, message, level="INFO"):
        if self.parent_ui:
            self.parent_ui.log(message, level)

    @staticmethod
    def setup(stdscr, config, skip_intro=False):
        curses.curs_set(0)
        stdscr.clear()
        stdscr.nodelay(0)
        
        h, w = stdscr.getmaxyx()
        init_color_256()
        
        for i in range(1, min(16, curses.COLORS)):
            try:
                curses.init_pair(i, i, 0)
            except:
                pass
        
        selected_theme_idx = 0
        theme_keys = list(THEMES.keys())
        current_theme = config.get('theme', 'dark_mode')
        
        if current_theme in theme_keys:
            selected_theme_idx = theme_keys.index(current_theme)
        
        while True:
            stdscr.clear()
            
            title = "==== KERN-4 SETUP ===="
            step_title = "Step 1/5: Choose Main Theme"
            instructions = "Use ↑↓ arrows to select, ENTER to confirm"
            
            title_x = max(0, (w - len(title)) // 2)
            step_x = max(0, (w - len(step_title)) // 2)
            inst_x = max(0, (w - len(instructions)) // 2)
            
            stdscr.addstr(2, title_x, title, curses.A_BOLD)
            stdscr.addstr(4, step_x, step_title, curses.A_BOLD)
            stdscr.addstr(5, inst_x, instructions)
            
            start_row = 8
            for i, theme_key in enumerate(theme_keys):
                theme = THEMES[theme_key]
                
                marker = "→ " if i == selected_theme_idx else "  "
                theme_name = theme["name"]
                theme_desc = theme["description"]
                
                name_line = f"{marker}{theme_name}"
                name_x = max(0, (w - 60) // 2)
                
                attr = curses.A_REVERSE | curses.A_BOLD if i == selected_theme_idx else curses.A_BOLD
                
                try:
                    stdscr.addstr(start_row + i * 3, name_x, name_line, attr)
                    stdscr.addstr(start_row + i * 3 + 1, name_x + 3, theme_desc, curses.A_DIM)
                except:
                    pass
            
            preview_row = start_row + len(theme_keys) * 3 + 2
            preview_title = "Color Preview:"
            try:
                stdscr.addstr(preview_row, max(0, (w - len(preview_title)) // 2), preview_title, curses.A_BOLD)
            except:
                pass
            
            selected_theme = THEMES[theme_keys[selected_theme_idx]]
            
            has_256 = curses.COLORS >= 256
            if has_256 and 'colors_256' in selected_theme:
                theme_colors = selected_theme['colors_256']
            else:
                theme_colors = selected_theme.get('colors_16', selected_theme.get('colors', {}))
            
            color_labels = [
                ("Primary", "primary"),
                ("Accent", "accent"),
                ("Highlight", "highlight"),
                ("Border", "border"),
                ("Warning", "warn"),
                ("Error", "error"),
            ]
            
            preview_start = preview_row + 2
            preview_x = max(0, (w - 50) // 2)
            
            for i, (label, key) in enumerate(color_labels):
                if key not in theme_colors:
                    continue
                    
                color_idx = theme_colors[key]
                try:
                    if has_256 and color_idx >= 100:
                        color_attr = curses.color_pair(color_idx) | curses.A_BOLD
                    elif color_idx < 16:
                        curses.init_pair(20 + i, color_idx, config.get('bg_color', 0))
                        color_attr = curses.color_pair(20 + i) | curses.A_BOLD
                    else:
                        color_attr = curses.A_BOLD
                    
                    preview_text = f"{label}: ████████ Kern-4"
                    stdscr.addstr(preview_start + i, preview_x, preview_text, color_attr)
                except:
                    pass
            
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == curses.KEY_UP:
                selected_theme_idx = max(0, selected_theme_idx - 1)
            elif key == curses.KEY_DOWN:
                selected_theme_idx = min(len(theme_keys) - 1, selected_theme_idx + 1)
            elif key in (ord('\n'), ord('\r'), curses.KEY_ENTER, 10, 13):
                config['theme'] = theme_keys[selected_theme_idx]
                selected_theme_obj = THEMES[config['theme']]
                if has_256 and 'colors_256' in selected_theme_obj:
                    theme_colors = selected_theme_obj['colors_256']
                else:
                    theme_colors = selected_theme_obj.get('colors_16', selected_theme_obj.get('colors', {}))
                config['accent_color'] = theme_colors['accent']
                config['error_color'] = theme_colors['error']
                break
        
        selected_fg = config.get('fg_color', 7)
        
        while True:
            stdscr.clear()
            
            title = "==== KERN-4 SETUP ===="
            step_title = "Step 2/5: Choose Foreground (Text) Color"
            instructions = "Use ↑↓ arrows to select, ENTER to confirm, 'd' for default"
            
            title_x = max(0, (w - len(title)) // 2)
            step_x = max(0, (w - len(step_title)) // 2)
            inst_x = max(0, (w - len(instructions)) // 2)
            
            stdscr.addstr(2, title_x, title, curses.A_BOLD)
            stdscr.addstr(4, step_x, step_title, curses.A_BOLD)
            stdscr.addstr(5, inst_x, instructions)
            
            color_list_width = 60
            start_col = max(0, (w - color_list_width) // 2)
            start_row = 7
            
            for i in range(min(16, curses.COLORS)):
                if i >= len(COLOR_NAMES):
                    break
                
                marker = "→ " if i == selected_fg else "  "
                color_name = COLOR_NAMES[i]
                
                try:
                    if i < curses.COLOR_PAIRS:
                        curses.init_pair(i + 1, i, config.get('bg_color', 0))
                        attr = curses.color_pair(i + 1)
                    else:
                        attr = curses.A_NORMAL
                    
                    label = f"{marker}{i:2d}. {color_name:<20}"
                    preview = "The fox jumped over kern-4..."
                    
                    stdscr.addstr(start_row + i, start_col, label, 
                                curses.A_REVERSE if i == selected_fg else curses.A_NORMAL)
                    stdscr.addstr(start_row + i, start_col + 25, preview, attr | curses.A_BOLD)
                except:
                    pass
            
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == curses.KEY_UP:
                selected_fg = max(0, selected_fg - 1)
            elif key == curses.KEY_DOWN:
                selected_fg = min(min(15, curses.COLORS - 1), selected_fg + 1)
            elif key in (ord('\n'), ord('\r'), curses.KEY_ENTER, 10, 13):
                config['fg_color'] = selected_fg
                break
            elif key == ord('d'):
                config['fg_color'] = 7
                break
        
        selected_bg = config.get('bg_color', 0)
        
        while True:
            stdscr.clear()
            
            title = "==== KERN-4 SETUP ===="
            step_title = "Step 3/5: Choose Background Color"
            instructions = "Use ↑↓ arrows to select, ENTER to confirm, 'd' for default"
            
            title_x = max(0, (w - len(title)) // 2)
            step_x = max(0, (w - len(step_title)) // 2)
            inst_x = max(0, (w - len(instructions)) // 2)
            
            stdscr.addstr(2, title_x, title, curses.A_BOLD)
            stdscr.addstr(4, step_x, step_title, curses.A_BOLD)
            stdscr.addstr(5, inst_x, instructions)
            
            color_list_width = 60
            start_col = max(0, (w - color_list_width) // 2)
            start_row = 7
            
            for i in range(min(16, curses.COLORS)):
                if i >= len(COLOR_NAMES):
                    break
                
                marker = "→ " if i == selected_bg else "  "
                color_name = COLOR_NAMES[i]
                
                try:
                    if i < curses.COLOR_PAIRS:
                        curses.init_pair(i + 1, config['fg_color'], i)
                        attr = curses.color_pair(i + 1)
                    else:
                        attr = curses.A_NORMAL
                    
                    label = f"{marker}{i:2d}. {color_name:<20}"
                    preview = "The quick kernish brown fox rolls..."
                    
                    stdscr.addstr(start_row + i, start_col, label, 
                                curses.A_REVERSE if i == selected_bg else curses.A_NORMAL)
                    stdscr.addstr(start_row + i, start_col + 25, preview, attr | curses.A_BOLD)
                except:
                    pass
            
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == curses.KEY_UP:
                selected_bg = max(0, selected_bg - 1)
            elif key == curses.KEY_DOWN:
                selected_bg = min(min(15, curses.COLORS - 1), selected_bg + 1)
            elif key in (ord('\n'), ord('\r'), curses.KEY_ENTER, 10, 13):
                config['bg_color'] = selected_bg
                break
            elif key == ord('d'):
                config['bg_color'] = 0
                break
        
        selected_logo = config.get('logo_color', 2)
        
        while True:
            stdscr.clear()
            
            title = "==== KERN-4 SETUP ===="
            step_title = "Step 4/5: Choose Logo Color"
            instructions = "Use ↑↓ arrows to select, ENTER to confirm, 'd' for default (Green)"
            
            title_x = max(0, (w - len(title)) // 2)
            step_x = max(0, (w - len(step_title)) // 2)
            inst_x = max(0, (w - len(instructions)) // 2)
            
            stdscr.addstr(2, title_x, title, curses.A_BOLD)
            stdscr.addstr(4, step_x, step_title, curses.A_BOLD)
            stdscr.addstr(5, inst_x, instructions)
            
            color_list_width = 60
            start_col = max(0, (w - color_list_width) // 2)
            start_row = 7
            
            for i in range(min(16, curses.COLORS)):
                if i >= len(COLOR_NAMES):
                    break
                
                marker = "→ " if i == selected_logo else "  "
                color_name = COLOR_NAMES[i]
                
                try:
                    if i < curses.COLOR_PAIRS:
                        curses.init_pair(i + 1, i, config['bg_color'])
                        attr = curses.color_pair(i + 1)
                    else:
                        attr = curses.A_NORMAL
                    
                    label = f"{marker}{i:2d}. {color_name:<20}"
                    preview = "==== KERN-4 ===="
                    
                    stdscr.addstr(start_row + i, start_col, label, 
                                curses.A_REVERSE if i == selected_logo else curses.A_NORMAL)
                    stdscr.addstr(start_row + i, start_col + 25, preview, attr | curses.A_BOLD)
                except:
                    pass
            
            stdscr.refresh()
            
            key = stdscr.getch()
            if key == curses.KEY_UP:
                selected_logo = max(0, selected_logo - 1)
            elif key == curses.KEY_DOWN:
                selected_logo = min(min(15, curses.COLORS - 1), selected_logo + 1)
            elif key in (ord('\n'), ord('\r'), curses.KEY_ENTER, 10, 13):
                config['logo_color'] = selected_logo
                break
            elif key == ord('d'):
                config['logo_color'] = 2
                break
        
        stdscr.clear()
        
        title = "==== KERN-4 SETUP ===="
        step_title = "Step 5/5: Configure Motor Mapping"
        instructions1 = "Scanning for serial devices..."
        
        title_x = max(0, (w - len(title)) // 2)
        step_x = max(0, (w - len(step_title)) // 2)
        inst_x = max(0, (w - len(instructions1)) // 2)
        
        stdscr.addstr(2, title_x, title, curses.A_BOLD)
        stdscr.addstr(4, step_x, step_title, curses.A_BOLD)
        stdscr.addstr(6, inst_x, instructions1)
        stdscr.refresh()
        
        ports = stepper.list_serial_ports()
        
        device_options = ["(unassigned)"]
        for port in ports:
            for axis in ["X", "Y", "Z"]:
                device_options.append(f"{port}:{axis}")
        
        motor_mapping = config.get('motor_mapping', [None, None, None, None])
        if len(motor_mapping) < 4:
            motor_mapping = [None, None, None, None]
        
        motor_indices = [0, 0, 0, 0]
        for i in range(4):
            if motor_mapping[i]:
                try:
                    idx = device_options.index(motor_mapping[i])
                    motor_indices[i] = idx
                except ValueError:
                    motor_indices[i] = 0
        
        selected_motor = 0
        scroll_offset = 0
        
        while True:
            stdscr.clear()
            
            title = "==== KERN-4 SETUP ===="
            step_title = "Step 5/5: Configure Motor Mapping"
            instructions1 = "Use ↑↓ to navigate motors, ←→ to change assignment"
            instructions2 = "Press ENTER to continue, 's' to skip motor mapping"
            
            title_x = max(0, (w - len(title)) // 2)
            step_x = max(0, (w - len(step_title)) // 2)
            inst1_x = max(0, (w - len(instructions1)) // 2)
            inst2_x = max(0, (w - len(instructions2)) // 2)
            
            stdscr.addstr(2, title_x, title, curses.A_BOLD)
            stdscr.addstr(4, step_x, step_title, curses.A_BOLD)
            stdscr.addstr(5, inst1_x, instructions1)
            stdscr.addstr(6, inst2_x, instructions2)
            
            if not ports:
                msg = "Error: No serial devices detected"
                stdscr.addstr(8, max(0, (w - len(msg)) // 2), msg, curses.A_BOLD)
            else:
                msg = f"Detected {len(ports)} serial port(s): {', '.join(ports)}"
                msg_x = max(0, (w - min(len(msg), w - 4)) // 2)
                stdscr.addstr(8, msg_x, msg[:w - 4])
            
            mapping_start_row = 11
            mapping_width = 50
            mapping_x = max(0, (w - mapping_width) // 2)
            
            for i in range(4):
                row = mapping_start_row + i * 2
                
                motor_label = f"Motor {i + 1}:"
                assignment = device_options[motor_indices[i]]
                
                marker = "→ " if i == selected_motor else "  "
                line = f"{marker}{motor_label:<12} {assignment}"
                
                attr = curses.A_REVERSE if i == selected_motor else curses.A_NORMAL
                if assignment != "(unassigned)":
                    attr |= curses.A_BOLD
                
                try:
                    stdscr.addstr(row, mapping_x, line, attr)
                except:
                    pass
            
            if device_options:
                options_start_row = mapping_start_row + 10
                options_title = f"Available options for Motor {selected_motor + 1}:"
                stdscr.addstr(options_start_row - 1, max(0, (w - len(options_title)) // 2), 
                            options_title, curses.A_BOLD)
                
                visible_options = min(8, h - options_start_row - 2)
                
                for i in range(visible_options):
                    opt_idx = scroll_offset + i
                    if opt_idx >= len(device_options):
                        break
                    
                    option = device_options[opt_idx]
                    is_current = (opt_idx == motor_indices[selected_motor])
                    
                    marker = "◆ " if is_current else "  "
                    line = f"{marker}{option}"
                    
                    attr = curses.A_BOLD if is_current else curses.A_NORMAL
                    
                    try:
                        stdscr.addstr(options_start_row + i, max(0, (w - 40) // 2), 
                                    line, attr)
                    except:
                        pass
                
                if len(device_options) > visible_options:
                    scroll_info = f"[{scroll_offset + 1}-{min(scroll_offset + visible_options, len(device_options))}/{len(device_options)}]"
                    try:
                        stdscr.addstr(options_start_row + visible_options, 
                                    max(0, (w - len(scroll_info)) // 2), scroll_info)
                    except:
                        pass
            
            stdscr.refresh()
            
            key = stdscr.getch()
            
            if key == curses.KEY_UP:
                selected_motor = max(0, selected_motor - 1)
                scroll_offset = max(0, min(scroll_offset, motor_indices[selected_motor]))
            elif key == curses.KEY_DOWN:
                selected_motor = min(3, selected_motor + 1)
                scroll_offset = max(0, min(scroll_offset, motor_indices[selected_motor]))
            elif key == curses.KEY_LEFT:
                motor_indices[selected_motor] = max(0, motor_indices[selected_motor] - 1)
                scroll_offset = max(0, min(scroll_offset, motor_indices[selected_motor]))
            elif key == curses.KEY_RIGHT:
                motor_indices[selected_motor] = min(len(device_options) - 1, motor_indices[selected_motor] + 1)
                visible_options = min(8, h - (mapping_start_row + 10) - 2)
                if motor_indices[selected_motor] >= scroll_offset + visible_options:
                    scroll_offset = motor_indices[selected_motor] - visible_options + 1
            elif key in (ord('\n'), ord('\r'), curses.KEY_ENTER, 10, 13):
                for i in range(4):
                    if motor_indices[i] == 0:
                        motor_mapping[i] = None
                    else:
                        motor_mapping[i] = device_options[motor_indices[i]]
                config['motor_mapping'] = motor_mapping
                break
            elif key == ord('s'):
                config['motor_mapping'] = [None, None, None, None]
                break
        
        config['setup_completed'] = True
        config['accent_color'] = 2
        config['error_color'] = 1
        
        save_config(config)
        
        stdscr.clear()
        msg = "Setup complete! Staring kern-4..."
        stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg, curses.A_BOLD)
        stdscr.refresh()
        time.sleep(1.5)

    def init_colors(self):
        try:
            self.has_256_colors = init_color_256()
            
            theme_name = self.config.get('theme', 'dark_mode')
            if theme_name not in THEMES:
                theme_name = 'dark_mode'
            
            theme = THEMES[theme_name]
            
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
            
        except Exception:
            self.COLOR_NORMAL = curses.A_NORMAL
            self.COLOR_ACCENT = curses.A_BOLD
            self.COLOR_ERROR = curses.A_REVERSE
            self.COLOR_WARN = curses.A_UNDERLINE
            self.COLOR_INFO = curses.A_DIM
            self.COLOR_HIGHLIGHT = curses.A_BOLD
            self.COLOR_BORDER = curses.A_NORMAL
            self.has_256_colors = False

    def show_settings(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        self.motor_mapping = self.config.get('motor_mapping', [None, None, None, None])
        self.init_colors()

        self.stdscr.nodelay(0)
        
        while True:
            self.stdscr.clear()
            
            title = "==== KERN-4 SETTINGS ===="
            self.stdscr.addstr(2, max(0, (w - len(title)) // 2), title, self.COLOR_ACCENT)
            
            theme_name = self.config.get('theme', 'dark_mode')
            if theme_name in THEMES:
                theme_display = THEMES[theme_name]['name']
            else:
                theme_display = theme_name
            
            # I want to change the bullets (●) with smth else, idk what
            options = [
                "",
                "Current Configuration:",
                f"  • Theme: {theme_display}",
                f"  • Foreground Color: {COLOR_NAMES[self.config['fg_color']]} ({self.config['fg_color']})",
                f"  • Background Color: {COLOR_NAMES[self.config['bg_color']]} ({self.config['bg_color']})",
                f"  • Logo Color: {COLOR_NAMES[self.config.get('logo_color', 2)]} ({self.config.get('logo_color', 2)})",
                "",
                "Motor Mapping:",
            ]
            
            for i in range(4):
                mapping = self.motor_mapping[i]
                if mapping:
                    options.append(f"  • Motor {i+1}: {mapping}") # same here...
                else:
                    options.append(f"  • Motor {i+1}: (unassigned)")
            
            options.extend([
                "",
                "Actions:",
                "  [1] Re-run Full Setup Wizard", # Feels like XP, for those who know
                "  [2] Change Theme Only",
                "  [3] Reset to Defaults",
                "  [ESC] Back to Main Menu",
            ])
            
            start_row = 5
            for i, line in enumerate(options):
                if start_row + i < h - 2:
                    try:
                        line_x = max(0, (w - len(line)) // 2)
                        attr = self.COLOR_NORMAL
                        if line.startswith("  ["):
                            attr = self.COLOR_ACCENT
                        elif line.startswith("  • Theme:"):
                            attr = self.COLOR_HIGHLIGHT
                        self.stdscr.addstr(start_row + i, line_x, line[:w-4], attr)
                    except:
                        pass
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            
            if key == ord('1'):
                self.log("Re-running full setup wizard...")
                self.setup(self.stdscr, self.config, skip_intro=True)
                
                self.config = load_config()
                self.motor_mapping = self.config.get('motor_mapping', [None, None, None, None])
                
                self.init_colors()
                
                self.log("Configuration updated")
                break
            
            elif key == ord('2'):
                self.change_theme()
                break
            
            elif key == ord('3'):
                self.config = DEFAULT_CONFIG.copy()
                self.config['setup_completed'] = True
                save_config(self.config)
                self.motor_mapping = [None, None, None, None]
                self.init_colors()
                self.log("Configuration reset to defaults")
                break
            
            elif key == 27:
                break
        
        self.stdscr.nodelay(1)
        self.stdscr.timeout(100)
    
    def change_theme(self):
        h, w = self.stdscr.getmaxyx()
        
        selected_theme_idx = 0
        theme_keys = list(THEMES.keys())
        current_theme = self.config.get('theme', 'dark_mode')
        
        if current_theme in theme_keys:
            selected_theme_idx = theme_keys.index(current_theme)
        
        while True:
            self.stdscr.clear()
            
            title = "==== CHANGE THEME ===="
            instructions = "Use ↑↓ arrows to select, ENTER to confirm, ESC to cancel"
            
            title_x = max(0, (w - len(title)) // 2)
            inst_x = max(0, (w - len(instructions)) // 2)
            
            self.stdscr.addstr(2, title_x, title, self.COLOR_ACCENT)
            self.stdscr.addstr(4, inst_x, instructions, self.COLOR_INFO)
            
            start_row = 7
            for i, theme_key in enumerate(theme_keys):
                theme = THEMES[theme_key]
                
                marker = "→ " if i == selected_theme_idx else "  "
                theme_name = theme["name"]
                theme_desc = theme["description"]
                
                name_line = f"{marker}{theme_name}"
                name_x = max(0, (w - 60) // 2)
                
                attr = self.COLOR_ACCENT if i == selected_theme_idx else self.COLOR_NORMAL
                if i == selected_theme_idx:
                    attr |= curses.A_REVERSE
                
                try:
                    self.stdscr.addstr(start_row + i * 3, name_x, name_line, attr)
                    self.stdscr.addstr(start_row + i * 3 + 1, name_x + 3, theme_desc, self.COLOR_INFO)
                except:
                    pass
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            if key == curses.KEY_UP:
                selected_theme_idx = max(0, selected_theme_idx - 1)
            elif key == curses.KEY_DOWN:
                selected_theme_idx = min(len(theme_keys) - 1, selected_theme_idx + 1)
            elif key in (ord('\n'), ord('\r'), curses.KEY_ENTER, 10, 13):
                self.config['theme'] = theme_keys[selected_theme_idx]
                save_config(self.config)
                self.init_colors()
                self.log(f"Theme changed to: {THEMES[self.config['theme']]['name']}")
                break
            elif key == 27:
                self.log("Theme change cancelled")
                break