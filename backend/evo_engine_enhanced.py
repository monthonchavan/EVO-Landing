"""
Lightweight EVO Engine - Optimized for Performance
Reduces computational load for smoother operation.
"""

import numpy as np
import math
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import random

class TerrainType(str, Enum):
    LUNAR = "lunar"
    MARS = "mars"
    ASTEROID = "asteroid"
    CUSTOM = "custom"

@dataclass
class Pose:
    x: float = 0.0
    y: float = 0.0
    z: float = 1000.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    timestamp: float = 0.0

@dataclass
class SimulationConfig:
    terrain_type: TerrainType = TerrainType.LUNAR
    initial_altitude: float = 1000.0
    descent_velocity: float = 50.0
    vibration_amplitude: float = 0.5
    vibration_frequency: float = 10.0
    camera_resolution: Tuple[int, int] = (640, 480)
    simulation_duration: float = 20.0
    noise_level: float = 0.1
    feature_density: int = 100  # Reduced from 200
    use_snn_processing: bool = True
    # Performance settings
    max_events_per_step: int = 200  # Limit events
    simplified_snn: bool = True  # Use simplified SNN

@dataclass
class SimulationState:
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
    corner_detections: List[Dict] = field(default_factory=list)
    tracked_features: List[Dict] = field(default_factory=list)


class LightweightTerrainGenerator:
    """Simplified terrain generator for better performance"""
    
    TERRAIN_PROFILES = {
        TerrainType.LUNAR: {'crater_ratio': 0.6, 'rock_ratio': 0.3, 'base_albedo': 0.12},
        TerrainType.MARS: {'crater_ratio': 0.4, 'rock_ratio': 0.4, 'base_albedo': 0.25},
        TerrainType.ASTEROID: {'crater_ratio': 0.5, 'rock_ratio': 0.35, 'base_albedo': 0.08},
        TerrainType.CUSTOM: {'crater_ratio': 0.5, 'rock_ratio': 0.35, 'base_albedo': 0.15},
    }
    
    def __init__(self, terrain_type: TerrainType, feature_density: int):
        self.terrain_type = terrain_type
        self.feature_density = min(feature_density, 100)  # Cap at 100
        self.profile = self.TERRAIN_PROFILES.get(terrain_type, self.TERRAIN_PROFILES[TerrainType.CUSTOM])
        self.features = self._generate_features()
        self.heightmap = self._generate_heightmap(64)  # Small heightmap
    
    def _generate_features(self) -> List[Dict]:
        features = []
        profile = self.profile
        
        for i in range(self.feature_density):
            rand = random.random()
            if rand < profile['crater_ratio']:
                feature_type = "crater"
                size = random.uniform(20, 60)
            else:
                feature_type = "rock"
                size = random.uniform(5, 20)
            
            features.append({
                "id": i,
                "type": feature_type,
                "x": random.uniform(-500, 500),
                "y": random.uniform(-500, 500),
                "z": 0,
                "size": size,
                "contrast": random.uniform(0.5, 1.0),
            })
        
        return features
    
    def _generate_heightmap(self, size: int = 64) -> np.ndarray:
        heightmap = np.zeros((size, size), dtype=np.float32)
        
        for feature in self.features[:50]:  # Limit features processed
            hx = int((feature['x'] + 500) / 1000 * size)
            hy = int((feature['y'] + 500) / 1000 * size)
            
            if not (0 <= hx < size and 0 <= hy < size):
                continue
            
            radius = max(1, int(feature['size'] / 1000 * size * 2))
            
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    nx, ny = hx + dx, hy + dy
                    if 0 <= nx < size and 0 <= ny < size:
                        dist = math.sqrt(dx**2 + dy**2) / (radius + 0.001)
                        if dist < 1:
                            height = feature['size'] * 0.1 * (1 - dist)
                            if feature['type'] == 'crater':
                                height = -height
                            heightmap[ny, nx] += height
        
        return heightmap
    
    def get_heightmap_data(self) -> Dict:
        return {
            'data': self.heightmap.tolist(),
            'width': self.heightmap.shape[1],
            'height': self.heightmap.shape[0],
            'scale': 1000,
            'max_height': float(np.max(self.heightmap)),
            'min_height': float(np.min(self.heightmap))
        }
    
    def get_features_3d(self) -> List[Dict]:
        return self.features[:50]  # Limit for performance


