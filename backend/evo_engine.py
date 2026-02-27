"""
Event-Based Visual Odometry (EVO) Engine
Simulates neuromorphic event camera data and pose estimation for planetary landing.
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
    CUSTOM = "custom"

@dataclass
class Event:
    """Single neuromorphic event from event camera"""
    x: int  # pixel x coordinate
    y: int  # pixel y coordinate  
    timestamp: float  # microseconds
    polarity: int  # +1 or -1 (brightness increase/decrease)

@dataclass
class Pose:
    """6-DOF pose of the lander"""
    x: float = 0.0
    y: float = 0.0
    z: float = 1000.0  # altitude in meters
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    timestamp: float = 0.0

@dataclass
class SimulationConfig:
    """Configuration for descent simulation"""
    terrain_type: TerrainType = TerrainType.LUNAR
    initial_altitude: float = 1000.0  # meters
    descent_velocity: float = 50.0  # m/s
    vibration_amplitude: float = 0.5  # degrees
    vibration_frequency: float = 10.0  # Hz
    camera_resolution: Tuple[int, int] = (640, 480)
    simulation_duration: float = 20.0  # seconds
    noise_level: float = 0.1  # 0-1 noise injection
    feature_density: int = 200  # terrain features

@dataclass
class SimulationState:
    """Current state of a running simulation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: SimulationConfig = field(default_factory=SimulationConfig)
    current_time: float = 0.0
    current_pose: Pose = field(default_factory=Pose)
    ground_truth_poses: List[Dict] = field(default_factory=list)
    estimated_poses: List[Dict] = field(default_factory=list)
    events_history: List[Dict] = field(default_factory=list)  # Store all events
    metrics_history: List[Dict] = field(default_factory=list)  # Store metrics
    events_generated: int = 0
    is_running: bool = False
    is_landed: bool = False  # Track landed state without resetting
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class TerrainGenerator:
    """Generates synthetic terrain features for event simulation"""
    
    def __init__(self, terrain_type: TerrainType, feature_density: int):
        self.terrain_type = terrain_type
        self.feature_density = feature_density
        self.features = self._generate_features()
    
    def _generate_features(self) -> List[Dict]:
        """Generate random terrain features (craters, rocks, ridges)"""
        features = []
        
        if self.terrain_type == TerrainType.LUNAR:
            # Lunar: more craters, fewer rocks
            crater_ratio = 0.6
        elif self.terrain_type == TerrainType.MARS:
            # Mars: mix of rocks and small craters
            crater_ratio = 0.4
        else:
            crater_ratio = 0.5
        
        for i in range(self.feature_density):
            feature_type = "crater" if random.random() < crater_ratio else "rock"
            features.append({
                "type": feature_type,
                "x": random.uniform(-500, 500),
                "y": random.uniform(-500, 500),
                "size": random.uniform(5, 50) if feature_type == "crater" else random.uniform(1, 10),
                "contrast": random.uniform(0.5, 1.0)
            })
        
        return features
    
    def get_feature_at(self, x: float, y: float) -> Optional[Dict]:
        """Get terrain feature at position if any"""
        for feature in self.features:
            dist = math.sqrt((feature["x"] - x)**2 + (feature["y"] - y)**2)
            if dist < feature["size"]:
                return feature
        return None

