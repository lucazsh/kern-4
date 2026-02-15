import time
from datetime import datetime
import curses

# arrows: ← ↑ → ↓ ←→ ● ○ (so I can copy them more easilly)
class control:
    def __init__(self, parent_ui):
        self.parent_ui = parent_ui
        self.stdscr = parent_ui.stdscr
        self.config = parent_ui.config
        self.devices = parent_ui.devices

    def control(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        self.stdscr.nodelay(0)
        
        step_sizes = [1, 10, 50, 100, 500, 1000]
        selected_step_idx = 2
        selected_motor = 0
        
        control_log = []
        
        target_pos = {}

        motor_mapping = self.config.get('motor_mapping', [None, None, None, None])

        def add_control_log(msg):
            control_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
            if len(control_log) > 20:
                control_log.pop(0)
        
        add_control_log("Manual control mode started")
        
        for i in range(4):
            if motor_mapping[i]:
                port, axis = motor_mapping[i].split(':')
                dev = next((d for d in self.devices if d.port == port), None)
                if dev and dev.connected:
                    key = f"{port}:{axis}"
                    target_pos[key] = dev.positions.get(axis, 0)

        for dev in self.devices:
            if dev.connected:
                dev.send("GETPOS")

        time.sleep(0.2)
        for dev in self.devices:
            dev.process_queue()
        
        while True:
            self.stdscr.clear()
            
            title = "==== MANUAL MOTOR CONTROL ===="
            self.stdscr.addstr(2, max(0, (w - len(title)) // 2), title, self.parent_ui.COLOR_ACCENT)
            
            instructions = [
                "Controls:",
                "  ← → : Move selected motor backward/forward",
                "  ↑ ↓ : Select motor (1-4)",
                "  [ ] : Decrease/Increase step size",
                "  SPACE : Stop all motors",
                "  H : Home all motors (move to position 0)",
                "  R : Refresh positions from devices",
                "  ESC : Exit manual control",
            ]
            
            start_row = 5
            for i, line in enumerate(instructions):
                try:
                    line_x = max(0, (w - 50) // 2)
                    attr = self.parent_ui.COLOR_ACCENT if line.startswith("  ") else self.parent_ui.COLOR_NORMAL
                    self.stdscr.addstr(start_row + i, line_x, line, attr)
                except:
                    pass
            
            settings_row = start_row + len(instructions) + 2
            step_size = step_sizes[selected_step_idx]
            
            try:
                self.stdscr.addstr(settings_row, max(0, (w - 40) // 2), 
                                f"Step Size: {step_size} steps", self.parent_ui.COLOR_HIGHLIGHT)
                self.stdscr.addstr(settings_row + 1, max(0, (w - 40) // 2), 
                                f"Selected Motor: {selected_motor + 1}", self.parent_ui.COLOR_HIGHLIGHT)
            except:
                pass
            
            motor_status_row = settings_row + 4
            
            try:
                self.stdscr.addstr(motor_status_row, max(0, (w - 30) // 2), 
                                "Motor Status:", self.parent_ui.COLOR_ACCENT)
            except:
                pass
            
            for i in range(4):
                row = motor_status_row + 2 + i * 2
                
                if motor_mapping[i] is None:
                    mapping_str = "(unassigned)"
                    status_color = self.parent_ui.COLOR_WARN
                else:
                    mapping_str = motor_mapping[i]
                    port, axis = mapping_str.split(':')
                    
                    dev = None
                    for d in self.devices:
                        if d.port == port:
                            dev = d
                            break
                    
                    if dev and dev.connected:
                        pos = dev.positions.get(axis, 0)
                        mapping_str = f"{port}:{axis} → Pos: {pos:6d} steps"
                        status_color = self.parent_ui.COLOR_ACCENT
                    else:
                        mapping_str = f"{port}:{axis} → DISCONNECTED"
                        status_color = self.parent_ui.COLOR_ERROR
                
                marker = "→ " if i == selected_motor else "  "
                line = f"{marker}M{i + 1}: {mapping_str}"
                
                attr = status_color
                if i == selected_motor:
                    attr |= curses.A_REVERSE
                
                try:
                    self.stdscr.addstr(row, max(0, (w - 60) // 2), line[:w-4], attr)
                except:
                    pass
            
            log_start_row = motor_status_row + 12
            
            try:
                self.stdscr.addstr(log_start_row, max(0, (w - 20) // 2), 
                                "Activity Log:", self.parent_ui.COLOR_ACCENT)
            except:
                pass
            
            for i, msg in enumerate(control_log[-10:]):
                try:
                    self.stdscr.addstr(log_start_row + 2 + i, 2, msg[:w-4], self.parent_ui.COLOR_INFO)
                except:
                    pass
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            
            if key == 27:
                add_control_log("Exiting manual control mode")
                break
            elif key == curses.KEY_UP:
                selected_motor = max(0, selected_motor - 1)
                add_control_log(f"Selected Motor {selected_motor + 1}")
            elif key == curses.KEY_DOWN:
                selected_motor = min(3, selected_motor + 1)
                add_control_log(f"Selected Motor {selected_motor + 1}")
            elif key == ord('['):
                selected_step_idx = max(0, selected_step_idx - 1)
                add_control_log(f"Step size: {step_sizes[selected_step_idx]} steps")
            elif key == ord(']'):
                selected_step_idx = min(len(step_sizes) - 1, selected_step_idx + 1)
                add_control_log(f"Step size: {step_sizes[selected_step_idx]} steps")
            elif key == curses.KEY_LEFT or key == curses.KEY_RIGHT:
                if motor_mapping[selected_motor]:
                    port, axis = motor_mapping[selected_motor].split(':')
                    dev = next((d for d in self.devices if d.port == port), None)
                    if dev and dev.connected:
                        key_str = f"{port}:{axis}"
                        if key_str not in target_pos:
                            target_pos[key_str] = dev.positions.get(axis, 0)
                        delta = step_size if key == curses.KEY_RIGHT else -step_size
                        target_pos[key_str] += delta
                        dev.move_axis(axis, delta)
                        arrow = "→" if delta > 0 else "←"
                        add_control_log(f"M{selected_motor + 1} ({axis}) {arrow} {abs(delta)} steps")
                    else:
                        add_control_log(f"M{selected_motor + 1}: Device not connected")
                else:
                    add_control_log(f"M{selected_motor + 1}: Not assigned")
            elif key == ord(' '):
                for dev in self.devices:
                    if dev.connected:
                        dev.stop_all()
                add_control_log("EMERGENCY STOP - All motors stopped")
            elif key in (ord('r'), ord('R')):
                add_control_log("Refreshing positions from devices...")
                for dev in self.devices:
                    if dev.connected:
                        dev.send("GETPOS")
                time.sleep(0.2)
                for dev in self.devices:
                    dev.process_queue()
                add_control_log("Positions refreshed")
            elif key in (ord('h'), ord('H')):
                add_control_log("HOMING - Moving all motors to position 0...")
                homed_count = 0
                for i in range(4):
                    if motor_mapping[i]:
                        port, axis = motor_mapping[i].split(':')
                        dev = next((d for d in self.devices if d.port == port), None)
                        if dev and dev.connected:
                            key_str = f"{port}:{axis}"
                            if key_str not in target_pos:
                                target_pos[key_str] = dev.positions.get(axis, 0)
                            current_target = target_pos[key_str]
                            delta = -current_target
                            if delta != 0:
                                dev.move_axis(axis, delta)
                                dev.positions[axis] = 0
                                add_control_log(f"M{i+1} ({axis}): {current_target} → 0 (Δ{delta})")
                                homed_count += 1
                            else:
                                add_control_log(f"M{i+1} ({axis}): already at home (0)")
                        else:
                            add_control_log(f"M{i+1}: Device not connected - skipped")
                    else:
                        add_control_log(f"M{i+1}: Not assigned - skipped")
                add_control_log(f"HOME complete - {homed_count} motor(s) homed" if homed_count else "HOME complete - no motors needed homing")
            
            for dev in self.devices:
                dev.process_queue()
        
        self.stdscr.nodelay(1)
        self.stdscr.timeout(100)
        self.parent_ui.log("Manual control mode exited")