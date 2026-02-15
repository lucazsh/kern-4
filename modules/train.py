import numpy as np
import os
import time

try:
    import pybullet as p
    import pybullet_data
    PYBULLET_AVAILABLE = True
except ImportError:
    PYBULLET_AVAILABLE = False

# This is very basic for now, will be better in the future
# Hopefully....
def build_param_shapes(obs_dim, hidden, action_dim):
    shapes = [
        (hidden, obs_dim),
        (hidden,),
        (action_dim, hidden),
        (action_dim,)
    ]
    sizes = [int(np.prod(s)) for s in shapes]
    return shapes, sizes

def unflatten_params(vector, shapes):
    params = []
    idx = 0
    for s in shapes:
        size = int(np.prod(s))
        flat = vector[idx:idx+size]
        params.append(flat.reshape(s))
        idx += size
    return params

def mlp_forward(params_vec, obs, shapes):
    W1, b1, W2, b2 = unflatten_params(params_vec, shapes)
    h = np.tanh(W1.dot(obs) + b1)
    out = W2.dot(h) + b2
    return out

class PyBullet:
    def __init__(self, urdf_path="robot.urdf", target_pos=(0.3, 0, 0.05), 
                 motor_indices=None, gui=False, hardware_callback=None):
        self.urdf_path = urdf_path
        self.target_pos = target_pos
        self.gui = gui
        self.client = None
        self.robot = None
        self.target = None
        self.motor_indices = motor_indices
        self.dt = 1.0 / 240.0
        self.hardware_callback = hardware_callback
        self.step_counter = 0
        self.last_distance = None
        self.total_reward = 0.0
        self.episode_count = 0
        
    def start(self):
        if not PYBULLET_AVAILABLE:
            raise ImportError("PyBullet not available")
        
        # Tried to match the dark mode theme 
        if self.gui:
            self.client = p.connect(p.GUI)
            p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
            p.configureDebugVisualizer(p.COV_ENABLE_SHADOWS, 1)
            p.configureDebugVisualizer(p.COV_ENABLE_RGB_BUFFER_PREVIEW, 0)
            p.configureDebugVisualizer(p.COV_ENABLE_DEPTH_BUFFER_PREVIEW, 0)
            p.configureDebugVisualizer(p.COV_ENABLE_SEGMENTATION_MARK_PREVIEW, 0)
            p.configureDebugVisualizer(rgbBackground=[0.05, 0.05, 0.1])
        else:
            self.client = p.connect(p.DIRECT)
        
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.resetSimulation()
        p.setGravity(0, 0, -9.81)
        
        plane = p.loadURDF("plane.urdf")
        p.changeVisualShape(plane, -1, rgbaColor=[0.1, 0.1, 0.15, 1])
        
        if not os.path.exists(self.urdf_path):
            raise FileNotFoundError(f"URDF not found: {self.urdf_path}")
                
        self.robot = p.loadURDF(self.urdf_path, useFixedBase=True, globalScaling=0.5)

        robot_pos, _ = p.getBasePositionAndOrientation(self.robot)

        num_joints = p.getNumJoints(self.robot)
        if num_joints > 0:
            ee_state = p.getLinkState(self.robot, num_joints - 1)
            ee_pos = ee_state[0]
            cube_position = [
                ee_pos[0] + 9.5,
                ee_pos[1],
                1.5
            ]
        else:
            cube_position = [
                robot_pos[0] + 12.0,
                robot_pos[1],
                1.5
            ]

        self.target_pos = tuple(cube_position)

        cube_size = [2.0, 2.0, 2.0]
        col_visual = p.createVisualShape(shapeType=p.GEOM_BOX, halfExtents=cube_size, 
                                        rgbaColor=[1, 0, 0, 1])
        col_collision = p.createCollisionShape(shapeType=p.GEOM_BOX, halfExtents=cube_size)
        
        self.target = p.createMultiBody(baseMass=0.1, 
                                    baseCollisionShapeIndex=col_collision,
                                    baseVisualShapeIndex=col_visual, 
                                    basePosition=cube_position)
        
        self.joint_info = {}
        self.joint_indices = []
        for i in range(p.getNumJoints(self.robot)):
            info = p.getJointInfo(self.robot, i)
            jtype = info[2]
            if jtype in (p.JOINT_REVOLUTE, p.JOINT_PRISMATIC, p.JOINT_SPHERICAL):
                self.joint_indices.append(i)
                self.joint_info[i] = info
        
        if self.motor_indices is None:
            if len(self.joint_indices) < 4:
                raise ValueError("URDF needs at least 4 controllable joints")
            self.motor_indices = self.joint_indices[:4]
        
        for j in self.joint_indices:
            p.setJointMotorControl2(self.robot, j, p.VELOCITY_CONTROL, force=0)
        
        self.end_effector_index = self.motor_indices[-1]
        
        self.num_motors = len(self.motor_indices)
        self.commanded_vel = np.zeros(self.num_motors, dtype=np.float32)
        q_init = []
        for mi in self.motor_indices:
            s = p.getJointState(self.robot, mi)
            q_init.append(s[0] if s else 0.0)
        self.commanded_pos = np.array(q_init, dtype=np.float32)
        
        self.max_joint_velocity = 1.0
        self.max_joint_acceleration = 5.0
        
    def soft_reset(self):
        self.step_counter = 0
        self.total_reward = 0.0
        self.last_distance = None
        self.episode_count += 1
        
        if self.motor_indices and self.robot:
            q_init = []
            for mi in self.motor_indices:
                s = p.getJointState(self.robot, mi)
                q_init.append(s[0] if s else 0.0)
            self.commanded_pos = np.array(q_init, dtype=np.float32)
            self.commanded_vel = np.zeros(self.num_motors, dtype=np.float32)
        
        return self._get_obs()
    
    def _get_obs(self):
        q = []
        for mi in self.motor_indices:
            s = p.getJointState(self.robot, mi)
            q.append(s[0] if s else 0.0)
        
        ee_state = p.getLinkState(self.robot, self.end_effector_index, 
                                  computeForwardKinematics=True)
        ee_pos = ee_state[0]
        tx, ty, tz = self.target_pos
        rel = [tx - ee_pos[0], ty - ee_pos[1], tz - ee_pos[2]]
        
        return np.array(q + list(rel), dtype=np.float32)
    
    def step(self, action):
        action = np.array(action, dtype=np.float32)
        dt = self.dt
        
        actual_positions = []
        for mi in self.motor_indices:
            s = p.getJointState(self.robot, mi)
            actual_positions.append(s[0] if s else 0.0)
        actual_positions = np.array(actual_positions, dtype=np.float32)
        
        if not hasattr(self, 'commanded_pos') or self.commanded_pos is None:
            self.commanded_pos = actual_positions.copy()
        if not hasattr(self, 'commanded_vel') or self.commanded_vel is None:
            self.commanded_vel = np.zeros_like(actual_positions)
        
        pos_error = actual_positions - self.commanded_pos
        big_error_mask = np.abs(pos_error) > 0.1
        if np.any(big_error_mask):
            self.commanded_pos[big_error_mask] = actual_positions[big_error_mask]
        
        desired_velocity = (action - self.commanded_pos) / dt
        desired_velocity = np.clip(desired_velocity, -self.max_joint_velocity, 
                                  self.max_joint_velocity)
        
        accel_needed = (desired_velocity - self.commanded_vel) / dt
        accel_clipped = np.clip(accel_needed, -self.max_joint_acceleration, 
                               self.max_joint_acceleration)
        
        self.commanded_vel += accel_clipped * dt
        self.commanded_pos += self.commanded_vel * dt
        
        for idx, mj in enumerate(self.motor_indices):
            targ = float(self.commanded_pos[idx])
            p.setJointMotorControl2(self.robot, mj, p.POSITION_CONTROL,
                                   targetPosition=targ, force=200)
        
        if self.hardware_callback is not None:
            try:
                self.hardware_callback(self.commanded_pos.copy())
            except Exception as e:
                pass
        
        p.stepSimulation()
        if self.gui:
            time.sleep(dt)
        
        self.step_counter += 1
        
        obs = self._get_obs()
        ee_state = p.getLinkState(self.robot, self.end_effector_index, 
                                  computeForwardKinematics=True)
        ee_pos = np.array(ee_state[0])
        target = np.array(self.target_pos)
        dist = np.linalg.norm(ee_pos - target)
        
        distance_reward = -dist * 2.0
        improvement_reward = 0.0
        if self.last_distance is not None:
            improvement = self.last_distance - dist
            improvement_reward = improvement * 10.0
        self.last_distance = dist
        
        touch_reward = 50.0 if dist < 0.04 else 0.0
        action_penalty = -np.sum(np.square(self.commanded_vel)) * 0.01
        
        reward = distance_reward + improvement_reward + touch_reward + action_penalty
        self.total_reward += reward
        
        done = False
        info = {
            'touched': dist < 0.04,
            'total_reward': self.total_reward,
            'distance': dist
        }
        
        return obs, reward, done, info
    
    def close(self):
        if self.client is not None:
            p.disconnect(self.client)
            self.client = None

