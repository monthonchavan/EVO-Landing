"""
Frame-Based Visual Odometry (FVO) Module for Comparison
Implements traditional frame-based VO to compare against Event-Based VO
"""

import numpy as np
import math
import random
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class FrameVOConfig:
    """Configuration for frame-based VO"""
    frame_rate: int = 30  # FPS
    resolution: Tuple[int, int] = (640, 480)
    feature_count: int = 100  # ORB features to detect
    motion_blur_factor: float = 0.1  # Blur at high speeds

class FrameBasedVO:
    """
    Traditional Frame-Based Visual Odometry
    Uses simulated frame capture and feature matching
    """
    
    def __init__(self, config: FrameVOConfig = None):
        self.config = config or FrameVOConfig()
        self.last_frame_time = 0.0
        self.last_features = []
        self.accumulated_pose = {
            "x": 0.0, "y": 0.0, "z": 0.0,
            "roll": 0.0, "pitch": 0.0, "yaw": 0.0
        }
        self.frame_interval = 1.0 / self.config.frame_rate
        self.pose_history = []
        self.metrics_history = []
    
    def process_frame(self, current_time: float, ground_truth: Dict, 
                      velocity: float = 50.0, vibration: float = 0.5) -> Dict:
        """
        Process a frame and estimate pose
        Simulates frame-based VO with realistic limitations
        """
        # Check if enough time has passed for next frame
        if current_time - self.last_frame_time < self.frame_interval:
            return None  # No new frame yet
        
        self.last_frame_time = current_time
        
        # Simulate frame capture
        frame_data = self._capture_frame(ground_truth, velocity, vibration)
        
        # Extract features (simulated ORB/SIFT)
        features = self._extract_features(frame_data)
        
        # Match features with previous frame
        if self.last_features:
            motion = self._estimate_motion(self.last_features, features, velocity)
        else:
            motion = {"dx": 0, "dy": 0, "dz": 0, "droll": 0, "dpitch": 0, "dyaw": 0}
        
        self.last_features = features
        
        # Update accumulated pose
        self._update_pose(motion)
        
        # Calculate error vs ground truth
        error = self._calculate_error(ground_truth)
        
        # Store history
        pose_record = {
            "time": current_time,
            **self.accumulated_pose
        }
        self.pose_history.append(pose_record)
        
        metrics_record = {
            "time": current_time,
            **error,
            "features_detected": len(features),
            "frame_quality": frame_data["quality"]
        }
        self.metrics_history.append(metrics_record)
        
        return {
            "pose": pose_record,
            "metrics": metrics_record,
            "features": len(features)
        }
    
    def _capture_frame(self, ground_truth: Dict, velocity: float, vibration: float) -> Dict:
        """Simulate frame capture with realistic effects"""
        # Motion blur increases with velocity
        blur_factor = min(1.0, velocity * self.config.motion_blur_factor / 100)
        
        # Vibration causes additional blur
        vibration_blur = vibration * 0.1
        
        # Total blur affects quality
        total_blur = blur_factor + vibration_blur
        quality = max(0.1, 1.0 - total_blur)
        
        # Altitude affects feature visibility
        altitude = ground_truth.get("z", 100)
        if altitude > 500:
            quality *= 0.8  # Features harder to see from high altitude
        elif altitude < 50:
            quality *= 1.1  # Good detail close to ground
        
        return {
            "quality": min(1.0, quality),
            "blur": total_blur,
            "altitude": altitude
        }
    
    def _extract_features(self, frame_data: Dict) -> List[Dict]:
        """Simulate feature extraction (ORB-like)"""
        quality = frame_data["quality"]
        base_features = self.config.feature_count
        
        # Quality affects number of features detected
        num_features = int(base_features * quality * random.uniform(0.8, 1.2))
        
        features = []
        for i in range(max(5, num_features)):
            features.append({
                "x": random.randint(0, self.config.resolution[0]),
                "y": random.randint(0, self.config.resolution[1]),
                "strength": random.uniform(0.3, 1.0) * quality,
                "id": i
            })
        
        return features
    
    def _estimate_motion(self, prev_features: List[Dict], curr_features: List[Dict],
                         velocity: float) -> Dict:
        """Estimate camera motion from feature matching"""
        # Simulate feature matching (not all features match)
        match_ratio = random.uniform(0.5, 0.9)
        num_matches = int(min(len(prev_features), len(curr_features)) * match_ratio)
        
        if num_matches < 5:
            # Too few matches - use velocity estimate
            return {
                "dx": random.gauss(0, 0.5),
                "dy": random.gauss(0, 0.5),
                "dz": -velocity * self.frame_interval + random.gauss(0, 1),
                "droll": random.gauss(0, 0.1),
                "dpitch": random.gauss(0, 0.1),
                "dyaw": random.gauss(0, 0.05)
            }
        
        # Calculate average feature displacement
        avg_dx = sum(f["x"] for f in curr_features[:num_matches]) / num_matches - \
                 sum(f["x"] for f in prev_features[:num_matches]) / num_matches
        avg_dy = sum(f["y"] for f in curr_features[:num_matches]) / num_matches - \
                 sum(f["y"] for f in prev_features[:num_matches]) / num_matches
        
        # Scale pixel motion to world motion (simplified)
        scale = 0.01
        
        return {
            "dx": avg_dx * scale + random.gauss(0, 0.1),
            "dy": avg_dy * scale + random.gauss(0, 0.1),
            "dz": -velocity * self.frame_interval + random.gauss(0, 0.5),
            "droll": random.gauss(0, 0.02),
            "dpitch": random.gauss(0, 0.02),
            "dyaw": random.gauss(0, 0.01)
        }
    
    def _update_pose(self, motion: Dict):
        """Update accumulated pose estimate"""
        self.accumulated_pose["x"] += motion["dx"]
        self.accumulated_pose["y"] += motion["dy"]
        self.accumulated_pose["z"] += motion["dz"]
        self.accumulated_pose["roll"] += motion["droll"]
        self.accumulated_pose["pitch"] += motion["dpitch"]
        self.accumulated_pose["yaw"] += motion["dyaw"]
    
    def _calculate_error(self, ground_truth: Dict) -> Dict:
        """Calculate error vs ground truth"""
        pos_error = math.sqrt(
            (ground_truth.get("x", 0) - self.accumulated_pose["x"])**2 +
            (ground_truth.get("y", 0) - self.accumulated_pose["y"])**2 +
            (ground_truth.get("z", 0) - self.accumulated_pose["z"])**2
        )
        
        att_error = math.sqrt(
            (ground_truth.get("roll", 0) - self.accumulated_pose["roll"])**2 +
            (ground_truth.get("pitch", 0) - self.accumulated_pose["pitch"])**2 +
            (ground_truth.get("yaw", 0) - self.accumulated_pose["yaw"])**2
        ) * 180 / math.pi
        
        return {
            "position_error": round(pos_error, 3),
            "attitude_error": round(att_error, 3)
        }
    
    def get_comparison_data(self) -> Dict:
        """Get data for comparison with EVO"""
        return {
            "method": "Frame-Based VO",
            "frame_rate": self.config.frame_rate,
            "pose_history": self.pose_history,
            "metrics_history": self.metrics_history,
            "total_frames": len(self.pose_history),
            "final_pose": self.accumulated_pose
        }
    
    def reset(self):
        """Reset VO state"""
        self.last_frame_time = 0.0
        self.last_features = []
        self.accumulated_pose = {
            "x": 0.0, "y": 0.0, "z": 0.0,
            "roll": 0.0, "pitch": 0.0, "yaw": 0.0
        }
        self.pose_history = []
        self.metrics_history = []


