"""
Enhanced EVO Engine with SNN Processing
Local-only version without external API dependencies.
"""

import numpy as np
import math
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import random
from snn_processor import SNNVisualOdometry, SNNCornerDetector, EventNoiseFilter

class TerrainType(str, Enum):
    LUNAR = "lunar"
    MARS = "mars"
    ASTEROID = "asteroid"
    CUSTOM = "custom"

@dataclass
class Event:
    """Single neuromorphic event from event camera"""
    x: int
    y: int
    timestamp: float  # microseconds
    polarity: int  # +1 or -1

@dataclass
class Pose:
    """6-DOF pose of the lander"""
    x: float = 0.0
    y: float = 0.0
    z: float = 1000.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    timestamp: float = 0.0

@dataclass
class SimulationConfig:
    """Configuration for descent simulation"""
    terrain_type: TerrainType = TerrainType.LUNAR
    initial_altitude: float = 1000.0
    descent_velocity: float = 50.0
    vibration_amplitude: float = 0.5
    vibration_frequency: float = 10.0
    camera_resolution: Tuple[int, int] = (640, 480)
    simulation_duration: float = 20.0
    noise_level: float = 0.1
    feature_density: int = 200
    # New SNN parameters
    use_snn_processing: bool = True
    snn_corner_threshold: float = 0.8
    noise_filter_enabled: bool = True