class EventCamera:
    """Simulates neuromorphic event camera behavior"""
    
    def __init__(self, resolution: Tuple[int, int], noise_level: float = 0.1):
        self.width, self.height = resolution
        self.noise_level = noise_level
        self.last_frame = np.zeros((self.height, self.width), dtype=np.float32)
        self.threshold = 0.15  # Brightness change threshold to trigger event
    
    def generate_events(self, current_frame: np.ndarray, timestamp: float) -> List[Dict]:
        """Generate events from frame difference"""
        events = []
        
        # Calculate difference from last frame
        diff = current_frame - self.last_frame
        
        # Find pixels that exceed threshold
        pos_events = np.where(diff > self.threshold)
        neg_events = np.where(diff < -self.threshold)
        
        # Generate positive polarity events
        for i in range(len(pos_events[0])):
            y, x = pos_events[0][i], pos_events[1][i]
            events.append({
                "x": int(x),
                "y": int(y),
                "timestamp": timestamp + random.uniform(0, 100),  # Microsecond jitter
                "polarity": 1
            })
        
        # Generate negative polarity events
        for i in range(len(neg_events[0])):
            y, x = neg_events[0][i], neg_events[1][i]
            events.append({
                "x": int(x),
                "y": int(y),
                "timestamp": timestamp + random.uniform(0, 100),
                "polarity": -1
            })
        
        # Add noise events
        num_noise = int(len(events) * self.noise_level)
        for _ in range(num_noise):
            events.append({
                "x": random.randint(0, self.width - 1),
                "y": random.randint(0, self.height - 1),
                "timestamp": timestamp + random.uniform(0, 100),
                "polarity": random.choice([-1, 1])
            })
        
        # Sort by timestamp
        events.sort(key=lambda e: e["timestamp"])
        
        self.last_frame = current_frame.copy()
        return events

class VisualOdometry:
    """Event-Based Visual Odometry algorithm"""
    
    def __init__(self):
        self.feature_tracks = []
        self.last_pose = Pose()
        self.accumulated_drift = {"x": 0.0, "y": 0.0, "z": 0.0}
    
    def process_events(self, events: List[Dict], dt: float) -> Dict:
        """Process event stream and estimate pose change"""
        if not events:
            return {"dx": 0, "dy": 0, "dz": 0, "droll": 0, "dpitch": 0, "dyaw": 0}
        
        # Cluster events into feature points
        features = self._cluster_events(events)
        
        # Track features over time
        motion = self._estimate_motion(features, dt)
        
        # Add small drift for realism
        drift_factor = 0.001
        motion["dx"] += random.gauss(0, drift_factor)
        motion["dy"] += random.gauss(0, drift_factor)
        motion["dz"] += random.gauss(0, drift_factor * 0.1)
        
        return motion
    
    def _cluster_events(self, events: List[Dict]) -> List[Dict]:
        """Cluster nearby events into feature points using simple grid-based approach"""
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
            if cell["count"] >= 5:  # Minimum events for feature
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
        
        # Simplified motion estimation based on feature flow
        cx = sum(f["x"] for f in features) / len(features)
        cy = sum(f["y"] for f in features) / len(features)
        
        # Expansion/contraction indicates vertical motion
        radial_flow = sum(
            math.sqrt((f["x"] - 320)**2 + (f["y"] - 240)**2) * f["strength"]
            for f in features
        ) / max(sum(f["strength"] for f in features), 1)
        
        return {
            "dx": (cx - 320) * 0.001 * dt,
            "dy": (cy - 240) * 0.001 * dt,
            "dz": -radial_flow * 0.01 * dt,  # Descent rate
            "droll": random.gauss(0, 0.01),
            "dpitch": random.gauss(0, 0.01),
            "dyaw": random.gauss(0, 0.005)
        }