# Gotta run this forever, lol
class Trainer:
    def __init__(self, env, obs_dim, action_dim, stop_event, hidden=32, update_interval=100):
        self.env = env
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.hidden = hidden
        self.stop_event = stop_event
        self.update_interval = update_interval
        
        self.shapes, self.sizes = build_param_shapes(obs_dim, hidden, action_dim)
        total = sum(self.sizes)
        
        self.params = np.zeros(total)
        self.step_count = 0
        self.best_reward = -float('inf')
        
    def train_continuously(self, status_callback=None):
        obs = self.env.soft_reset()
        
        pop_size = 10
        elite_size = 3
        population = [np.random.randn(self.params.size) * 0.5 for _ in range(pop_size)]
        scores = np.zeros(pop_size)
        
        current_individual = 0
        evaluation_steps = 200
        
        while not self.stop_event.is_set():
            current_params = population[current_individual]
            
            total_reward = 0.0
            for _ in range(evaluation_steps):
                if self.stop_event.is_set():
                    break
                
                act = mlp_forward(current_params, obs, self.shapes)
                act = np.clip(act, -2.0, 2.0)
                obs, reward, done, info = self.env.step(act)
                total_reward += reward
                self.step_count += 1
            
            scores[current_individual] = total_reward
            
            if status_callback and self.step_count % 50 == 0:
                status_callback(self.step_count, total_reward, info.get('distance', 0))
            
            current_individual += 1
            
            if current_individual >= pop_size:
                elite_idx = np.argsort(scores)[-elite_size:]
                
                new_population = []
                for i in range(pop_size):
                    if i < elite_size:
                        new_population.append(population[elite_idx[i]].copy())
                    else:
                        parent = population[np.random.choice(elite_idx)]
                        child = parent + np.random.randn(parent.size) * 0.3
                        new_population.append(child)
                
                population = new_population
                
                best_idx = elite_idx[-1]
                if scores[best_idx] > self.best_reward:
                    self.best_reward = scores[best_idx]
                    np.save("kern_policy.npy", population[best_idx])
                
                scores = np.zeros(pop_size)
                current_individual = 0
        
        return self.params
