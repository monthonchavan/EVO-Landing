"""
Minimal SNN Event-Driven Navigation
====================================
The simplest possible implementation of:
1. Event camera simulation
2. SNN corner detection  
3. Visual odometry

Just numpy required. No visualization dependencies.
Run: python snn_minimal.py
"""

import numpy as np
from typing import List, Tuple


# ============================================================================
# 1. EVENT CAMERA - Detects brightness changes
# ============================================================================

class EventCamera:
    """
    Dynamic Vision Sensor (DVS) simulation
    Each pixel fires when brightness changes by > threshold
    """
    def __init__(self, width: int = 64, height: int = 64, threshold: float = 0.15):
        self.width = width
        self.height = height
        self.threshold = threshold
        self.log_ref = None  # Reference log-intensity
        
    def process(self, image: np.ndarray) -> List[Tuple[int, int, int]]:
        """
        Compare image to reference, return events as (x, y, polarity)
        polarity: +1 = brighter, -1 = darker
        """
        # Convert to log space
        log_img = np.log(np.clip(image, 1e-6, 1.0))
        
        # First frame - just store reference
        if self.log_ref is None:
            self.log_ref = log_img.copy()
            return []
        
        # Find changes exceeding threshold
        delta = log_img - self.log_ref
        
        events = []
        
        # ON events (got brighter)
        on_y, on_x = np.where(delta > self.threshold)
        for x, y in zip(on_x, on_y):
            events.append((x, y, 1))
        
        # OFF events (got darker)
        off_y, off_x = np.where(delta < -self.threshold)
        for x, y in zip(off_x, off_y):
            events.append((x, y, -1))
        
        # Update reference where events occurred
        self.log_ref[delta > self.threshold] = log_img[delta > self.threshold]
        self.log_ref[delta < -self.threshold] = log_img[delta < -self.threshold]
        
        return events


# ============================================================================
# 2. SNN CORNER DETECTOR - LIF neurons detect features
# ============================================================================

class LIFNeuron:
    """
    Leaky Integrate-and-Fire neuron
    
    Dynamics: V = V * (1 - leak) + input
    Fires when V >= threshold, then resets
    """
    def __init__(self, threshold: float = 1.0, leak: float = 0.1):
        self.threshold = threshold
        self.leak = leak
        self.V = 0.0  # Membrane potential
        
    def step(self, input_current: float) -> bool:
        """Process one timestep, return True if spike"""
        # Leaky integration
        self.V = self.V * (1 - self.leak) + input_current
        
        # Check for spike
        if self.V >= self.threshold:
            self.V = 0.0  # Reset
            return True
        return False