class EVOSimulator:
    """Main simulation engine combining all components"""
    
    def __init__(self, config: SimulationConfig = None):
        self.config = config or SimulationConfig()
        self.terrain = TerrainGenerator(self.config.terrain_type, self.config.feature_density)
        self.camera = EventCamera(self.config.camera_resolution, self.config.noise_level)
        self.vo = VisualOdometry()
        self.state = SimulationState(config=self.config)
        self.state.current_pose = Pose(z=self.config.initial_altitude)
    
    def step(self, dt: float = 0.05) -> Dict:
        """Advance simulation by dt seconds"""
        if self.state.current_pose.z <= 0:
            self.state.is_running = False
            return {"status": "landed", "state": self._get_state_dict()}
        
        self.state.is_running = True
        self.state.current_time += dt
        
        # Update ground truth pose (simulated descent)
        gt_pose = self._update_ground_truth(dt)
        
        # Generate synthetic camera frame
        frame = self._render_frame(gt_pose)
        
        # Generate events from frame
        events = self.camera.generate_events(frame, self.state.current_time * 1e6)
        self.state.events_generated += len(events)
        
        # Run visual odometry
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
        
        return {
            "status": "running",
            "time": self.state.current_time,
            "ground_truth": self.state.ground_truth_poses[-1],
            "estimated": self.state.estimated_poses[-1],
            "events": events[:500],  # Limit events returned
            "event_count": len(events),
            "total_events": self.state.events_generated,
            "metrics": metrics,
            "altitude": gt_pose.z
        }
    
    def _update_ground_truth(self, dt: float) -> Pose:
        """Update ground truth pose based on descent dynamics"""
        pose = self.state.current_pose
        
        # Descent
        pose.z -= self.config.descent_velocity * dt
        
        # Lateral drift (wind, thrust asymmetry)
        pose.x += random.gauss(0, 0.5) * dt
        pose.y += random.gauss(0, 0.5) * dt
        
        # Vibration (rocket engine noise)
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
        # Simple integration of motion estimates
        est = Pose(
            x=self.state.current_pose.x + motion["dx"],
            y=self.state.current_pose.y + motion["dy"],
            z=self.state.current_pose.z + motion["dz"],
            roll=self.state.current_pose.roll + motion["droll"],
            pitch=self.state.current_pose.pitch + motion["dpitch"],
            yaw=self.state.current_pose.yaw + motion["dyaw"],
            timestamp=self.state.current_time
        )
        return est
    
    def _render_frame(self, pose: Pose) -> np.ndarray:
        """Render synthetic camera frame from current pose"""
        frame = np.zeros((self.config.camera_resolution[1], self.config.camera_resolution[0]), dtype=np.float32)
        
        # Base brightness based on altitude (higher = dimmer features)
        base_brightness = min(1.0, 100 / max(pose.z, 1))
        
        # Project terrain features onto camera
        for feature in self.terrain.features:
            # Simple perspective projection
            scale = 100 / max(pose.z, 1)
            px = int((feature["x"] - pose.x) * scale + 320)
            py = int((feature["y"] - pose.y) * scale + 240)
            
            if 0 <= px < 640 and 0 <= py < 480:
                # Draw feature with some size based on distance
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
        
        # Position error (3D distance)
        pos_error = math.sqrt(
            (gt["x"] - est["x"])**2 +
            (gt["y"] - est["y"])**2 +
            (gt["z"] - est["z"])**2
        )
        
        # Attitude error (degrees)
        att_error = math.sqrt(
            (gt["roll"] - est["roll"])**2 +
            (gt["pitch"] - est["pitch"])**2 +
            (gt["yaw"] - est["yaw"])**2
        ) * 180 / math.pi
        
        # Drift rate (error per second)
        if self.state.current_time > 0:
            drift_rate = pos_error / self.state.current_time
        else:
            drift_rate = 0
        
        # Simulated processing latency
        latency = random.uniform(0.5, 2.0)  # ms
        
        return {
            "position_error": round(pos_error, 3),
            "attitude_error": round(att_error, 3),
            "drift_rate": round(drift_rate, 4),
            "latency_ms": round(latency, 2)
        }
    
    def _get_state_dict(self) -> Dict:
        """Get serializable state dictionary"""
        return {
            "id": self.state.id,
            "time": self.state.current_time,
            "is_running": self.state.is_running,
            "events_generated": self.state.events_generated,
            "altitude": self.state.current_pose.z,
            "config": {
                "terrain_type": self.config.terrain_type.value,
                "initial_altitude": self.config.initial_altitude,
                "descent_velocity": self.config.descent_velocity,
                "vibration_amplitude": self.config.vibration_amplitude,
                "noise_level": self.config.noise_level
            }
        }
    
    def get_full_state(self) -> Dict:
        """Get complete simulation state for persistence"""
        return {
            **self._get_state_dict(),
            "ground_truth_poses": self.state.ground_truth_poses[-100:],  # Last 100
            "estimated_poses": self.state.estimated_poses[-100:]
        }
    
    def reset(self):
        """Reset simulation to initial state"""
        self.state = SimulationState(config=self.config)
        self.state.current_pose = Pose(z=self.config.initial_altitude)
        self.camera = EventCamera(self.config.camera_resolution, self.config.noise_level)
        self.vo = VisualOdometry()
