# LandingOS - Event-Driven Visual Navigation Platform

## Local Development Version

A fully local, self-contained research platform for developing and testing Event-Based Visual Odometry (EVO) algorithms for spacecraft precision landing using neuromorphic event cameras.

![LandingOS Dashboard](docs/dashboard_preview.png)

## Features

### Core Capabilities
- **EVO Simulation Engine** - Realistic neuromorphic event camera simulation
- **SNN Processing** - Spiking Neural Network-inspired corner detection and feature tracking
- **3D Visualization** - Interactive Three.js terrain and trajectory rendering
- **Frame-Based VO Comparison** - Compare event-based vs traditional 30 FPS VO
- **Batch Experiments** - Run and compare multiple simulations with different configs

### Algorithms
- **Harris-SNN Corner Detection** - Bio-inspired corner detection using LIF neurons
- **Event Noise Filter** - Vibration-aware filtering for spacecraft descent scenarios
- **Feature Tracking** - STDP-inspired temporal feature tracking
- **Motion Estimation** - Optical flow and pose estimation from event streams

### Data Management
- **Hardware Import** - Support for CSV, JSON, AEDAT 4.0, Prophesee RAW formats
- **Data Export** - Export events, trajectories, and experiment results
- **Batch Comparison** - Statistical comparison of multiple experiment runs

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 10, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: 3.9 or higher
- **Node.js**: 16.0 or higher
- **RAM**: 4 GB minimum, 8 GB recommended
- **Storage**: 500 MB for installation

### Required Software
1. **Python 3.9+** - https://www.python.org/downloads/
2. **Node.js 16+** - https://nodejs.org/
3. **Git** (optional) - https://git-scm.com/

---

## Quick Start

### Option 1: Using the Startup Script (Recommended)

```bash
# Clone or download the repository
cd /path/to/landingos

# Make the script executable (Linux/Mac)
chmod +x start_local.sh

# Run the startup script
./start_local.sh
```

### Option 2: Manual Startup

**Terminal 1 - Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
yarn install  # or npm install
yarn start    # or npm start
```

### Access the Application
- **Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8001/docs

---

## Project Structure

```
landingos/
├── backend/
│   ├── server.py              # Main FastAPI server
│   ├── evo_engine_enhanced.py # Enhanced EVO simulation engine
│   ├── snn_processor.py       # SNN-based corner detection
│   ├── frame_vo.py            # Frame-based VO for comparison
│   ├── batch_experiments.py   # Batch experiment manager
│   ├── hardware_import.py     # Hardware data parser
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/landingos/
│   │   │   └── LandingOSDashboard.js  # Main dashboard
│   │   └── components/
│   │       ├── Scene3D.js     # 3D visualization
│   │       └── BatchExperiments.js # Batch experiments UI
│   └── package.json           # Node dependencies
├── docs/
│   ├── README.md              # User documentation
│   └── TECHNICAL_REPORT.md    # Technical details
├── start_local.sh             # Local startup script
└── README.md                  # This file
```

---

## Usage Guide

### Running a Simulation

1. Open the dashboard at http://localhost:3000
2. Configure simulation parameters:
   - **Terrain**: Lunar, Mars, or Asteroid
   - **Altitude**: Initial height (100-10000m)
   - **Velocity**: Descent speed (5-200 m/s)
   - **Vibration**: Engine vibration amplitude (0-5°)
   - **Noise Level**: Sensor noise (0-100%)
3. Toggle **SNN Processing** for advanced corner detection
4. Click **Start** to begin the descent simulation

### Viewing 3D Visualization

1. Click the **3D View** tab in the sidebar
2. Use mouse to rotate, zoom, and pan
3. Watch the lander descend with real-time trajectory

### Running Batch Experiments

1. Go to **Batch Experiments** tab
2. Click **New Experiment** or load a preset
3. Configure multiple experiments with different parameters
4. Click **Run All** to execute
5. Click **Compare** to see statistical comparison

### Comparing EVO vs Frame-Based VO

1. Enable **Compare FVO** toggle in the top bar
2. Run a simulation
3. View side-by-side comparison in the results panel

### Importing Hardware Data

1. Click **Import Data** in the sidebar
2. Drag & drop your event camera file
3. Supported formats: CSV, JSON, NumPy, AEDAT 4.0, RAW

### Exporting Results

1. Click **Export Data** in the sidebar
2. Choose export format (CSV or JSON)
3. Export events, trajectories, or full experiments

---

## API Reference

### Simulation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/landingos/simulation/create` | Create new simulation |
| POST | `/api/landingos/simulation/{id}/step` | Advance simulation |
| GET | `/api/landingos/simulation/{id}/state` | Get current state |
| GET | `/api/landingos/simulation/{id}/3d` | Get 3D visualization data |
| POST | `/api/landingos/simulation/{id}/reset` | Reset simulation |

### Batch Experiment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/landingos/experiments/presets` | Get preset configs |
| POST | `/api/landingos/experiments/run` | Run batch experiments |
| POST | `/api/landingos/experiments/compare` | Compare results |
| GET | `/api/landingos/experiments/list` | List all experiments |

### Data Export Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/landingos/export/simulation/{id}/events` | Export events |
| GET | `/api/landingos/export/simulation/{id}/trajectory` | Export trajectory |

---

## Configuration

### Backend Configuration

Edit `backend/.env`:
```env
# MongoDB (optional - uses in-memory if not set)
MONGO_URL=mongodb://localhost:27017

# Server settings
HOST=0.0.0.0
PORT=8001
```

### Frontend Configuration

Edit `frontend/.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## Algorithms

### SNN Corner Detection

The corner detector uses Leaky Integrate-and-Fire (LIF) neurons:

```python
# Neuron model
membrane_potential *= (1 - leak_rate * dt)
membrane_potential += input_current

if membrane_potential >= threshold:
    spike = True
    membrane_potential = 0
```

### Event Noise Filter

Filters vibration-induced noise events:
- Refractory period filtering
- Spatial correlation checking
- Adaptive thresholds based on vibration level

### Feature Tracking

STDP-inspired feature matching:
- Weight updates based on timing
- 20-pixel matching threshold
- 500ms feature timeout

---

## Performance Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Position Error | 3D distance from ground truth | < 1m |
| Attitude Error | Rotation error in degrees | < 0.5° |
| Drift Rate | Error accumulation per second | < 0.01 m/s |
| Latency | Processing time per event batch | < 2ms |

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python3 --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend compilation errors
```bash
# Clear node modules and reinstall
rm -rf node_modules
yarn install
```

### Port already in use
```bash
# Kill process on port 8001
kill $(lsof -t -i:8001)

# Kill process on port 3000
kill $(lsof -t -i:3000)
```

---

## References

1. Gallego, G., et al. "Event-based Vision: A Survey" (2020)
2. Scaramuzza, D. "Event Cameras: From Fundamentals to Applications"
3. NASA JPL "Precision Landing Technologies"
4. Rebecq, H., et al. "EVO: A Geometric Approach to Event-Based 6-DOF Parallel Tracking and Mapping"

---

## License

This project is for research and educational purposes.

---

*LandingOS v2.0 - Local Edition*
*Event-Driven Visual Navigation for Precision Planetary Landing*