def compare_vo_methods(evo_data: Dict, fvo_data: Dict) -> Dict:
    """
    Compare Event-Based VO with Frame-Based VO
    Returns comprehensive comparison metrics
    """
    evo_metrics = evo_data.get("metrics_history", [])
    fvo_metrics = fvo_data.get("metrics_history", [])
    
    if not evo_metrics or not fvo_metrics:
        return {"error": "Insufficient data for comparison"}
    
    # Calculate average errors
    evo_avg_pos_error = sum(m.get("position_error", 0) for m in evo_metrics) / len(evo_metrics)
    evo_avg_att_error = sum(m.get("attitude_error", 0) for m in evo_metrics) / len(evo_metrics)
    
    fvo_avg_pos_error = sum(m.get("position_error", 0) for m in fvo_metrics) / len(fvo_metrics)
    fvo_avg_att_error = sum(m.get("attitude_error", 0) for m in fvo_metrics) / len(fvo_metrics)
    
    # Calculate final errors
    evo_final_pos = evo_metrics[-1].get("position_error", 0) if evo_metrics else 0
    fvo_final_pos = fvo_metrics[-1].get("position_error", 0) if fvo_metrics else 0
    
    # Determine winner
    pos_winner = "EVO" if evo_avg_pos_error < fvo_avg_pos_error else "FVO"
    att_winner = "EVO" if evo_avg_att_error < fvo_avg_att_error else "FVO"
    
    # Calculate improvement percentage
    if fvo_avg_pos_error > 0:
        pos_improvement = ((fvo_avg_pos_error - evo_avg_pos_error) / fvo_avg_pos_error) * 100
    else:
        pos_improvement = 0
    
    return {
        "event_based_vo": {
            "average_position_error": round(evo_avg_pos_error, 3),
            "average_attitude_error": round(evo_avg_att_error, 3),
            "final_position_error": round(evo_final_pos, 3),
            "data_points": len(evo_metrics)
        },
        "frame_based_vo": {
            "average_position_error": round(fvo_avg_pos_error, 3),
            "average_attitude_error": round(fvo_avg_att_error, 3),
            "final_position_error": round(fvo_final_pos, 3),
            "data_points": len(fvo_metrics),
            "frame_rate": fvo_data.get("frame_rate", 30)
        },
        "comparison": {
            "position_accuracy_winner": pos_winner,
            "attitude_accuracy_winner": att_winner,
            "evo_position_improvement_percent": round(pos_improvement, 1),
            "recommendation": _get_recommendation(evo_avg_pos_error, fvo_avg_pos_error, 
                                                   evo_avg_att_error, fvo_avg_att_error)
        }
    }


def _get_recommendation(evo_pos: float, fvo_pos: float, 
                        evo_att: float, fvo_att: float) -> str:
    """Generate recommendation based on comparison"""
    evo_score = 0
    fvo_score = 0
    
    if evo_pos < fvo_pos:
        evo_score += 2
    else:
        fvo_score += 2
    
    if evo_att < fvo_att:
        evo_score += 1
    else:
        fvo_score += 1
    
    if evo_score > fvo_score:
        return "Event-Based VO shows better performance. Recommended for high-dynamics scenarios."
    elif fvo_score > evo_score:
        return "Frame-Based VO shows better performance. Consider for stable descent conditions."
    else:
        return "Both methods show similar performance. Choose based on hardware constraints."