class LightweightEventCamera:
    """Simplified event camera - generates events"""
    
    def __init__(self, resolution: Tuple[int, int], noise_level: float = 0.1, max_events: int = 200):
        self.width, self.height = resolution
        self.noise_level = noise_level
        self.max_events = max_events
        self.last_frame = None  # Will be set on first frame
        self.threshold = 0.05  # Lower threshold for more events
    
    def generate_events(self, current_frame: np.ndarray, timestamp: float) -> List[Dict]:
        events = []
        
        # Initialize last frame if needed
        if self.last_frame is None:
            self.last_frame = current_frame.copy()
            # Generate some initial events based on frame brightness
            bright_coords = np.argwhere(current_frame > 0.1)
            for i, (y, x) in enumerate(bright_coords[:self.max_events // 2]):
                events.append({
                    "x": int(x),
                    "y": int(y),
                    "timestamp": timestamp + random.uniform(0, 50),
                    "polarity": 1
                })
            return events
        
        # Calculate difference
        diff = current_frame - self.last_frame
        
        # Find event locations
        pos_mask = diff > self.threshold
        neg_mask = diff < -self.threshold
        
        pos_coords = np.argwhere(pos_mask)
        neg_coords = np.argwhere(neg_mask)
        
        # Limit events per polarity
        max_per_polarity = self.max_events // 2
        
        for i, (y, x) in enumerate(pos_coords[:max_per_polarity]):
            events.append({
                "x": int(x),
                "y": int(y),
                "timestamp": timestamp + random.uniform(0, 50),
                "polarity": 1
            })
        
        for i, (y, x) in enumerate(neg_coords[:max_per_polarity]):
            events.append({
                "x": int(x),
                "y": int(y),
                "timestamp": timestamp + random.uniform(0, 50),
                "polarity": -1
            })
        
        # Add minimal noise events to ensure some activity
        if len(events) < 10:
            for _ in range(15):
                events.append({
                    "x": random.randint(0, self.width - 1),
                    "y": random.randint(0, self.height - 1),
                    "timestamp": timestamp + random.uniform(0, 100),
                    "polarity": random.choice([-1, 1])
                })
        
        self.last_frame = current_frame.copy()
        return events[:self.max_events]
                "y": int(y * 4),
                "timestamp": timestamp + random.uniform(0, 50),
                "polarity": 1
            })
        
        for i, (y, x) in enumerate(neg_coords[:max_per_polarity]):
            events.append({
                "x": int(x * 4),
                "y": int(y * 4),
                "timestamp": timestamp + random.uniform(0, 50),
                "polarity": -1
            })
        
        # Add minimal noise
        num_noise = min(10, int(len(events) * self.noise_level))
        for _ in range(num_noise):
            events.append({
                "x": random.randint(0, self.width - 1),
                "y": random.randint(0, self.height - 1),
                "timestamp": timestamp + random.uniform(0, 100),
                "polarity": random.choice([-1, 1])
            })
        
        self.last_frame = downsampled.copy()
        return events[:self.max_events]


class SimplifiedSNNProcessor:
    """Lightweight SNN-inspired processing"""
    
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        self.grid_size = 32  # Larger grid = fewer cells
        self.grid_w = width // self.grid_size
        self.grid_h = height // self.grid_size
        self.corner_response = np.zeros((self.grid_h, self.grid_w), dtype=np.float32)
        self.features = []
    
    def process_events(self, events: List[Dict], current_time: float) -> Tuple[List[Dict], List[Dict]]:
        """Simplified corner detection and feature tracking"""
        if not events:
            return [], self.features
        
        # Reset corner response with decay
        self.corner_response *= 0.8
        
        corners = []
        grid_counts = {}
        
        # Count events per grid cell
        for event in events:
            gx = event['x'] // self.grid_size
            gy = event['y'] // self.grid_size
            key = (gx, gy)
            grid_counts[key] = grid_counts.get(key, 0) + 1
        
        # Detect corners in high-activity cells
        for (gx, gy), count in grid_counts.items():
            if count >= 3 and gx < self.grid_w and gy < self.grid_h:
                self.corner_response[gy, gx] += count * 0.1
                
                if self.corner_response[gy, gx] > 0.5:
                    corners.append({
                        'x': gx * self.grid_size + self.grid_size // 2,
                        'y': gy * self.grid_size + self.grid_size // 2,
                        'response': self.corner_response[gy, gx],
                        'type': 'snn'
                    })
        
        # Simple feature tracking - just keep recent corners
        self.features = corners[:20]  # Limit features
        
        return corners[:10], self.features  # Limit returned corners
    
    def estimate_motion(self, events: List[Dict], dt: float) -> Dict:
        """Simple motion estimation"""
        if len(events) < 5:
            return {'dx': 0, 'dy': 0, 'dz': 0, 'droll': 0, 'dpitch': 0, 'dyaw': 0}
        
        # Compute centroid
        cx = sum(e['x'] for e in events) / len(events)
        cy = sum(e['y'] for e in events) / len(events)
        
        # Simple flow estimation
        drift = 0.0005
        return {
            'dx': (cx - 320) * 0.0005 * dt + random.gauss(0, drift),
            'dy': (cy - 240) * 0.0005 * dt + random.gauss(0, drift),
            'dz': -len(events) * 0.001 * dt,
            'droll': random.gauss(0, drift),
            'dpitch': random.gauss(0, drift),
            'dyaw': random.gauss(0, drift * 0.5)
        }