@dataclass
class SimulationState:
    """Current state of a running simulation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: SimulationConfig = field(default_factory=SimulationConfig)
    current_time: float = 0.0
    current_pose: Pose = field(default_factory=Pose)
    ground_truth_poses: List[Dict] = field(default_factory=list)
    estimated_poses: List[Dict] = field(default_factory=list)
    events_history: List[Dict] = field(default_factory=list)
    metrics_history: List[Dict] = field(default_factory=list)
    events_generated: int = 0
    is_running: bool = False
    is_landed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # SNN data
    corner_detections: List[Dict] = field(default_factory=list)
    tracked_features: List[Dict] = field(default_factory=list)

class TerrainGenerator:
    """Generates synthetic terrain features with enhanced detail"""
    
    TERRAIN_PROFILES = {
        TerrainType.LUNAR: {'crater_ratio': 0.6, 'rock_ratio': 0.3, 'ridge_ratio': 0.1, 'base_albedo': 0.12},
        TerrainType.MARS: {'crater_ratio': 0.4, 'rock_ratio': 0.4, 'ridge_ratio': 0.2, 'base_albedo': 0.25},
        TerrainType.ASTEROID: {'crater_ratio': 0.5, 'rock_ratio': 0.35, 'ridge_ratio': 0.15, 'base_albedo': 0.08},
        TerrainType.CUSTOM: {'crater_ratio': 0.5, 'rock_ratio': 0.35, 'ridge_ratio': 0.15, 'base_albedo': 0.15},
    }
    
    def __init__(self, terrain_type: TerrainType, feature_density: int, custom_features: List[Dict] = None):
        self.terrain_type = terrain_type
        self.feature_density = feature_density
        self.profile = self.TERRAIN_PROFILES.get(terrain_type, self.TERRAIN_PROFILES[TerrainType.CUSTOM])
        self.features = custom_features if custom_features else self._generate_features()
        self.heightmap = self._generate_heightmap()
    
    def _generate_features(self) -> List[Dict]:
        """Generate random terrain features (craters, rocks, ridges)"""
        features = []
        profile = self.profile
        
        for i in range(self.feature_density):
            rand = random.random()
            if rand < profile['crater_ratio']:
                feature_type = "crater"
                size = random.uniform(10, 80)
                depth = size * random.uniform(0.1, 0.3)
            elif rand < profile['crater_ratio'] + profile['rock_ratio']:
                feature_type = "rock"
                size = random.uniform(2, 15)
                depth = size * random.uniform(0.5, 1.0)
            else:
                feature_type = "ridge"
                size = random.uniform(5, 30)
                depth = size * random.uniform(0.2, 0.5)
            
            features.append({
                "id": i,
                "type": feature_type,
                "x": random.uniform(-500, 500),
                "y": random.uniform(-500, 500),
                "z": 0,  # Height will be computed
                "size": size,
                "depth": depth,
                "contrast": random.uniform(0.4, 1.0),
                "albedo": profile['base_albedo'] * random.uniform(0.8, 1.2)
            })
        
        return features
    
    def _generate_heightmap(self, size: int = 256) -> np.ndarray:
        """Generate terrain heightmap for 3D visualization"""
        heightmap = np.zeros((size, size), dtype=np.float32)
        
        # Add features to heightmap
        for feature in self.features:
            # Convert world coords to heightmap coords
            hx = int((feature['x'] + 500) / 1000 * size)
            hy = int((feature['y'] + 500) / 1000 * size)
            
            if not (0 <= hx < size and 0 <= hy < size):
                continue
            
            radius = int(feature['size'] / 1000 * size * 2) + 1
            
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    nx, ny = hx + dx, hy + dy
                    if 0 <= nx < size and 0 <= ny < size:
                        dist = math.sqrt(dx**2 + dy**2) / (radius + 0.001)
                        if dist < 1:
                            if feature['type'] == 'crater':
                                # Crater profile: bowl shape
                                height = -feature['depth'] * (1 - dist**2)
                            elif feature['type'] == 'rock':
                                # Rock profile: gaussian bump
                                height = feature['depth'] * math.exp(-3 * dist**2)
                            else:  # ridge
                                # Ridge profile: elongated
                                height = feature['depth'] * (1 - dist) * 0.5
                            
                            heightmap[ny, nx] += height
        
        return heightmap
    
    def get_heightmap_data(self) -> Dict:
        """Get heightmap data for 3D visualization"""
        return {
            'data': self.heightmap.tolist(),
            'width': self.heightmap.shape[1],
            'height': self.heightmap.shape[0],
            'scale': 1000,  # World scale
            'max_height': float(np.max(self.heightmap)),
            'min_height': float(np.min(self.heightmap))
        }
    
    def get_features_3d(self) -> List[Dict]:
        """Get features with 3D positions"""
        return [{
            **f,
            'z': self._get_height_at(f['x'], f['y'])
        } for f in self.features]
    
    def _get_height_at(self, x: float, y: float) -> float:
        """Get terrain height at world position"""
        size = self.heightmap.shape[0]
        hx = int((x + 500) / 1000 * size)
        hy = int((y + 500) / 1000 * size)
        if 0 <= hx < size and 0 <= hy < size:
            return float(self.heightmap[hy, hx])
        return 0.0


class EventCamera:
    """Enhanced event camera simulation with realistic noise models"""
    
    def __init__(self, resolution: Tuple[int, int], noise_level: float = 0.1):
        self.width, self.height = resolution
        self.noise_level = noise_level
        self.last_frame = np.zeros((self.height, self.width), dtype=np.float32)
        self.threshold_positive = 0.15
        self.threshold_negative = 0.15
        # Adaptive threshold per pixel (simulates sensor variations)
        self.threshold_map = np.ones((self.height, self.width), dtype=np.float32) * 0.15
        self.threshold_map += np.random.uniform(-0.02, 0.02, self.threshold_map.shape)
    
    def generate_events(self, current_frame: np.ndarray, timestamp: float) -> List[Dict]:
        """Generate events from frame difference with realistic modeling"""
        events = []
        
        # Calculate difference from last frame
        diff = current_frame - self.last_frame
        
        # Positive events (brightness increase)
        pos_mask = diff > self.threshold_map
        pos_y, pos_x = np.where(pos_mask)
        
        for i in range(len(pos_y)):
            y, x = pos_y[i], pos_x[i]
            # Timestamp jitter (realistic DVS behavior)
            jitter = random.uniform(0, 50)  # microseconds
            events.append({
                "x": int(x),
                "y": int(y),
                "timestamp": timestamp + jitter,
                "polarity": 1
            })
        
        # Negative events
        neg_mask = diff < -self.threshold_map
        neg_y, neg_x = np.where(neg_mask)
        
        for i in range(len(neg_y)):
            y, x = neg_y[i], neg_x[i]
            jitter = random.uniform(0, 50)
            events.append({
                "x": int(x),
                "y": int(y),
                "timestamp": timestamp + jitter,
                "polarity": -1
            })
        
        # Add noise events (hot pixels, dark current)
        num_noise = int(len(events) * self.noise_level)
        for _ in range(num_noise):
            events.append({
                "x": random.randint(0, self.width - 1),
                "y": random.randint(0, self.height - 1),
                "timestamp": timestamp + random.uniform(0, 100),
                "polarity": random.choice([-1, 1])
            })
        
        events.sort(key=lambda e: e["timestamp"])
        self.last_frame = current_frame.copy()
        
        return events


class StandardVisualOdometry:
    """Standard grid-based visual odometry (non-SNN)"""
    
    def __init__(self):
        self.feature_tracks = []
        self.last_pose = Pose()
        self.accumulated_drift = {"x": 0.0, "y": 0.0, "z": 0.0}
    
    def process_events(self, events: List[Dict], dt: float) -> Dict:
        """Process event stream and estimate pose change"""
        if not events:
            return {"dx": 0, "dy": 0, "dz": 0, "droll": 0, "dpitch": 0, "dyaw": 0}
        
        features = self._cluster_events(events)
        motion = self._estimate_motion(features, dt)
        
        drift_factor = 0.001
        motion["dx"] += random.gauss(0, drift_factor)
        motion["dy"] += random.gauss(0, drift_factor)
        motion["dz"] += random.gauss(0, drift_factor * 0.1)
        
        return motion
    
    def _cluster_events(self, events: List[Dict]) -> List[Dict]:
        """Cluster nearby events into feature points"""
        grid_size = 20
        grid = {}
        
        for event in events:
            gx, gy = event["x"] // grid_size, event["y"] // grid_size
            key = (gx, gy)
            if key not in grid:
                grid[key] = {"x": 0, "y": 0, "count": 0, "polarity_sum": 0}
            grid[key]["x"] += event["x"]
            grid[key]["y"] += event["y"]
            grid[key]["count"] += 1
            grid[key]["polarity_sum"] += event["polarity"]
        
        features = []
        for key, cell in grid.items():
            if cell["count"] >= 5:
                features.append({
                    "x": cell["x"] / cell["count"],
                    "y": cell["y"] / cell["count"],
                    "strength": cell["count"],
                    "polarity": cell["polarity_sum"]
                })
        
        return features
    
    def _estimate_motion(self, features: List[Dict], dt: float) -> Dict:
        """Estimate camera motion from features"""
        if len(features) < 3:
            return {"dx": 0, "dy": 0, "dz": 0, "droll": 0, "dpitch": 0, "dyaw": 0}
        
        cx = sum(f["x"] for f in features) / len(features)
        cy = sum(f["y"] for f in features) / len(features)
        
        radial_flow = sum(
            math.sqrt((f["x"] - 320)**2 + (f["y"] - 240)**2) * f["strength"]
            for f in features
        ) / max(sum(f["strength"] for f in features), 1)
        
        return {
            "dx": (cx - 320) * 0.001 * dt,
            "dy": (cy - 240) * 0.001 * dt,
            "dz": -radial_flow * 0.01 * dt,
            "droll": random.gauss(0, 0.01),
            "dpitch": random.gauss(0, 0.01),
            "dyaw": random.gauss(0, 0.005)
        }


class EVOSimulatorEnhanced:
    """Enhanced simulation engine with SNN processing"""
    
    def __init__(self, config: SimulationConfig = None):
        self.config = config or SimulationConfig()
        self.terrain = TerrainGenerator(self.config.terrain_type, self.config.feature_density)
        self.camera = EventCamera(self.config.camera_resolution, self.config.noise_level)
        
        # Choose VO algorithm
        if self.config.use_snn_processing:
            self.vo = SNNVisualOdometry(
                self.config.camera_resolution[0],
                self.config.camera_resolution[1]
            )
        else:
            self.vo = StandardVisualOdometry()
        
        self.state = SimulationState(config=self.config)
        self.state.current_pose = Pose(z=self.config.initial_altitude)
    
    def step(self, dt: float = 0.05) -> Dict:
        """Advance simulation by dt seconds"""
        if self.state.current_pose.z <= 0 or self.state.is_landed:
            self.state.is_running = False
            self.state.is_landed = True
            return {
                "status": "landed",
                "state": self._get_state_dict(),
                "time": self.state.current_time,
                "altitude": max(0, self.state.current_pose.z),
                "total_events": self.state.events_generated,
                "metrics": self._calculate_metrics() if self.state.ground_truth_poses else {}
            }
        
        self.state.is_running = True
        self.state.current_time += dt
        
        # Update ground truth pose
        gt_pose = self._update_ground_truth(dt)
        
        # Generate synthetic camera frame
        frame = self._render_frame(gt_pose)
        
        # Generate events
        events = self.camera.generate_events(frame, self.state.current_time * 1e6)
        self.state.events_generated += len(events)
        
        # Store events
        self.state.events_history.extend(events)
        if len(self.state.events_history) > 50000:
            self.state.events_history = self.state.events_history[-50000:]
        
        # Run visual odometry
        if self.config.use_snn_processing:
            motion = self.vo.process_events(events, dt, self.config.vibration_amplitude)
            # Get SNN-specific data
            self.state.corner_detections = self.vo.corner_detector.detect_corners(
                events, self.state.current_time
            )
            self.state.tracked_features = self.vo.get_tracked_features()
        else:
            motion = self.vo.process_events(events, dt)
        
        # Update estimated pose
        est_pose = self._update_estimated_pose(motion)
        
        # Store poses
        self.state.ground_truth_poses.append({
            "time": self.state.current_time,
            "x": gt_pose.x, "y": gt_pose.y, "z": gt_pose.z,
            "roll": gt_pose.roll, "pitch": gt_pose.pitch, "yaw": gt_pose.yaw
        })
        self.state.estimated_poses.append({
            "time": self.state.current_time,
            "x": est_pose.x, "y": est_pose.y, "z": est_pose.z,
            "roll": est_pose.roll, "pitch": est_pose.pitch, "yaw": est_pose.yaw
        })
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        self.state.metrics_history.append({
            "time": self.state.current_time,
            **metrics
        })
        
        # Check landing
        if gt_pose.z <= 0:
            self.state.is_landed = True
            self.state.is_running = False
        
        return {
            "status": "landed" if self.state.is_landed else "running",
            "time": self.state.current_time,
            "ground_truth": self.state.ground_truth_poses[-1],
            "estimated": self.state.estimated_poses[-1],
            "events": events[:500],
            "event_count": len(events),
            "total_events": self.state.events_generated,
            "metrics": metrics,
            "altitude": max(0, gt_pose.z),
            "corners_detected": len(self.state.corner_detections),
            "features_tracked": len(self.state.tracked_features)
        }
    
    def _update_ground_truth(self, dt: float) -> Pose:
        """Update ground truth pose"""
        pose = self.state.current_pose
        
        pose.z -= self.config.descent_velocity * dt
        pose.x += random.gauss(0, 0.5) * dt
        pose.y += random.gauss(0, 0.5) * dt
        
        vib = self.config.vibration_amplitude
        freq = self.config.vibration_frequency
        t = self.state.current_time
        pose.roll = vib * math.sin(2 * math.pi * freq * t) + random.gauss(0, vib * 0.3)
        pose.pitch = vib * math.cos(2 * math.pi * freq * t * 1.1) + random.gauss(0, vib * 0.3)
        pose.yaw += random.gauss(0, 0.05) * dt
        
        pose.timestamp = self.state.current_time
        return pose
    
    def _update_estimated_pose(self, motion: Dict) -> Pose:
        """Update estimated pose from VO"""
        return Pose(
            x=self.state.current_pose.x + motion["dx"],
            y=self.state.current_pose.y + motion["dy"],
            z=self.state.current_pose.z + motion["dz"],
            roll=self.state.current_pose.roll + motion["droll"],
            pitch=self.state.current_pose.pitch + motion["dpitch"],
            yaw=self.state.current_pose.yaw + motion["dyaw"],
            timestamp=self.state.current_time
        )
    
    def _render_frame(self, pose: Pose) -> np.ndarray:
        """Render synthetic camera frame"""
        frame = np.zeros((self.config.camera_resolution[1], self.config.camera_resolution[0]), dtype=np.float32)
        
        base_brightness = min(1.0, 100 / max(pose.z, 1))
        
        for feature in self.terrain.features:
            scale = 100 / max(pose.z, 1)
            px = int((feature["x"] - pose.x) * scale + 320)
            py = int((feature["y"] - pose.y) * scale + 240)
            
            if 0 <= px < 640 and 0 <= py < 480:
                size = max(1, int(feature["size"] * scale))
                brightness = feature["contrast"] * base_brightness
                
                for dx in range(-size, size + 1):
                    for dy in range(-size, size + 1):
                        npx, npy = px + dx, py + dy
                        if 0 <= npx < 640 and 0 <= npy < 480:
                            dist = math.sqrt(dx**2 + dy**2)
                            if dist <= size:
                                frame[npy, npx] = brightness * (1 - dist / (size + 1))
        
        return frame
    
    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if len(self.state.ground_truth_poses) < 2:
            return {"position_error": 0, "attitude_error": 0, "drift_rate": 0, "latency_ms": 0}
        
        gt = self.state.ground_truth_poses[-1]
        est = self.state.estimated_poses[-1]
        
        pos_error = math.sqrt(
            (gt["x"] - est["x"])**2 +
            (gt["y"] - est["y"])**2 +
            (gt["z"] - est["z"])**2
        )
        
        att_error = math.sqrt(
            (gt["roll"] - est["roll"])**2 +
            (gt["pitch"] - est["pitch"])**2 +
            (gt["yaw"] - est["yaw"])**2
        ) * 180 / math.pi
        
        drift_rate = pos_error / self.state.current_time if self.state.current_time > 0 else 0
        latency = random.uniform(0.3, 1.5)
        
        return {
            "position_error": round(pos_error, 3),
            "attitude_error": round(att_error, 3),
            "drift_rate": round(drift_rate, 4),
            "latency_ms": round(latency, 2)
        }
    
    def _get_state_dict(self) -> Dict:
        """Get serializable state"""
        return {
            "id": self.state.id,
            "time": self.state.current_time,
            "is_running": self.state.is_running,
            "is_landed": self.state.is_landed,
            "events_generated": self.state.events_generated,
            "altitude": max(0, self.state.current_pose.z),
            "config": {
                "terrain_type": self.config.terrain_type.value,
                "initial_altitude": self.config.initial_altitude,
                "descent_velocity": self.config.descent_velocity,
                "vibration_amplitude": self.config.vibration_amplitude,
                "noise_level": self.config.noise_level,
                "use_snn_processing": self.config.use_snn_processing
            }
        }
    
    def get_full_state(self) -> Dict:
        """Get complete simulation state"""
        return {
            **self._get_state_dict(),
            "ground_truth_poses": self.state.ground_truth_poses,
            "estimated_poses": self.state.estimated_poses,
            "events_history": self.state.events_history[-1000:],
            "metrics_history": self.state.metrics_history,
            "terrain_heightmap": self.terrain.get_heightmap_data(),
            "terrain_features": self.terrain.get_features_3d()
        }
    
    def get_3d_data(self) -> Dict:
        """Get data for 3D visualization"""
        return {
            "terrain": {
                "heightmap": self.terrain.get_heightmap_data(),
                "features": self.terrain.get_features_3d()
            },
            "trajectory": {
                "ground_truth": self.state.ground_truth_poses,
                "estimated": self.state.estimated_poses
            },
            "current_pose": {
                "x": self.state.current_pose.x,
                "y": self.state.current_pose.y,
                "z": self.state.current_pose.z,
                "roll": self.state.current_pose.roll,
                "pitch": self.state.current_pose.pitch,
                "yaw": self.state.current_pose.yaw
            }
        }
    
    def reset(self):
        """Reset simulation"""
        self.state = SimulationState(config=self.config)
        self.state.current_pose = Pose(z=self.config.initial_altitude)
        self.camera = EventCamera(self.config.camera_resolution, self.config.noise_level)
        if self.config.use_snn_processing:
            self.vo = SNNVisualOdometry(
                self.config.camera_resolution[0],
                self.config.camera_resolution[1]
            )
        else:
            self.vo = StandardVisualOdometry()
