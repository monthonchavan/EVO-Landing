"""
Spiking Neural Network (SNN) Inspired Event Processor
Implements bio-inspired algorithms for event-based feature detection and tracking.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import math

@dataclass
class Neuron:
    """Simple Leaky Integrate-and-Fire (LIF) neuron model"""
    membrane_potential: float = 0.0
    threshold: float = 1.0
    leak_rate: float = 0.1
    refractory_period: float = 0.001  # 1ms
    last_spike_time: float = -1.0
    
    def integrate(self, input_current: float, dt: float, current_time: float) -> bool:
        """Integrate input and check for spike"""
        # Check refractory period
        if current_time - self.last_spike_time < self.refractory_period:
            return False
        
        # Leaky integration
        self.membrane_potential = (1 - self.leak_rate * dt) * self.membrane_potential + input_current
        
        # Spike detection
        if self.membrane_potential >= self.threshold:
            self.membrane_potential = 0.0
            self.last_spike_time = current_time
            return True
        
        return False


class SNNCornerDetector:
    """
    SNN-based corner detection for event streams.
    Uses a grid of LIF neurons to detect corners based on event patterns.
    """
    
    def __init__(self, width: int = 640, height: int = 480, grid_size: int = 8):
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.grid_w = width // grid_size
        self.grid_h = height // grid_size
        
        # Create neuron grid for corner detection
        self.neurons = {}
        for gx in range(self.grid_w):
            for gy in range(self.grid_h):
                self.neurons[(gx, gy)] = Neuron(threshold=0.8, leak_rate=0.15)
        
        # Surface of Active Events (SAE) - time surface
        self.time_surface = np.zeros((height, width), dtype=np.float32)
        self.polarity_surface = np.zeros((height, width), dtype=np.int8)
        
        # Corner response accumulator
        self.corner_response = np.zeros((self.grid_h, self.grid_w), dtype=np.float32)
        
    def update_time_surface(self, events: List[Dict], current_time: float):
        """Update the time surface with new events"""
        decay_rate = 0.01  # Decay old events
        
        # Apply decay
        self.time_surface *= np.exp(-decay_rate * 0.05)  # 50ms decay constant
        
        for event in events:
            x, y = event['x'], event['y']
            if 0 <= x < self.width and 0 <= y < self.height:
                self.time_surface[y, x] = 1.0
                self.polarity_surface[y, x] = event['polarity']
    
    def compute_harris_response(self, cx: int, cy: int, patch_size: int = 8) -> float:
        """Compute Harris-like corner response from event time surface"""
        half = patch_size // 2
        
        # Extract patch from time surface
        y_start = max(0, cy - half)
        y_end = min(self.height, cy + half)
        x_start = max(0, cx - half)
        x_end = min(self.width, cx + half)
        
        patch = self.time_surface[y_start:y_end, x_start:x_end]
        
        if patch.size < 4:
            return 0.0
        
        # Compute gradients
        Ix = np.zeros_like(patch)
        Iy = np.zeros_like(patch)
        
        if patch.shape[1] > 2:
            Ix[:, 1:-1] = patch[:, 2:] - patch[:, :-2]
        if patch.shape[0] > 2:
            Iy[1:-1, :] = patch[2:, :] - patch[:-2, :]
        
        # Structure tensor elements
        Ixx = np.sum(Ix * Ix)
        Iyy = np.sum(Iy * Iy)
        Ixy = np.sum(Ix * Iy)
        
        # Harris response
        det = Ixx * Iyy - Ixy * Ixy
        trace = Ixx + Iyy
        k = 0.04  # Harris constant
        
        response = det - k * trace * trace
        return max(0, response)
    
    def detect_corners(self, events: List[Dict], current_time: float) -> List[Dict]:
        """Detect corners using SNN-inspired processing"""
        if not events:
            return []
        
        # Update time surface
        self.update_time_surface(events, current_time)
        
        corners = []
        
        # Process each grid cell
        for gx in range(self.grid_w):
            for gy in range(self.grid_h):
                # Count events in this cell
                cell_events = [e for e in events 
                              if (e['x'] // self.grid_size == gx and 
                                  e['y'] // self.grid_size == gy)]
                
                if len(cell_events) < 3:
                    continue
                
                # Center of cell in pixel coordinates
                cx = gx * self.grid_size + self.grid_size // 2
                cy = gy * self.grid_size + self.grid_size // 2
                
                # Compute Harris-like corner response
                response = self.compute_harris_response(cx, cy)
                
                # Feed response to LIF neuron
                neuron = self.neurons[(gx, gy)]
                input_current = response * len(cell_events) / 10.0
                
                if neuron.integrate(input_current, 0.001, current_time):
                    # Neuron spiked - corner detected!
                    corners.append({
                        'x': cx,
                        'y': cy,
                        'response': response,
                        'event_count': len(cell_events),
                        'type': 'harris_snn'
                    })
                
                self.corner_response[gy, gx] = response
        
        return corners
    
    def get_feature_map(self) -> np.ndarray:
        """Get the current corner response map"""
        return self.corner_response.copy()


class EventNoiseFilter:
    """
    Vibration-aware noise filter for event streams.
    Filters out noise events caused by high-frequency vibrations.
    """
    
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        
        # Refractory filter - recent event timestamps per pixel
        self.last_event_time = np.full((height, width), -np.inf, dtype=np.float32)
        
        # Spatial correlation filter
        self.event_density = np.zeros((height // 4, width // 4), dtype=np.float32)
        
        # Parameters
        self.refractory_period = 0.001  # 1ms - reject events too close in time
        self.min_neighbors = 2  # Minimum neighbor events for validity
        self.neighbor_radius = 3  # pixels
        
    def filter_events(self, events: List[Dict], vibration_amplitude: float = 0.5) -> List[Dict]:
        """Filter noise events considering vibration level"""
        if not events:
            return []
        
        filtered = []
        
        # Adjust refractory period based on vibration
        adaptive_refractory = self.refractory_period * (1 + vibration_amplitude)
        
        for event in events:
            x, y, t = event['x'], event['y'], event['timestamp'] / 1e6  # Convert to seconds
            
            if not (0 <= x < self.width and 0 <= y < self.height):
                continue
            
            # Refractory filter
            if t - self.last_event_time[y, x] < adaptive_refractory:
                continue
            
            # Spatial correlation filter - check for nearby recent events
            neighbors = 0
            for dx in range(-self.neighbor_radius, self.neighbor_radius + 1):
                for dy in range(-self.neighbor_radius, self.neighbor_radius + 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if t - self.last_event_time[ny, nx] < 0.01:  # 10ms window
                            neighbors += 1
            
            # Accept event if it has enough neighbors or is strong
            if neighbors >= self.min_neighbors:
                filtered.append(event)
                self.last_event_time[y, x] = t
                
                # Update density map
                gx, gy = x // 4, y // 4
                if gx < self.event_density.shape[1] and gy < self.event_density.shape[0]:
                    self.event_density[gy, gx] = min(1.0, self.event_density[gy, gx] + 0.1)
        
        # Decay density map
        self.event_density *= 0.95
        
        return filtered


class SNNFeatureTracker:
    """
    SNN-based feature tracking across event windows.
    Uses spike-timing-dependent plasticity (STDP) inspired learning.
    """
    
    def __init__(self, max_features: int = 100):
        self.max_features = max_features
        self.features = []  # List of tracked features
        self.feature_neurons = {}  # Neuron per feature for temporal processing
        
    def update(self, detected_corners: List[Dict], current_time: float) -> List[Dict]:
        """Update feature tracks with newly detected corners"""
        if not detected_corners:
            return self.features
        
        # Match new corners to existing features
        matched = set()
        
        for corner in detected_corners:
            best_match = None
            best_dist = float('inf')
            
            for i, feature in enumerate(self.features):
                if i in matched:
                    continue
                
                dist = math.sqrt(
                    (corner['x'] - feature['x'])**2 + 
                    (corner['y'] - feature['y'])**2
                )
                
                if dist < 20 and dist < best_dist:  # 20 pixel matching threshold
                    best_match = i
                    best_dist = dist
            
            if best_match is not None:
                # Update existing feature (STDP-like weight update)
                feature = self.features[best_match]
                alpha = 0.3  # Learning rate
                feature['x'] = (1 - alpha) * feature['x'] + alpha * corner['x']
                feature['y'] = (1 - alpha) * feature['y'] + alpha * corner['y']
                feature['response'] = corner['response']
                feature['age'] += 1
                feature['last_seen'] = current_time
                matched.add(best_match)
            else:
                # Create new feature
                if len(self.features) < self.max_features:
                    self.features.append({
                        'id': len(self.features),
                        'x': corner['x'],
                        'y': corner['y'],
                        'response': corner['response'],
                        'age': 1,
                        'created': current_time,
                        'last_seen': current_time
                    })
        
        # Remove stale features
        self.features = [f for f in self.features 
                        if current_time - f['last_seen'] < 0.5]  # 500ms timeout
        
        return self.features
    
    def get_optical_flow(self) -> List[Dict]:
        """Compute optical flow from feature tracks"""
        flows = []
        for feature in self.features:
            if feature['age'] > 1:
                # Estimate flow from recent motion
                flows.append({
                    'x': feature['x'],
                    'y': feature['y'],
                    'vx': 0,  # Would need history for actual flow
                    'vy': 0,
                    'age': feature['age']
                })
        return flows


class SNNVisualOdometry:
    """
    Enhanced Visual Odometry using SNN-inspired processing.
    Combines corner detection, noise filtering, and feature tracking.
    """
    
    def __init__(self, width: int = 640, height: int = 480):
        self.corner_detector = SNNCornerDetector(width, height)
        self.noise_filter = EventNoiseFilter(width, height)
        self.feature_tracker = SNNFeatureTracker()
        
        self.last_pose = {'x': 0, 'y': 0, 'z': 0, 'roll': 0, 'pitch': 0, 'yaw': 0}
        self.accumulated_drift = {'x': 0, 'y': 0, 'z': 0}
        
    def process_events(self, events: List[Dict], dt: float, vibration: float = 0.5) -> Dict:
        """Process events with SNN pipeline and estimate motion"""
        if not events:
            return {'dx': 0, 'dy': 0, 'dz': 0, 'droll': 0, 'dpitch': 0, 'dyaw': 0}
        
        current_time = events[-1]['timestamp'] / 1e6 if events else 0
        
        # Step 1: Filter noise
        filtered_events = self.noise_filter.filter_events(events, vibration)
        
        # Step 2: Detect corners
        corners = self.corner_detector.detect_corners(filtered_events, current_time)
        
        # Step 3: Track features
        features = self.feature_tracker.update(corners, current_time)
        
        # Step 4: Estimate motion from features
        motion = self._estimate_motion(features, filtered_events, dt)
        
        return motion
    
    def _estimate_motion(self, features: List[Dict], events: List[Dict], dt: float) -> Dict:
        """Estimate camera motion from tracked features"""
        if len(features) < 3:
            return {'dx': 0, 'dy': 0, 'dz': 0, 'droll': 0, 'dpitch': 0, 'dyaw': 0}
        
        # Compute centroid of features
        cx = sum(f['x'] for f in features) / len(features)
        cy = sum(f['y'] for f in features) / len(features)
        
        # Compute radial flow (expansion/contraction)
        total_strength = sum(f['response'] for f in features) + 0.001
        radial_flow = sum(
            math.sqrt((f['x'] - 320)**2 + (f['y'] - 240)**2) * f['response']
            for f in features
        ) / total_strength
        
        # Compute rotation from feature distribution asymmetry
        moment_x = sum((f['x'] - 320) * f['response'] for f in features) / total_strength
        moment_y = sum((f['y'] - 240) * f['response'] for f in features) / total_strength
        
        # Motion estimation
        drift_factor = 0.0005  # Reduced drift for SNN processing
        
        return {
            'dx': (cx - 320) * 0.0008 * dt + np.random.normal(0, drift_factor),
            'dy': (cy - 240) * 0.0008 * dt + np.random.normal(0, drift_factor),
            'dz': -radial_flow * 0.008 * dt,
            'droll': moment_y * 0.00001 + np.random.normal(0, drift_factor),
            'dpitch': moment_x * 0.00001 + np.random.normal(0, drift_factor),
            'dyaw': np.random.normal(0, drift_factor * 0.5)
        }
    
    def get_corner_map(self) -> np.ndarray:
        """Get corner response visualization"""
        return self.corner_detector.get_feature_map()
    
    def get_tracked_features(self) -> List[Dict]:
        """Get currently tracked features"""
        return self.feature_tracker.features