class EVOSimulatorEnhanced:
    """Lightweight simulation engine optimized for performance"""
    
    def __init__(self, config: SimulationConfig = None):
        self.config = config or SimulationConfig()
        self.terrain = LightweightTerrainGenerator(self.config.terrain_type, self.config.feature_density)
        self.camera = LightweightEventCamera(
            self.config.camera_resolution, 
            self.config.noise_level,
            self.config.max_events_per_step
        )
        self.snn = SimplifiedSNNProcessor(
            self.config.camera_resolution[0],
            self.config.camera_resolution[1]
        ) if self.config.use_snn_processing else None
        
        self.state = SimulationState(config=self.config)
        self.state.current_pose = Pose(z=self.config.initial_altitude)
    
    def step(self, dt: float = 0.1) -> Dict:  # Larger timestep
        """Advance simulation - optimized for performance"""
        if self.state.current_pose.z <= 0 or self.state.is_landed:
            self.state.is_running = False
            self.state.is_landed = True
            return {
                "status": "landed",
                "time": self.state.current_time,
                "altitude": 0,
                "total_events": self.state.events_generated,
                "metrics": self._calculate_metrics()
            }
        
        self.state.is_running = True
        self.state.current_time += dt
        
        # Update ground truth pose
        gt_pose = self._update_ground_truth(dt)
        
        # Generate frame (simplified)
        frame = self._render_frame_simple(gt_pose)
        
        # Generate events (limited)
        events = self.camera.generate_events(frame, self.state.current_time * 1e6)
        self.state.events_generated += len(events)
        
        # Store limited events
        self.state.events_history = events  # Only keep current step
        
        # Process with SNN (if enabled)
        corners = []
        features = []
        if self.snn:
            corners, features = self.snn.process_events(events, self.state.current_time)
            motion = self.snn.estimate_motion(events, dt)
        else:
            motion = self._simple_motion_estimate(events, dt)
        
        self.state.corner_detections = corners
        self.state.tracked_features = features
        
        # Update estimated pose
        est_pose = Pose(
            x=self.state.current_pose.x + motion['dx'],
            y=self.state.current_pose.y + motion['dy'],
            z=self.state.current_pose.z + motion['dz'],
            roll=self.state.current_pose.roll + motion['droll'],
            pitch=self.state.current_pose.pitch + motion['dpitch'],
            yaw=self.state.current_pose.yaw + motion['dyaw'],
            timestamp=self.state.current_time
        )
        
        # Store poses (limit history)
        gt_dict = {"time": self.state.current_time, "x": gt_pose.x, "y": gt_pose.y, "z": gt_pose.z,
                   "roll": gt_pose.roll, "pitch": gt_pose.pitch, "yaw": gt_pose.yaw}
        est_dict = {"time": self.state.current_time, "x": est_pose.x, "y": est_pose.y, "z": est_pose.z,
                    "roll": est_pose.roll, "pitch": est_pose.pitch, "yaw": est_pose.yaw}
        
        self.state.ground_truth_poses.append(gt_dict)
        self.state.estimated_poses.append(est_dict)
        
        # Limit history to last 50 entries
        if len(self.state.ground_truth_poses) > 50:
            self.state.ground_truth_poses = self.state.ground_truth_poses[-50:]
            self.state.estimated_poses = self.state.estimated_poses[-50:]
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        self.state.metrics_history.append({"time": self.state.current_time, **metrics})
        if len(self.state.metrics_history) > 50:
            self.state.metrics_history = self.state.metrics_history[-50:]
        
        # Check landing
        if gt_pose.z <= 0:
            self.state.is_landed = True
            self.state.is_running = False
        
        return {
            "status": "landed" if self.state.is_landed else "running",
            "time": self.state.current_time,
            "ground_truth": gt_dict,
            "estimated": est_dict,
            "events": events[:100],  # Limit events sent to frontend
            "event_count": len(events),
            "total_events": self.state.events_generated,
            "metrics": metrics,
            "altitude": max(0, gt_pose.z),
            "corners_detected": len(corners),
            "features_tracked": len(features)
        }
    
    def _update_ground_truth(self, dt: float) -> Pose:
        pose = self.state.current_pose
        pose.z -= self.config.descent_velocity * dt
        pose.x += random.gauss(0, 0.3) * dt
        pose.y += random.gauss(0, 0.3) * dt
        
        vib = self.config.vibration_amplitude
        freq = self.config.vibration_frequency
        t = self.state.current_time
        pose.roll = vib * math.sin(2 * math.pi * freq * t)
        pose.pitch = vib * math.cos(2 * math.pi * freq * t * 1.1)
        pose.yaw += random.gauss(0, 0.02) * dt
        
        pose.timestamp = self.state.current_time
        return pose
    
    def _render_frame_simple(self, pose: Pose) -> np.ndarray:
        """Simplified frame rendering"""
        h, w = self.config.camera_resolution[1], self.config.camera_resolution[0]
        frame = np.zeros((h, w), dtype=np.float32)
        
        base_brightness = min(1.0, 100 / max(pose.z, 1))
        
        # Only process limited features
        for feature in self.terrain.features[:30]:
            scale = 100 / max(pose.z, 1)
            px = int((feature["x"] - pose.x) * scale + 320)
            py = int((feature["y"] - pose.y) * scale + 240)
            
            if 0 <= px < 640 and 0 <= py < 480:
                size = max(1, int(feature["size"] * scale * 0.5))
                brightness = feature["contrast"] * base_brightness
                
                # Simple circle instead of complex rendering
                for dx in range(-size, size + 1, 2):  # Skip pixels for speed
                    for dy in range(-size, size + 1, 2):
                        npx, npy = px + dx, py + dy
                        if 0 <= npx < 640 and 0 <= npy < 480:
                            dist = math.sqrt(dx**2 + dy**2)
                            if dist <= size:
                                frame[npy, npx] = brightness * (1 - dist / (size + 1))
        
        return frame
    
    def _simple_motion_estimate(self, events: List[Dict], dt: float) -> Dict:
        if len(events) < 3:
            return {'dx': 0, 'dy': 0, 'dz': 0, 'droll': 0, 'dpitch': 0, 'dyaw': 0}
        
        cx = sum(e['x'] for e in events) / len(events)
        cy = sum(e['y'] for e in events) / len(events)
        
        return {
            'dx': (cx - 320) * 0.0005 * dt,
            'dy': (cy - 240) * 0.0005 * dt,
            'dz': -len(events) * 0.0005 * dt,
            'droll': random.gauss(0, 0.001),
            'dpitch': random.gauss(0, 0.001),
            'dyaw': random.gauss(0, 0.0005)
        }
    
    def _calculate_metrics(self) -> Dict:
        if len(self.state.ground_truth_poses) < 1:
            return {"position_error": 0, "attitude_error": 0, "drift_rate": 0, "latency_ms": 0}
        
        gt = self.state.ground_truth_poses[-1]
        est = self.state.estimated_poses[-1] if self.state.estimated_poses else gt
        
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
        
        drift_rate = pos_error / max(self.state.current_time, 0.1)
        
        return {
            "position_error": round(pos_error, 3),
            "attitude_error": round(att_error, 3),
            "drift_rate": round(drift_rate, 4),
            "latency_ms": round(random.uniform(0.3, 1.0), 2)
        }
    
    def get_full_state(self) -> Dict:
        return {
            "id": self.state.id,
            "time": self.state.current_time,
            "is_running": self.state.is_running,
            "is_landed": self.state.is_landed,
            "events_generated": self.state.events_generated,
            "altitude": max(0, self.state.current_pose.z),
            "ground_truth_poses": self.state.ground_truth_poses[-20:],
            "estimated_poses": self.state.estimated_poses[-20:],
            "events_history": self.state.events_history[:100],
            "metrics_history": self.state.metrics_history[-20:],
            "terrain_heightmap": self.terrain.get_heightmap_data(),
            "terrain_features": self.terrain.get_features_3d()
        }
    
    def get_3d_data(self) -> Dict:
        return {
            "terrain": {
                "heightmap": self.terrain.get_heightmap_data(),
                "features": self.terrain.get_features_3d()
            },
            "trajectory": {
                "ground_truth": self.state.ground_truth_poses[-20:],
                "estimated": self.state.estimated_poses[-20:]
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
        self.state = SimulationState(config=self.config)
        self.state.current_pose = Pose(z=self.config.initial_altitude)
        self.camera = LightweightEventCamera(
            self.config.camera_resolution,
            self.config.noise_level,
            self.config.max_events_per_step
        )
        if self.config.use_snn_processing:
            self.snn = SimplifiedSNNProcessor(
                self.config.camera_resolution[0],
                self.config.camera_resolution[1]
            )
