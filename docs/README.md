# LandingOS Documentation

## Event-Driven Visual Navigation for Precision Planetary Landing

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [Core Concepts](#core-concepts)
5. [API Reference](#api-reference)
6. [Hardware Integration](#hardware-integration)
7. [Data Export](#data-export)
8. [AI Analysis](#ai-analysis)
9. [Configuration Guide](#configuration-guide)
10. [Algorithm Details](#algorithm-details)
11. [Troubleshooting](#troubleshooting)

---

## Overview

LandingOS is a comprehensive research platform for developing and testing Event-Based Visual Odometry (EVO) algorithms designed for spacecraft precision landing in extreme planetary environments.

### Key Features

- **Event Camera Simulation**: Generate synthetic neuromorphic event data mimicking descent scenarios
- **Visual Odometry Engine**: Real-time pose estimation from event streams
- **AI-Powered Analysis**: GPT-4o powered insights for experiment optimization
- **Hardware Data Import**: Support for Prophesee, iniVation, and standard formats
- **Data Export**: CSV and JSON export for research papers and analysis
- **Real-time Visualization**: Event stream, trajectory, and performance metrics

### Use Cases

1. **Algorithm Development**: Test new EVO algorithms in controlled environments
2. **Parameter Optimization**: Find optimal settings for different terrains
3. **Hardware Validation**: Compare simulated vs real hardware data
4. **Educational**: Learn about event-based vision and visual odometry

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        LandingOS Platform                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   Frontend   │    │   Backend    │    │     MongoDB      │  │
│  │   (React)    │◄──►│  (FastAPI)   │◄──►│   (Experiments)  │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│         │                   │                                    │
│         │            ┌──────┴──────┐                            │
│         │            │             │                            │
│  ┌──────▼──────┐  ┌──▼───┐  ┌─────▼─────┐  ┌──────────────┐   │
│  │  Dashboard  │  │ EVO  │  │    AI     │  │   Hardware   │   │
│  │    UI       │  │Engine│  │ Analysis  │  │   Import     │   │
│  └─────────────┘  └──────┘  └───────────┘  └──────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | React, Recharts | User interface, visualization |
| Backend | FastAPI (Python) | API server, simulation engine |
| EVO Engine | NumPy | Event generation, visual odometry |
| AI Analysis | GPT-4o via Emergent | Experiment insights |
| Database | MongoDB | Experiment persistence |

---

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.10+
- MongoDB

### Quick Start

1. **Access the Dashboard**
   ```
   Navigate to: https://links-1.preview.emergentagent.com
   ```

2. **Create a Simulation**
   - Select terrain type (Lunar/Mars)
   - Set initial altitude (100-10000m)
   - Configure descent velocity (5-200 m/s)
   - Adjust vibration and noise levels

3. **Run Simulation**
   - Click "Start" to begin descent
   - Watch real-time event visualization
   - Monitor performance metrics
   - Use "Pause" to stop, "Reset" to restart

4. **Analyze Results**
   - Enable AI Analysis toggle
   - Click "Analyze Results" for insights
   - Export data for further analysis

---

## Core Concepts

### Event Camera Basics

Unlike traditional cameras that capture frames at fixed intervals, neuromorphic event cameras output **asynchronous events** when individual pixels detect brightness changes.

```
Event = {
    x: pixel column (0-639),
    y: pixel row (0-479),
    timestamp: microseconds,
    polarity: +1 (brightness increase) or -1 (decrease)
}
```

### Visual Odometry

Visual Odometry (VO) estimates camera motion by:

1. **Feature Detection**: Identify stable terrain features
2. **Feature Tracking**: Follow features across event streams
3. **Motion Estimation**: Calculate pose change from feature flow

### Simulation Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| `terrain_type` | lunar, mars | Surface characteristics |
| `initial_altitude` | 100-10000m | Starting height |
| `descent_velocity` | 5-200 m/s | Vertical speed |
| `vibration_amplitude` | 0-5° | Engine vibration |
| `vibration_frequency` | 1-100 Hz | Vibration rate |
| `noise_level` | 0-1 | Sensor noise injection |
| `feature_density` | 50-500 | Terrain feature count |

---

## API Reference

### Base URL
```
https://links-1.preview.emergentagent.com/api/landingos
```

### Simulation Endpoints

#### Create Simulation
```http
POST /simulation/create
Content-Type: application/json

{
    "terrain_type": "lunar",
    "initial_altitude": 1000,
    "descent_velocity": 50,
    "vibration_amplitude": 0.5,
    "noise_level": 0.1,
    "feature_density": 200
}

Response:
{
    "id": "abc123",
    "status": "created",
    "time": 0.0,
    "altitude": 1000.0,
    "events_generated": 0,
    "metrics": {...}
}
```

#### Step Simulation
```http
POST /simulation/{sim_id}/step?steps=5

Response:
{
    "simulation_id": "abc123",
    "steps_executed": 5,
    "final_result": {
        "status": "running",
        "time": 0.25,
        "altitude": 987.5,
        "events": [...],
        "metrics": {...}
    }
}
```

#### Get Simulation State
```http
GET /simulation/{sim_id}/state

Response:
{
    "id": "abc123",
    "time": 5.0,
    "is_running": true,
    "events_generated": 12500,
    "ground_truth_poses": [...],
    "estimated_poses": [...]
}
```

#### Reset Simulation
```http
POST /simulation/{sim_id}/reset

Response:
{
    "status": "reset",
    "simulation_id": "abc123"
}
```

#### Delete Simulation
```http
DELETE /simulation/{sim_id}

Response:
{
    "status": "deleted",
    "simulation_id": "abc123"
}
```

### Experiment Endpoints

#### Create Experiment
```http
POST /experiment/create
Content-Type: application/json

{
    "name": "Lunar Landing Test 1",
    "description": "Testing high vibration scenario",
    "config": {
        "terrain_type": "lunar",
        "initial_altitude": 500,
        "vibration_amplitude": 2.0
    }
}
```

#### Run Experiment
```http
POST /experiment/{exp_id}/run?total_steps=200
```

#### List Experiments
```http
GET /experiments
```

### AI Analysis Endpoints

#### Analyze Simulation
```http
POST /ai/analyze
Content-Type: application/json

{
    "simulation_id": "abc123",
    "analysis_type": "simulation"
}

Response:
{
    "enabled": true,
    "analysis": "## Performance Assessment\n..."
}
```

#### Compare Experiments
```http
POST /ai/analyze
Content-Type: application/json

{
    "experiment_ids": ["exp1", "exp2", "exp3"],
    "analysis_type": "comparison"
}
```

#### Get Parameter Suggestions
```http
POST /ai/analyze
Content-Type: application/json

{
    "analysis_type": "suggestion",
    "target_accuracy": 0.5
}
```

---

## Hardware Integration

### Supported Formats

| Format | Extension | Source |
|--------|-----------|--------|
| CSV | .csv | Universal |
| JSON | .json | Custom |
| Text | .txt | Legacy |
| NumPy | .npy | Python |
| AEDAT 4.0 | .aedat4, .aedat | Prophesee/iniVation |
| RAW | .raw | Prophesee EVK |

### CSV Format Example
```csv
x,y,timestamp,polarity
320,240,1000000,1
321,241,1000050,-1
319,239,1000100,1
```

### JSON Format Example
```json
{
    "metadata": {
        "camera": "Prophesee EVK4",
        "resolution": [1280, 720]
    },
    "events": [
        {"x": 320, "y": 240, "timestamp": 1000000, "polarity": 1},
        {"x": 321, "y": 241, "timestamp": 1000050, "polarity": -1}
    ]
}
```

### Import via API
```http
POST /import/upload
Content-Type: multipart/form-data

file: <binary data>
format_hint: csv (optional)

Response:
{
    "success": true,
    "dataset_id": "hw123",
    "total_events": 50000,
    "duration_ms": 1000.5
}
```

### Supported Hardware

- **Prophesee EVK4**: 1280x720, RAW/AEDAT4
- **iniVation DAVIS346**: 346x260, AEDAT4
- **Samsung DVS**: 640x480, RAW
- **Custom sensors**: CSV/JSON export

---

## Data Export

### Export Events
```http
GET /export/simulation/{sim_id}/events?format=csv

# Returns downloadable CSV file
```

### Export Trajectory
```http
GET /export/simulation/{sim_id}/trajectory?format=json

# Returns ground truth and estimated poses
```

### Export Experiment
```http
GET /export/experiment/{exp_id}

# Returns complete experiment data including:
# - Configuration
# - Results
# - Trajectory
# - Metrics history
```

### Python Export Example
```python
import requests

# Export trajectory
response = requests.get(
    f"{API_URL}/export/simulation/{sim_id}/trajectory",
    params={"format": "json"}
)
trajectory_data = response.json()

# Save to file
with open("trajectory.json", "w") as f:
    json.dump(trajectory_data, f, indent=2)
```

---

## AI Analysis

### Features

- **Performance Assessment**: Evaluate simulation quality
- **Issue Detection**: Identify potential problems
- **Optimization Suggestions**: Parameter recommendations
- **Experiment Comparison**: Cross-run analysis

### Toggle Control

The AI Analysis feature can be enabled/disabled via the toggle in the top bar. When disabled:
- No API calls to AI service
- Local metrics still available
- Reduced latency

### Analysis Types

1. **Simulation Analysis**
   - Position/attitude error evaluation
   - Drift rate assessment
   - Latency analysis
   - Risk evaluation

2. **Experiment Comparison**
   - Best/worst configuration identification
   - Trend analysis
   - Next experiment recommendations

3. **Parameter Suggestions**
   - Target accuracy-based optimization
   - Physical constraint consideration

---

## Configuration Guide

### Terrain Types

#### Lunar Surface
- High crater density
- Sharp shadows
- Low albedo variation
- Recommended for: precision landing tests

#### Martian Surface
- Mixed rocks and craters
- Dust effects simulation
- Higher texture variation
- Recommended for: robustness tests

### Vibration Settings

| Scenario | Amplitude | Frequency |
|----------|-----------|-----------|
| Gentle descent | 0.1-0.3° | 5-10 Hz |
| Normal landing | 0.3-1.0° | 10-30 Hz |
| High thrust | 1.0-3.0° | 30-60 Hz |
| Emergency | 3.0-5.0° | 50-100 Hz |

### Noise Injection

| Level | Value | Use Case |
|-------|-------|----------|
| Clean | 0.0 | Algorithm validation |
| Light | 0.1 | Normal operation |
| Medium | 0.3 | Robustness test |
| Heavy | 0.5 | Stress test |
| Extreme | 0.8+ | Failure analysis |

---

## Algorithm Details

### Event Generation

```python
# Simplified event generation algorithm
for each pixel (x, y):
    brightness_change = current_frame[y,x] - last_frame[y,x]
    if abs(brightness_change) > threshold:
        emit_event(x, y, timestamp, sign(brightness_change))
```

### Feature Detection

1. **Spatial Clustering**: Group nearby events
2. **Temporal Filtering**: Remove transient noise
3. **Corner Detection**: Identify stable features

### Pose Estimation

```
1. Extract features from event stream
2. Match features across time windows
3. Compute optical flow vectors
4. Estimate rotation from flow center
5. Estimate translation from flow magnitude
6. Apply Kalman filtering for smoothing
```

### Performance Metrics

| Metric | Formula | Ideal Value |
|--------|---------|-------------|
| Position Error | √((gt.x-est.x)² + (gt.y-est.y)² + (gt.z-est.z)²) | < 1m |
| Attitude Error | √((gt.roll-est.roll)² + ...) × 180/π | < 0.5° |
| Drift Rate | position_error / time | < 0.01 m/s |
| Latency | processing_time | < 2ms |

---

## Troubleshooting

### Common Issues

#### Simulation Not Starting
- Check browser console for errors
- Verify API connectivity
- Ensure simulation was created first

#### No Events Visible
- Increase feature density
- Reduce noise level
- Check camera threshold settings

#### High Position Error
- Lower vibration amplitude
- Reduce noise level
- Increase feature density

#### AI Analysis Unavailable
- Check EMERGENT_LLM_KEY configuration
- Verify AI toggle is enabled
- Check network connectivity

### Performance Tips

1. **Faster Simulation**: Reduce feature density
2. **Better Accuracy**: Lower noise, more features
3. **Smooth Visualization**: Limit event display count
4. **Reliable AI**: Ensure stable connection

### Debug Mode

Access detailed logs:
```bash
# Backend logs
tail -f /var/log/supervisor/backend.err.log

# Frontend console
Open browser DevTools → Console
```

---

## References

1. Gallego, G., et al. "Event-based Vision: A Survey" (2020)
2. Scaramuzza, D. "Event Cameras: From Fundamentals to Applications"
3. NASA JPL "Precision Landing Technologies"
4. Prophesee "Metavision SDK Documentation"

---

## Support

For issues and feature requests:
- Check the [Troubleshooting](#troubleshooting) section
- Review API error messages
- Contact research team

---

*LandingOS v1.0 - Event-Driven Visual Navigation Platform*
*Built for precision planetary landing research*
