from . import stepper

class kern_devices:
    def scan_devices(self):
        self.log("Scanning for serial devices...")
        ports = stepper.list_serial_ports()
        
        if not ports:
            self.log("No serial ports found", "WARN")
            return
        
        self.log(f"Found {len(ports)} serial port(s)")
        
        for port in ports:
            if any(d.port == port for d in self.devices):
                self.log(f"Already connected to {port}", "INFO")
                continue
            
            dev = stepper.device(port, baud=115200)
            if dev.connect():
                self.devices.append(dev)
                self.log(f"Connected to {port}", "INFO")
            else:
                self.log(f"Failed to connect to {port}", "WARN")

    def disconnect_all(self):
        self.log("Disconnecting all devices...")
        
        for dev in self.devices:
            dev.disconnect()
        
        self.log("All devices disconnected")