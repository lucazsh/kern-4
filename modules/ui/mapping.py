from .. import stepper
import curses
from ..utils import save_config

# arrows: ← ↑ → ↓ ←→ ● ○ ◆ (so I can copy them more easilly)
def configuration(self):
    self.stdscr.clear()
    h, w = self.stdscr.getmaxyx()
    
    self.stdscr.nodelay(0)
    
    ports = stepper.list_serial_ports()
    
    device_options = ["(unassigned)"]
    # If you have only one CNC V3 sheild you might need to change this
    # to include the A axis
    # TODO: Change this for other users
    for port in ports:
        for axis in ["X", "Y", "Z"]: 
            device_options.append(f"{port}:{axis}")
    
    motor_indices = [0, 0, 0, 0]
    for i in range(4):
        if self.motor_mapping[i]:
            try:
                idx = device_options.index(self.motor_mapping[i])
                motor_indices[i] = idx
            except ValueError:
                motor_indices[i] = 0
    
    selected_motor = 0
    scroll_offset = 0
    
    while True:
        self.stdscr.clear()
        
        title = "==== KERN-4 MOTOR MAPPING ===="
        instructions1 = "Use ↑↓ to navigate motors, ←→ to change assignment"
        instructions2 = "Press ENTER to save, ESC to cancel"
        
        title_x = max(0, (w - len(title)) // 2)
        inst1_x = max(0, (w - len(instructions1)) // 2)
        inst2_x = max(0, (w - len(instructions2)) // 2)
        
        self.stdscr.addstr(2, title_x, title, self.COLOR_ACCENT)
        self.stdscr.addstr(4, inst1_x, instructions1, self.COLOR_INFO)
        self.stdscr.addstr(5, inst2_x, instructions2, self.COLOR_INFO)
        
        if not ports:
            msg = "Error: No serial devices detected"
            self.stdscr.addstr(7, max(0, (w - len(msg)) // 2), msg, self.COLOR_WARN)
        else:
            msg = f"Detected {len(ports)} serial port(s): {', '.join(ports)}"
            msg_x = max(0, (w - min(len(msg), w - 4)) // 2)
            self.stdscr.addstr(7, msg_x, msg[:w - 4], self.COLOR_ACCENT)
        
        mapping_start_row = 10
        mapping_width = 50
        mapping_x = max(0, (w - mapping_width) // 2)
        
        for i in range(4):
            row = mapping_start_row + i * 2
            
            motor_label = f"Motor {i + 1}:"
            assignment = device_options[motor_indices[i]]
            
            marker = "→ " if i == selected_motor else "  "
            line = f"{marker}{motor_label:<12} {assignment}"
            
            attr = self.COLOR_ACCENT if i == selected_motor else self.COLOR_NORMAL
            if assignment != "(unassigned)":
                attr |= curses.A_BOLD
            
            try:
                self.stdscr.addstr(row, mapping_x, line, attr)
            except:
                pass
        
        if device_options:
            options_start_row = mapping_start_row + 10
            options_title = f"Available options for Motor {selected_motor + 1}:"
            self.stdscr.addstr(options_start_row - 1, max(0, (w - len(options_title)) // 2), 
                                options_title, self.COLOR_ACCENT)
            
            visible_options = min(8, h - options_start_row - 2)
            
            for i in range(visible_options):
                opt_idx = scroll_offset + i
                if opt_idx >= len(device_options):
                    break
                
                option = device_options[opt_idx]
                is_current = (opt_idx == motor_indices[selected_motor])
                
                marker = "◆ " if is_current else "  "
                line = f"{marker}{option}"
                
                attr = self.COLOR_ACCENT if is_current else self.COLOR_NORMAL
                
                try:
                    self.stdscr.addstr(options_start_row + i, max(0, (w - 40) // 2), 
                                    line, attr)
                except:
                    pass
            
            if len(device_options) > visible_options:
                scroll_info = f"[{scroll_offset + 1}-{min(scroll_offset + visible_options, len(device_options))}/{len(device_options)}]"
                try:
                    self.stdscr.addstr(options_start_row + visible_options, 
                                    max(0, (w - len(scroll_info)) // 2), scroll_info, self.COLOR_INFO)
                except:
                    pass
        
        self.stdscr.refresh()
        
        key = self.stdscr.getch()
        
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
                    self.motor_mapping[i] = None
                else:
                    self.motor_mapping[i] = device_options[motor_indices[i]]
            
            self.config['motor_mapping'] = self.motor_mapping
            save_config(self.config)
            
            self.log("Motor mapping saved successfully")
            break
        elif key == 27:
            self.log("Motor mapping cancelled")
            break
    
    self.stdscr.nodelay(1)
    self.stdscr.timeout(100)