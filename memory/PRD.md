# LandingOS - Event-Driven Visual Navigation Platform

## Original Problem Statement
Build an integrated platform for "Event-Driven Visual Navigation for Precision Planetary Landing in Extreme Environments" - a research tool for developing and testing Event-Based Visual Odometry (EVO) algorithms using neuromorphic event cameras for spacecraft landing.

## User Requirements
- Light scientific/academic theme
- AI integration with toggle to enable/disable
- Focus on both simulation/visualization AND EVO accuracy
- Synthetic data generation pipeline
- Event-Based Visual Odometry algorithm implementation
- Research documentation and experiment management
- **Hardware data import from physical event cameras**
- **Comprehensive project documentation**

## Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        LandingOS Platform                        │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React)          │  Backend (FastAPI)                 │
│  - Bento Grid Dashboard    │  - EVO Simulation Engine           │
│  - Event Canvas (2D)       │  - AI Analysis (GPT-4o)            │
│  - Performance Charts      │  - Hardware Import Parser          │
│  - Import/Export UI        │  - Data Export Module              │
│  - AI Toggle Control       │  - WebSocket Real-time             │
└─────────────────────────────────────────────────────────────────┘
```

## What's Been Implemented (Jan 2026)

### Core Features ✅
- [x] EVO Simulation Engine with terrain generation (Lunar/Mars)
- [x] Event camera simulator (neuromorphic events)
- [x] Visual odometry algorithm (feature detection, pose estimation)
- [x] Performance metrics (Position Error, Attitude Error, Drift Rate, Latency)
- [x] Real-time visualization with charts

### AI Analysis ✅
- [x] GPT-4o powered experiment analysis
- [x] Toggle switch to enable/disable AI
- [x] Performance assessment and optimization suggestions
- [x] Experiment comparison capabilities

### Hardware Integration ✅ (NEW)
- [x] CSV import (x, y, timestamp, polarity)
- [x] JSON import (event arrays)
- [x] NumPy (.npy) import
- [x] AEDAT 4.0 format (Prophesee/iniVation)
- [x] Prophesee RAW format
- [x] Text file import (space/tab separated)
- [x] Drag & drop upload interface
- [x] Dataset management

### Data Export ✅ (NEW)
- [x] Events export (CSV/JSON)
- [x] Trajectory export (CSV/JSON)
- [x] Experiment data export
- [x] Download functionality

### Real-time Features ✅ (NEW)
- [x] WebSocket endpoint for streaming updates
- [x] Real-time chart updates
- [x] Live pose estimation comparison

### Documentation ✅ (NEW)
- [x] Comprehensive README at /app/docs/README.md
- [x] API reference with examples
- [x] Hardware integration guide
- [x] Algorithm documentation
- [x] Configuration guide
- [x] Troubleshooting section

## API Endpoints

### Simulation
- `POST /api/landingos/simulation/create` - Create simulation
- `POST /api/landingos/simulation/{id}/step` - Advance simulation
- `GET /api/landingos/simulation/{id}/state` - Get state
- `POST /api/landingos/simulation/{id}/reset` - Reset
- `DELETE /api/landingos/simulation/{id}` - Delete

### Hardware Import
- `GET /api/landingos/import/formats` - List supported formats
- `POST /api/landingos/import/upload` - Upload hardware data
- `GET /api/landingos/import/datasets` - List datasets
- `GET /api/landingos/import/dataset/{id}` - Get dataset events
- `DELETE /api/landingos/import/dataset/{id}` - Delete dataset

### Data Export
- `GET /api/landingos/export/simulation/{id}/events` - Export events
- `GET /api/landingos/export/simulation/{id}/trajectory` - Export trajectory
- `GET /api/landingos/export/experiment/{id}` - Export experiment

### AI Analysis
- `POST /api/landingos/ai/analyze` - Run AI analysis
- `GET /api/landingos/ai/status` - Check AI availability

### WebSocket
- `WS /api/landingos/ws/simulation/{id}` - Real-time updates

## Test Results (Iteration 4)
- **Backend**: 100% (12/12 tests passed)
- **Frontend**: 95% (19/20 tests passed - 1 minor UI issue)
- **Overall**: All core features working

## Supported Hardware Formats

| Format | Extension | Manufacturer |
|--------|-----------|--------------|
| CSV | .csv | Universal |
| JSON | .json | Custom |
| NumPy | .npy | Python |
| AEDAT 4.0 | .aedat4, .aedat | Prophesee, iniVation |
| RAW | .raw | Prophesee EVK |
| Text | .txt | Legacy |

## File Structure
```
/app/
├── backend/
│   ├── server.py           # Main FastAPI app
│   ├── landingos_api.py    # LandingOS routes
│   ├── evo_engine.py       # Simulation engine
│   ├── ai_analysis.py      # GPT-4o integration
│   └── hardware_import.py  # Data import/export
├── frontend/src/
│   ├── pages/landingos/
│   │   └── LandingOSDashboard.js
│   ├── App.js
│   └── index.css
├── docs/
│   └── README.md           # Full documentation
└── memory/
    └── PRD.md              # This file
```

## Next Steps / Backlog

### P1 (High Priority)
- [ ] 3D visualization with Three.js/React Three Fiber
- [ ] Multiple camera support in simulation
- [ ] Experiment batch comparison
- [ ] Report generation (PDF export)

### P2 (Medium Priority)
- [ ] Hardware-in-the-Loop (HIL) simulation
- [ ] Spiking Neural Network (SNN) feature detection
- [ ] Custom terrain generation tool
- [ ] Real hardware integration testing

### Future Enhancements
- [ ] VR/AR visualization mode
- [ ] Team collaboration features
- [ ] Auto-generated research papers
- [ ] Cloud deployment for distributed testing
