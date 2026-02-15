import os
import time
import threading
from .. import train
from ..utils import save_targets
from ..train import PYBULLET_AVAILABLE, PyBullet

class kern_train:
    def __init__(self):
        self.motor_mapping = [None, None, None, None]
        self.device_states = {}
        self.staged_targets = {}
        self.accumulation_counter = 0
        self.aggregation_threshold = 400 # You can change it, but it worked perfectly for me
        self.angle_to_steps_scale = 100.0 # Might need to change this one too idk

    def hardware_callback(self, action):
        try:
            scale = self.angle_to_steps_scale
            
            for i in range(4):
                if self.motor_mapping[i] is None:
                    continue
                
                mapping_str = self.motor_mapping[i]
                if ':' not in mapping_str:
                    continue
                
                port, axis = mapping_str.split(':', 1)
                angle_rad = float(action[i])
                gear = self.gear_ratios[i] if i < len(self.gear_ratios) else 1.0
                steps = int(round(angle_rad * gear * scale))
                
                MAX_STEPS = 1000000
                steps = max(-MAX_STEPS, min(MAX_STEPS, steps))
                
                key = f"{port}:{axis}"
                self.staged_targets[key] = int(steps)
            
            self.accumulation_counter += 1
            
            if self.accumulation_counter >= self.aggregation_threshold:
                for k, staged_abs in list(self.staged_targets.items()):
                    port, axis = k.split(":", 1)
                    
                    if k not in self.device_states:
                        self.device_states[k] = {
                            'current_steps': 0,
                            'target_steps': 0,
                            'lock': threading.Lock()
                        }
                    
                    with self.device_states[k]['lock']:
                        current = int(self.device_states[k].get('current_steps', 0))
                        delta = int(staged_abs) - current
                        self.device_states[k]['target_steps'] = int(staged_abs)
                    
                    if delta == 0:
                        continue
                    
                    dev = None
                    for d in self.devices:
                        if d.port == port:
                            dev = d
                            break
                    
                    if dev and dev.connected:
                        cmd = f"MOVE {axis} {delta}"
                        dev.send(cmd)
                        
                        with self.device_states[k]['lock']:
                            self.device_states[k]['current_steps'] = int(staged_abs)
                
                save_targets({k: v['target_steps'] for k, v in self.device_states.items()})
                
                self.accumulation_counter = 0
                self.staged_targets.clear()
        
        except Exception as e:
            self.log(f"Hardware callback error: {e}", "ERROR")
    
    def start_training(self):
        if not PYBULLET_AVAILABLE:
            self.log("PyBullet not available - cannot start training", "ERROR")
            self.log("Install it with: pip install pybullet", "WARN")
            return
        
        if self.training_active:
            self.log("Training already active", "WARN")
            return
        
        urdf_path = "./URDF/robot.urdf"
        if not os.path.exists(urdf_path):
            self.log(f"URDF not found: {urdf_path}", "ERROR")
            # If you lost it for some reason, yk where to grab it again
            return
        
        self.log("Starting AI training...")
        self.training_stop_event.clear()
        self.training_active = True
        
        def training_thread_func():
            try:
                env = PyBullet(
                    urdf_path=urdf_path,
                    target_pos=(0.3, 0.0, 0.05),
                    motor_indices=None,
                    gui=True,
                    hardware_callback=lambda action: kern_train.hardware_callback(self, action)
                )
                env.start()
                self.training_env = env
                
                trainer = train.Trainer(
                    env, obs_dim=7, action_dim=4,
                    stop_event=self.training_stop_event,
                    hidden=32, update_interval=100
                )
                
                def status_cb(steps, reward, distance):
                    self.log(f"Training: Step {steps}, Reward {reward:.2f}, Dist {distance:.3f}")
                
                trainer.train_continuously(status_callback=status_cb)
                
                env.close()
                self.training_env = None
                
            except Exception as e:
                self.log(f"Training error: {e}", "ERROR")
            
            finally:
                self.training_active = False
                self.log("Training stopped")
        
        self.training_thread = threading.Thread(target=training_thread_func, daemon=True)
        self.training_thread.start()

    def stop_training(self):
        if not self.training_active:
            self.log("Training not active", "WARN")
            return
        
        self.log("Stopping training...")
        self.training_stop_event.set()
        
        for dev in self.devices:
            dev.stop_all()
        
        time.sleep(0.5)
        
        self.log("Returning motors to home position (0)...")
        
        for i in range(4):
            if self.motor_mapping[i]:
                port, axis = self.motor_mapping[i].split(':')
                dev = next((d for d in self.devices if d.port == port), None)
                if dev and dev.connected:
                    dev.send("GETPOS")
        
        time.sleep(0.2)
        
        for dev in self.devices:
            dev.process_queue()
        
        for i in range(4):
            if self.motor_mapping[i]:
                port, axis = self.motor_mapping[i].split(':')
                dev = next((d for d in self.devices if d.port == port), None)
                if dev and dev.connected:
                    current_pos = dev.positions.get(axis, 0)
                    delta = -current_pos
                    
                    if delta != 0:
                        dev.move_axis(axis, delta)
                        self.log(f"M{i+1} ({axis}): {current_pos} → 0 (Δ{delta})")
                        
                        key = f"{port}:{axis}"
                        if key in self.device_states:
                            with self.device_states[key]['lock']:
                                self.device_states[key]['current_steps'] = 0
                                self.device_states[key]['target_steps'] = 0
        
        save_targets({k: 0 for k in self.device_states.keys()})