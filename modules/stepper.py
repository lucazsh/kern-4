import serial
import serial.tools.list_ports
import time
import re
import threading
import queue

def list_serial_ports():
    return [p.device for p in serial.tools.list_ports.comports()]

def safe_write(ser, data):
    try:
        ser.write((data + '\n').encode())
        return True
    except Exception as e:
        return False

def serial_reader_thread(ser, q, stop_event):
    buf = ""
    while not stop_event.is_set() and ser and getattr(ser, "is_open", False):
        try:
            data = ser.read(ser.in_waiting or 1)
            if not data:
                time.sleep(0.01)
                continue
            decoded = data.decode(errors='ignore')
            buf += decoded
            while '\n' in buf:
                line, buf = buf.split('\n', 1)
                line = line.strip()
                if line:
                    q.put(line)
        except Exception as e:
            q.put(f"__ERROR__ {e}")
            break

class device:
    def __init__(self, port, baud=115200):
        self.port = port
        self.baud = baud
        self.ser = None
        self.q = queue.Queue()
        self.reader_stop = threading.Event()
        self.reader_thread = None
        self.positions = {'X': 0, 'Y': 0, 'Z': 0}
        self.connected = False
        
    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.1)
            self.connected = True
            self.reader_stop.clear()
            self.reader_thread = threading.Thread(
                target=serial_reader_thread, 
                args=(self.ser, self.q, self.reader_stop), 
                daemon=True
            )
            self.reader_thread.start()
            return True
        except Exception as e:
            self.connected = False
            return False
    
    def disconnect(self):
        try:
            self.reader_stop.set()
            time.sleep(0.03)
            if self.ser and getattr(self.ser, "is_open", False):
                self.ser.close()
            self.connected = False
        except:
            pass
    
    def send(self, cmd):
        if self.ser and getattr(self.ser, "is_open", False):
            return safe_write(self.ser, cmd)
        return False
    
    def process_queue(self):
        messages = []
        try:
            while not self.q.empty():
                line = self.q.get_nowait()
                if isinstance(line, str) and not line.startswith("__ERROR__"):
                    if line.upper().startswith("POS"):
                        for axis in ['X', 'Y', 'Z']:
                            m = re.search(rf"{axis}:([-\d]+)", line, re.IGNORECASE)
                            if m:
                                self.positions[axis] = int(m.group(1))
                    else:
                        messages.append(line)
        except queue.Empty:
            pass
        return messages
    
    def move_axis(self, axis, steps):
        cmd = f"MOVE {axis} {steps}"
        return self.send(cmd)
    
    def move_all(self, dx, dy, dz):
        cmd = f"MALL {dx} {dy} {dz}"
        return self.send(cmd)
    
    def stop_all(self):
        return self.send("STOP")
    
    def set_speed(self, speed):
        cmd = f"SETSPD {speed}"
        return self.send(cmd)
    
    def set_acceleration(self, accel):
        cmd = f"SETACC {accel}"
        return self.send(cmd)