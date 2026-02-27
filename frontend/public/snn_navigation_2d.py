"""
Event-Driven Visual Navigation using Spiking Neural Networks (SNN)
===================================================================
A simple 2D simulation of spacecraft descent using neuromorphic event cameras
and bio-inspired processing for visual odometry.

Requirements: numpy, matplotlib
Run: python snn_navigation_2d.py

Author: LandingOS Research Platform
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.collections import PatchCollection
import matplotlib.animation as animation
from dataclasses import dataclass
from typing import List, Tuple
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class Config:
    """Simulation configuration"""
    # World
    world_size: Tuple[int, int] = (400, 400)  # pixels
    num_features: int = 50  # terrain features
    
    # Spacecraft
    start_altitude: float = 300.0  # starting height
    descent_velocity: float = 30.0  # m/s downward
    lateral_drift: float = 5.0  # random lateral movement
    
    # Event Camera
    contrast_threshold: float = 0.15  # brightness change to trigger event
    noise_rate: float = 0.02  # background noise probability
    
    # SNN Parameters
    grid_size: int = 20  # size of each SNN neuron's receptive field
    leak_rate: float = 0.15  # membrane potential leak
    threshold: float = 1.0  # spike threshold
    refractory_ms: float = 10.0  # refractory period in ms
    
    # Simulation
    dt: float = 0.05  # timestep (seconds)
    total_time: float = 10.0  # simulation duration


# ============================================================================
# TERRAIN GENERATOR
# ============================================================================

class Terrain:
    """
    Simple 2D terrain with features (craters/rocks)
    Features are circles with varying sizes and brightness
    """
    def __init__(self, config: Config):
        self.config = config
        self.width, self.height = config.world_size
        self.features = self._generate_features()
        
    def _generate_features(self) -> List[dict]:
        """Generate random terrain features"""
        features = []
        for i in range(self.config.num_features):
            features.append({
                'x': np.random.uniform(0, self.width),
                'y': np.random.uniform(0, self.height),
                'radius': np.random.uniform(5, 25),
                'brightness': np.random.uniform(0.3, 1.0),
                'type': np.random.choice(['crater', 'rock'])
            })
        return features
    
    def render(self, camera_x: float, camera_y: float, altitude: float) -> np.ndarray:
        """
        Render terrain as seen from camera at given position/altitude
        Returns a 2D intensity image
        """
        # Image dimensions (what the camera sees)
        img_w, img_h = 100, 100
        image = np.ones((img_h, img_w)) * 0.1  # dark background
        
        # Scale factor based on altitude (closer = larger features)
        scale = 50.0 / max(altitude, 1.0)
        
        for feature in self.features:
            # Project feature position relative to camera
            fx = (feature['x'] - camera_x) * scale + img_w / 2
            fy = (feature['y'] - camera_y) * scale + img_h / 2
            fr = feature['radius'] * scale
            
            # Skip if outside view
            if fx < -fr or fx > img_w + fr or fy < -fr or fy > img_h + fr:
                continue
            
            # Draw circular feature
            y_coords, x_coords = np.ogrid[:img_h, :img_w]
            dist = np.sqrt((x_coords - fx)**2 + (y_coords - fy)**2)
            mask = dist < fr
            
            # Brightness profile (brighter at edges for craters, center for rocks)
            if feature['type'] == 'crater':
                profile = dist[mask] / (fr + 0.001)  # rim is bright
            else:
                profile = 1 - dist[mask] / (fr + 0.001)  # center is bright
            
            image[mask] = np.maximum(image[mask], feature['brightness'] * profile)
        
        return np.clip(image, 0, 1)


# ============================================================================
# EVENT CAMERA
# ============================================================================

@dataclass
class Event:
    """Single neuromorphic event"""
    x: int
    y: int
    timestamp: float
    polarity: int  # +1 (ON) or -1 (OFF)

class EventCamera:
    """
    Simulates a Dynamic Vision Sensor (DVS)
    Each pixel independently detects brightness changes
    """
    def __init__(self, width: int, height: int, config: Config):
        self.width = width
        self.height = height
        self.config = config
        
        # Log-intensity reference per pixel
        self.log_ref = None
        self.initialized = False
        
    def generate_events(self, intensity_image: np.ndarray, timestamp: float) -> List[Event]:
        """
        Compare current image to reference and generate events
        where brightness changed beyond threshold
        """
        events = []
        
        # Convert to log space (avoid log(0))
        log_intensity = np.log(np.clip(intensity_image, 1e-6, 1.0))
        
        # Initialize on first frame
        if not self.initialized:
            self.log_ref = log_intensity.copy()
            self.initialized = True
            return events
        
        # Compute change
        delta = log_intensity - self.log_ref
        
        # Find pixels that exceeded threshold
        # ON events (brightness increased)
        on_mask = delta > self.config.contrast_threshold
        on_y, on_x = np.where(on_mask)
        for i in range(len(on_y)):
            events.append(Event(
                x=on_x[i], 
                y=on_y[i], 
                timestamp=timestamp,
                polarity=1
            ))
        
        # OFF events (brightness decreased)
        off_mask = delta < -self.config.contrast_threshold
        off_y, off_x = np.where(off_mask)
        for i in range(len(off_y)):
            events.append(Event(
                x=off_x[i], 
                y=off_y[i], 
                timestamp=timestamp,
                polarity=-1
            ))
        
        # Update reference where events occurred
        self.log_ref[on_mask] = log_intensity[on_mask]
        self.log_ref[off_mask] = log_intensity[off_mask]
        
        # Add noise events
        num_noise = int(self.width * self.height * self.config.noise_rate)
        for _ in range(num_noise):
            events.append(Event(
                x=np.random.randint(0, self.width),
                y=np.random.randint(0, self.height),
                timestamp=timestamp + np.random.uniform(0, self.config.dt),
                polarity=np.random.choice([-1, 1])
            ))
        
        return events


# ============================================================================
# SPIKING NEURAL NETWORK - LIF Neurons for Corner Detection
# ============================================================================

class LIFNeuron:
    """
    Leaky Integrate-and-Fire Neuron
    The fundamental unit of our SNN
    """
    def __init__(self, threshold: float = 1.0, leak: float = 0.1, refractory: float = 0.01):
        self.threshold = threshold
        self.leak = leak
        self.refractory = refractory
        
        self.membrane_potential = 0.0
        self.last_spike_time = -np.inf
        
    def integrate(self, input_current: float, current_time: float, dt: float) -> bool:
        """
        Integrate input and check for spike
        Returns True if neuron fires
        """
        # Check refractory period
        if current_time - self.last_spike_time < self.refractory:
            return False
        
        # Leaky integration: V = V * (1 - leak) + input
        self.membrane_potential = self.membrane_potential * (1 - self.leak) + input_current
        
        # Check threshold
        if self.membrane_potential >= self.threshold:
            self.membrane_potential = 0.0  # Reset
            self.last_spike_time = current_time
            return True
        
        return False


class SNNCornerDetector:
    """
    Grid of LIF neurons for corner/feature detection
    Each neuron monitors a spatial region and fires when
    it detects corner-like event patterns
    """
    def __init__(self, image_width: int, image_height: int, config: Config):
        self.config = config
        self.grid_size = config.grid_size
        
        # Create neuron grid
        self.grid_w = image_width // config.grid_size
        self.grid_h = image_height // config.grid_size
        
        # One LIF neuron per grid cell
        self.neurons = [[LIFNeuron(
            threshold=config.threshold,
            leak=config.leak_rate,
            refractory=config.refractory_ms / 1000.0
        ) for _ in range(self.grid_w)] for _ in range(self.grid_h)]
        
        # Time surface for corner response
        self.time_surface = np.zeros((image_height, image_width))
        
    def process_events(self, events: List[Event], current_time: float, dt: float) -> List[dict]:
        """
        Process events through SNN and return detected corners
        """
        # Update time surface with events
        for event in events:
            if 0 <= event.x < self.time_surface.shape[1] and \
               0 <= event.y < self.time_surface.shape[0]:
                self.time_surface[event.y, event.x] = current_time
        
        # Decay time surface
        self.time_surface *= 0.95
        
        # Count events per grid cell
        event_counts = np.zeros((self.grid_h, self.grid_w))
        for event in events:
            gx = min(event.x // self.grid_size, self.grid_w - 1)
            gy = min(event.y // self.grid_size, self.grid_h - 1)
            event_counts[gy, gx] += 1
        
        corners = []
        
        # Process each neuron
        for gy in range(self.grid_h):
            for gx in range(self.grid_w):
                # Compute corner response for this cell
                corner_response = self._compute_corner_response(gx, gy)
                
                # Input current = events + corner response
                input_current = event_counts[gy, gx] * 0.1 + corner_response * 0.5
                
                # Integrate and check for spike
                if self.neurons[gy][gx].integrate(input_current, current_time, dt):
                    # Neuron spiked - corner detected!
                    corners.append({
                        'x': gx * self.grid_size + self.grid_size // 2,
                        'y': gy * self.grid_size + self.grid_size // 2,
                        'response': corner_response
                    })
        
        return corners
    
    def _compute_corner_response(self, gx: int, gy: int) -> float:
        """
        Compute Harris-like corner response from time surface
        """
        # Extract patch
        x_start = gx * self.grid_size
        y_start = gy * self.grid_size
        x_end = min(x_start + self.grid_size, self.time_surface.shape[1])
        y_end = min(y_start + self.grid_size, self.time_surface.shape[0])
        
        patch = self.time_surface[y_start:y_end, x_start:x_end]
        
        if patch.size < 4:
            return 0.0
        
        # Compute gradients
        Ix = np.zeros_like(patch)
        Iy = np.zeros_like(patch)
        
        if patch.shape[1] > 2:
            Ix[:, 1:-1] = (patch[:, 2:] - patch[:, :-2]) / 2
        if patch.shape[0] > 2:
            Iy[1:-1, :] = (patch[2:, :] - patch[:-2, :]) / 2
        
        # Harris response: det(M) - k * trace(M)^2
        Ixx = np.sum(Ix * Ix)
        Iyy = np.sum(Iy * Iy)
        Ixy = np.sum(Ix * Iy)
        
        det = Ixx * Iyy - Ixy * Ixy
        trace = Ixx + Iyy
        
        response = det - 0.04 * trace * trace
        return max(0, response)


# ============================================================================
# VISUAL ODOMETRY
# ============================================================================

class VisualOdometry:
    """
    Estimates camera motion from detected corners and events
    """
    def __init__(self, image_width: int, image_height: int):
        self.img_w = image_width
        self.img_h = image_height
        self.prev_corners = []
        
    def estimate_motion(self, corners: List[dict], events: List[Event], dt: float) -> Tuple[float, float]:
        """
        Estimate 2D motion (dx, dy) from corners and events
        Returns estimated velocity in pixels/second
        """
        if len(corners) < 2 and len(events) < 10:
            return 0.0, 0.0
        
        # Use corner centroid offset from image center
        if corners:
            cx = np.mean([c['x'] for c in corners])
            cy = np.mean([c['y'] for c in corners])
        else:
            cx = np.mean([e.x for e in events[:100]])
            cy = np.mean([e.y for e in events[:100]])
        
        # Estimate velocity from offset
        # If features are offset to the right, camera is moving left, etc.
        vx = -(cx - self.img_w / 2) * 0.5
        vy = -(cy - self.img_h / 2) * 0.5
        
        return vx, vy


# ============================================================================
# SPACECRAFT SIMULATION
# ============================================================================

class Spacecraft:
    """
    Simple 2D spacecraft descending toward terrain
    """
    def __init__(self, config: Config):
        self.config = config
        
        # Position (x, y in world coords, z is altitude)
        self.x = config.world_size[0] / 2
        self.y = config.world_size[1] / 2
        self.z = config.start_altitude
        
        # Estimated position (from visual odometry)
        self.est_x = self.x
        self.est_y = self.y
        self.est_z = self.z
        
        # History for plotting
        self.history = {
            'time': [],
            'true_x': [], 'true_y': [], 'true_z': [],
            'est_x': [], 'est_y': [], 'est_z': [],
            'events': [], 'corners': [],
            'position_error': []
        }
        
    def update_true_position(self, dt: float):
        """Update actual position (ground truth)"""
        self.z -= self.config.descent_velocity * dt
        self.x += np.random.normal(0, self.config.lateral_drift * dt)
        self.y += np.random.normal(0, self.config.lateral_drift * dt)
        
        # Keep in bounds
        self.x = np.clip(self.x, 50, self.config.world_size[0] - 50)
        self.y = np.clip(self.y, 50, self.config.world_size[1] - 50)
        self.z = max(0, self.z)
        
    def update_estimated_position(self, vx: float, vy: float, num_events: int, dt: float):
        """Update estimated position from visual odometry"""
        self.est_x += vx * dt
        self.est_y += vy * dt
        
        # Estimate altitude from event rate (more events = closer)
        self.est_z -= self.config.descent_velocity * dt
        
        # Add small drift (realistic VO behavior)
        self.est_x += np.random.normal(0, 0.1)
        self.est_y += np.random.normal(0, 0.1)
        
    def record(self, t: float, num_events: int, num_corners: int):
        """Record state for plotting"""
        self.history['time'].append(t)
        self.history['true_x'].append(self.x)
        self.history['true_y'].append(self.y)
        self.history['true_z'].append(self.z)
        self.history['est_x'].append(self.est_x)
        self.history['est_y'].append(self.est_y)
        self.history['est_z'].append(self.est_z)
        self.history['events'].append(num_events)
        self.history['corners'].append(num_corners)
        
        error = np.sqrt((self.x - self.est_x)**2 + (self.y - self.est_y)**2)
        self.history['position_error'].append(error)


# ============================================================================
# MAIN SIMULATION
# ============================================================================

def run_simulation(config: Config = None, visualize: bool = True):
    """
    Run the complete SNN-based navigation simulation
    """
    if config is None:
        config = Config()
    
    print("=" * 60)
    print("SNN-Based Event-Driven Visual Navigation Simulation")
    print("=" * 60)
    print(f"World size: {config.world_size}")
    print(f"Start altitude: {config.start_altitude}m")
    print(f"Descent velocity: {config.descent_velocity}m/s")
    print(f"SNN grid size: {config.grid_size}x{config.grid_size}")
    print("=" * 60)
    
    # Initialize components
    terrain = Terrain(config)
    spacecraft = Spacecraft(config)
    
    # Event camera (100x100 pixels)
    event_camera = EventCamera(100, 100, config)
    
    # SNN corner detector
    snn = SNNCornerDetector(100, 100, config)
    
    # Visual odometry
    vo = VisualOdometry(100, 100)
    
    # Setup visualization
    if visualize:
        plt.ion()
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('SNN Event-Driven Visual Navigation', fontsize=14, fontweight='bold')
    
    # Simulation loop
    t = 0.0
    step = 0
    
    print("\nStarting descent simulation...")
    print("-" * 60)
    
    while t < config.total_time and spacecraft.z > 0:
        # 1. Update true spacecraft position
        spacecraft.update_true_position(config.dt)
        
        # 2. Render what camera sees
        intensity_image = terrain.render(spacecraft.x, spacecraft.y, spacecraft.z)
        
        # 3. Generate events from camera
        events = event_camera.generate_events(intensity_image, t)
        
        # 4. Process events through SNN
        corners = snn.process_events(events, t, config.dt)
        
        # 5. Estimate motion with visual odometry
        vx, vy = vo.estimate_motion(corners, events, config.dt)
        
        # 6. Update estimated position
        spacecraft.update_estimated_position(vx, vy, len(events), config.dt)
        
        # 7. Record history
        spacecraft.record(t, len(events), len(corners))
        
        # Print status every 20 steps
        if step % 20 == 0:
            error = np.sqrt((spacecraft.x - spacecraft.est_x)**2 + 
                          (spacecraft.y - spacecraft.est_y)**2)
            print(f"t={t:.2f}s | Alt={spacecraft.z:.1f}m | "
                  f"Events={len(events):4d} | Corners={len(corners):2d} | "
                  f"Error={error:.2f}px")
        
        # Visualize
        if visualize and step % 5 == 0:
            _update_visualization(fig, axes, terrain, spacecraft, 
                                 intensity_image, events, corners, snn, t)
        
        t += config.dt
        step += 1
    
    print("-" * 60)
    print(f"Simulation complete! Landed at t={t:.2f}s")
    
    # Final statistics
    final_error = spacecraft.history['position_error'][-1]
    avg_error = np.mean(spacecraft.history['position_error'])
    total_events = sum(spacecraft.history['events'])
    total_corners = sum(spacecraft.history['corners'])
    
    print(f"\n=== RESULTS ===")
    print(f"Final position error: {final_error:.2f} pixels")
    print(f"Average position error: {avg_error:.2f} pixels")
    print(f"Total events generated: {total_events}")
    print(f"Total corners detected: {total_corners}")
    
    if visualize:
        plt.ioff()
        _plot_final_results(spacecraft.history)
        plt.show()
    
    return spacecraft.history


def _update_visualization(fig, axes, terrain, spacecraft, image, events, corners, snn, t):
    """Update the visualization during simulation"""
    for ax_row in axes:
        for ax in ax_row:
            ax.clear()
    
    # 1. Terrain view (top-left)
    ax = axes[0, 0]
    ax.set_xlim(0, terrain.width)
    ax.set_ylim(0, terrain.height)
    
    # Draw features
    for f in terrain.features:
        color = 'brown' if f['type'] == 'crater' else 'gray'
        circle = Circle((f['x'], f['y']), f['radius'], 
                        color=color, alpha=f['brightness'])
        ax.add_patch(circle)
    
    # Draw spacecraft position
    ax.plot(spacecraft.x, spacecraft.y, 'b^', markersize=15, label='True')
    ax.plot(spacecraft.est_x, spacecraft.est_y, 'r+', markersize=15, 
            markeredgewidth=3, label='Estimated')
    ax.set_title(f'Terrain View (Alt: {spacecraft.z:.1f}m)')
    ax.legend(loc='upper right')
    ax.set_aspect('equal')
    
    # 2. Camera view (top-middle)
    ax = axes[0, 1]
    ax.imshow(image, cmap='gray', vmin=0, vmax=1)
    ax.set_title(f'Camera View (t={t:.2f}s)')
    
    # 3. Events (top-right)
    ax = axes[0, 2]
    ax.set_xlim(0, 100)
    ax.set_ylim(100, 0)  # Flip y
    
    if events:
        on_events = [(e.x, e.y) for e in events if e.polarity == 1]
        off_events = [(e.x, e.y) for e in events if e.polarity == -1]
        
        if on_events:
            ax.scatter([e[0] for e in on_events], [e[1] for e in on_events], 
                      c='blue', s=10, alpha=0.7, label='ON')
        if off_events:
            ax.scatter([e[0] for e in off_events], [e[1] for e in off_events], 
                      c='red', s=10, alpha=0.7, label='OFF')
    
    ax.set_title(f'Events ({len(events)})')
    ax.legend(loc='upper right', fontsize=8)
    
    # 4. SNN Time Surface (bottom-left)
    ax = axes[1, 0]
    ax.imshow(snn.time_surface, cmap='hot', vmin=0)
    ax.set_title('SNN Time Surface')
    
    # 5. Detected Corners (bottom-middle)
    ax = axes[1, 1]
    ax.imshow(image, cmap='gray', vmin=0, vmax=1, alpha=0.5)
    if corners:
        ax.scatter([c['x'] for c in corners], [c['y'] for c in corners], 
                  c='yellow', s=100, marker='+', linewidths=2)
    ax.set_title(f'SNN Corners ({len(corners)})')
    
    # 6. Position error (bottom-right)
    ax = axes[1, 2]
    if spacecraft.history['time']:
        ax.plot(spacecraft.history['time'], spacecraft.history['position_error'], 'b-')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Error (pixels)')
        ax.set_title('Position Error')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.pause(0.01)


def _plot_final_results(history):
    """Plot final results after simulation"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('SNN Navigation - Final Results', fontsize=14, fontweight='bold')
    
    # 1. Trajectory comparison
    ax = axes[0, 0]
    ax.plot(history['true_x'], history['true_y'], 'b-', linewidth=2, label='True')
    ax.plot(history['est_x'], history['est_y'], 'r--', linewidth=2, label='Estimated')
    ax.set_xlabel('X Position (pixels)')
    ax.set_ylabel('Y Position (pixels)')
    ax.set_title('2D Trajectory')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    # 2. Altitude profile
    ax = axes[0, 1]
    ax.plot(history['time'], history['true_z'], 'b-', linewidth=2, label='True')
    ax.plot(history['time'], history['est_z'], 'r--', linewidth=2, label='Estimated')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Altitude (m)')
    ax.set_title('Altitude vs Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. Events and corners
    ax = axes[1, 0]
    ax.plot(history['time'], history['events'], 'b-', alpha=0.7, label='Events')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Events per step', color='blue')
    ax.tick_params(axis='y', labelcolor='blue')
    
    ax2 = ax.twinx()
    ax2.plot(history['time'], history['corners'], 'r-', alpha=0.7, label='Corners')
    ax2.set_ylabel('Corners detected', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    
    ax.set_title('Event & Corner Activity')
    ax.grid(True, alpha=0.3)
    
    # 4. Position error
    ax = axes[1, 1]
    ax.plot(history['time'], history['position_error'], 'g-', linewidth=2)
    ax.fill_between(history['time'], 0, history['position_error'], alpha=0.3, color='green')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Position Error (pixels)')
    ax.set_title(f'Position Error (Final: {history["position_error"][-1]:.2f}px)')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("   EVENT-DRIVEN VISUAL NAVIGATION WITH SNN")
    print("   Simulating Spacecraft Descent using Neuromorphic Vision")
    print("="*60 + "\n")
    
    # Create configuration
    config = Config(
        world_size=(400, 400),
        num_features=50,
        start_altitude=300.0,
        descent_velocity=30.0,
        grid_size=20,
        total_time=10.0
    )
    
    # Run simulation with visualization
    results = run_simulation(config, visualize=True)
    
    print("\n" + "="*60)
    print("Simulation finished! Close the plot window to exit.")
    print("="*60)