class SNNDetector:
    """
    Grid of LIF neurons for corner detection
    """
    def __init__(self, img_width: int, img_height: int, cell_size: int = 8):
        self.cell_size = cell_size
        self.grid_w = img_width // cell_size
        self.grid_h = img_height // cell_size
        
        # Create neuron grid
        self.neurons = [[LIFNeuron() for _ in range(self.grid_w)] 
                        for _ in range(self.grid_h)]
        
        # Time surface for gradient computation
        self.time_surface = np.zeros((img_height, img_width))
        self.time = 0
        
    def process(self, events: List[Tuple[int, int, int]]) -> List[Tuple[int, int, float]]:
        """
        Process events, return detected corners as (x, y, strength)
        """
        self.time += 1
        
        # Update time surface
        for x, y, p in events:
            if 0 <= x < self.time_surface.shape[1] and 0 <= y < self.time_surface.shape[0]:
                self.time_surface[y, x] = self.time
        
        # Decay time surface
        self.time_surface *= 0.9
        
        # Count events per cell
        counts = np.zeros((self.grid_h, self.grid_w))
        for x, y, p in events:
            gx = min(x // self.cell_size, self.grid_w - 1)
            gy = min(y // self.cell_size, self.grid_h - 1)
            counts[gy, gx] += 1
        
        corners = []
        
        # Process each neuron
        for gy in range(self.grid_h):
            for gx in range(self.grid_w):
                # Compute Harris-like corner response
                response = self._harris_response(gx, gy)
                
                # Input = event count + corner response
                input_current = counts[gy, gx] * 0.05 + response * 0.3
                
                # Feed to neuron
                if self.neurons[gy][gx].step(input_current):
                    cx = gx * self.cell_size + self.cell_size // 2
                    cy = gy * self.cell_size + self.cell_size // 2
                    corners.append((cx, cy, response))
        
        return corners
    
    def _harris_response(self, gx: int, gy: int) -> float:
        """Compute corner response from time surface gradients"""
        x0 = gx * self.cell_size
        y0 = gy * self.cell_size
        x1 = min(x0 + self.cell_size, self.time_surface.shape[1])
        y1 = min(y0 + self.cell_size, self.time_surface.shape[0])
        
        patch = self.time_surface[y0:y1, x0:x1]
        if patch.size < 4:
            return 0.0
        
        # Gradients
        Ix = np.diff(patch, axis=1, prepend=0)
        Iy = np.diff(patch, axis=0, prepend=0)
        
        # Structure tensor
        Ixx = np.sum(Ix * Ix)
        Iyy = np.sum(Iy * Iy)
        Ixy = np.sum(Ix * Iy)
        
        # Harris: det(M) - k*trace(M)^2
        det = Ixx * Iyy - Ixy * Ixy
        trace = Ixx + Iyy
        return max(0, det - 0.04 * trace * trace)


# ============================================================================
# 3. VISUAL ODOMETRY - Estimate motion from corners
# ============================================================================

class VisualOdometry:
    """
    Simple 2D visual odometry from detected corners
    """
    def __init__(self, img_width: int, img_height: int):
        self.cx = img_width / 2
        self.cy = img_height / 2
        
    def estimate_velocity(self, corners: List[Tuple[int, int, float]]) -> Tuple[float, float]:
        """
        Estimate (vx, vy) from corner positions
        Corners offset from center indicate motion
        """
        if len(corners) < 2:
            return 0.0, 0.0
        
        # Compute centroid
        mean_x = np.mean([c[0] for c in corners])
        mean_y = np.mean([c[1] for c in corners])
        
        # Offset from center indicates motion
        vx = -(mean_x - self.cx) * 0.1
        vy = -(mean_y - self.cy) * 0.1
        
        return vx, vy


# ============================================================================
# 4. SIMPLE SIMULATION
# ============================================================================

def create_moving_scene(width: int, height: int, num_features: int = 20) -> List[dict]:
    """Create random features"""
    return [{
        'x': np.random.uniform(0, width),
        'y': np.random.uniform(0, height),
        'r': np.random.uniform(3, 10),
        'b': np.random.uniform(0.3, 1.0)
    } for _ in range(num_features)]


def render_scene(features: List[dict], cam_x: float, cam_y: float, 
                 scale: float, img_size: int = 64) -> np.ndarray:
    """Render features as seen from camera"""
    img = np.ones((img_size, img_size)) * 0.1
    
    for f in features:
        # Project feature
        fx = (f['x'] - cam_x) * scale + img_size / 2
        fy = (f['y'] - cam_y) * scale + img_size / 2
        fr = f['r'] * scale
        
        if fx < -fr or fx > img_size + fr or fy < -fr or fy > img_size + fr:
            continue
        
        # Draw circle
        y, x = np.ogrid[:img_size, :img_size]
        mask = (x - fx)**2 + (y - fy)**2 < fr**2
        img[mask] = np.maximum(img[mask], f['b'])
    
    return img


def run_demo():
    """Run a simple navigation demo"""
    print("=" * 50)
    print("SNN Event-Driven Navigation - Minimal Demo")
    print("=" * 50)
    
    # Setup
    img_size = 64
    features = create_moving_scene(200, 200, num_features=30)
    
    camera = EventCamera(img_size, img_size, threshold=0.12)
    snn = SNNDetector(img_size, img_size, cell_size=8)
    vo = VisualOdometry(img_size, img_size)
    
    # Simulate descent
    true_x, true_y = 100.0, 100.0
    est_x, est_y = 100.0, 100.0
    altitude = 150.0
    
    print(f"\nStarting at altitude {altitude}m")
    print("-" * 50)
    
    total_events = 0
    total_corners = 0
    
    for step in range(100):
        # Move camera (descending + lateral drift)
        altitude -= 1.5
        true_x += np.random.normal(0, 0.3)
        true_y += np.random.normal(0, 0.3)
        
        if altitude <= 0:
            break
        
        # Scale based on altitude
        scale = 30.0 / max(altitude, 1)
        
        # Render scene
        image = render_scene(features, true_x, true_y, scale, img_size)
        
        # Generate events
        events = camera.process(image)
        total_events += len(events)
        
        # Detect corners with SNN
        corners = snn.process(events)
        total_corners += len(corners)
        
        # Estimate velocity
        vx, vy = vo.estimate_velocity(corners)
        
        # Update estimated position
        est_x += vx
        est_y += vy
        
        # Print every 20 steps
        if step % 20 == 0:
            error = np.sqrt((true_x - est_x)**2 + (true_y - est_y)**2)
            print(f"Step {step:3d} | Alt={altitude:5.1f}m | "
                  f"Events={len(events):4d} | Corners={len(corners):2d} | "
                  f"Error={error:.2f}")
    
    # Final results
    final_error = np.sqrt((true_x - est_x)**2 + (true_y - est_y)**2)
    
    print("-" * 50)
    print(f"\n=== FINAL RESULTS ===")
    print(f"Total events:  {total_events}")
    print(f"Total corners: {total_corners}")
    print(f"Final error:   {final_error:.2f} pixels")
    print(f"True position: ({true_x:.1f}, {true_y:.1f})")
    print(f"Est. position: ({est_x:.1f}, {est_y:.1f})")
    print("=" * 50)
    
    return {
        'total_events': total_events,
        'total_corners': total_corners,
        'final_error': final_error
    }


# ============================================================================
# ALGORITHM EXPLANATION
# ============================================================================

"""
HOW IT WORKS:
=============

1. EVENT CAMERA (EventCamera class)
   - Mimics Dynamic Vision Sensor (DVS)
   - Each pixel independently monitors log(brightness)
   - Fires event when: |log(I_new) - log(I_ref)| > threshold
   - Output: sparse list of (x, y, polarity) events
   
2. SNN CORNER DETECTOR (SNNDetector class)
   - Grid of Leaky Integrate-and-Fire (LIF) neurons
   - Each neuron monitors a spatial region (cell)
   - Input current = (event_count * 0.05) + (harris_response * 0.3)
   - Neuron dynamics: V = V * 0.9 + input
   - Fires spike when V >= 1.0 (corner detected!)
   - Harris response computed from time surface gradients
   
3. VISUAL ODOMETRY (VisualOdometry class)
   - Centroid of detected corners indicates camera motion
   - If corners are offset to the right → camera moving left
   - Simple but effective for 2D navigation

KEY EQUATIONS:
==============

Event Generation:
    event if |log(I(t)) - log(I_ref)| > C
    
LIF Neuron:
    V[t+1] = V[t] * (1 - leak) + I[t]
    spike if V >= threshold
    
Harris Corner Response:
    M = [sum(Ix²)    sum(Ix*Iy)]
        [sum(Ix*Iy)  sum(Iy²)  ]
    R = det(M) - k * trace(M)²

Motion Estimation:
    vx = -(mean_corner_x - image_center_x) * gain
    vy = -(mean_corner_y - image_center_y) * gain
"""


if __name__ == "__main__":
    run_demo()
