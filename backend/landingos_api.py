"""
LandingOS API - Event-Driven Visual Navigation Platform
FastAPI backend for EVO simulation and experiment management
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid
import asyncio
import json

# Import enhanced engine with SNN support
from evo_engine_enhanced import EVOSimulatorEnhanced as EVOSimulator, SimulationConfig, TerrainType
from hardware_import import event_parser, data_exporter, HardwareDataset
from frame_vo import FrameBasedVO, FrameVOConfig, compare_vo_methods
from batch_experiments import BatchExperimentManager, ExperimentConfig, PRESET_EXPERIMENTS

# Initialize batch experiment manager
batch_manager = BatchExperimentManager()

# Router for LandingOS API
landingos_router = APIRouter(prefix="/api/landingos", tags=["LandingOS"])

# In-memory storage for active simulations
active_simulations: Dict[str, EVOSimulator] = {}
# Storage for Frame-Based VO instances (for comparison)
fvo_instances: Dict[str, FrameBasedVO] = {}
# Storage for imported hardware datasets
imported_datasets: Dict[str, Dict] = {}
# WebSocket connections for real-time updates
websocket_connections: List[WebSocket] = []

# ============== Pydantic Models ==============

class SimulationConfigRequest(BaseModel):
    terrain_type: str = "lunar"
    initial_altitude: float = Field(default=1000.0, ge=100, le=10000)
    descent_velocity: float = Field(default=50.0, ge=5, le=200)
    vibration_amplitude: float = Field(default=0.5, ge=0, le=5)
    vibration_frequency: float = Field(default=10.0, ge=1, le=100)
    noise_level: float = Field(default=0.1, ge=0, le=1)
    feature_density: int = Field(default=200, ge=50, le=500)
    use_snn_processing: bool = True  # Enable SNN-based corner detection

class SimulationResponse(BaseModel):
    id: str
    status: str
    time: float
    altitude: float
    events_generated: int
    metrics: Dict

class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    config: SimulationConfigRequest

class ExperimentResponse(BaseModel):
    id: str
    name: str
    description: str
    config: Dict
    status: str
    created_at: str
    results: Optional[Dict] = None

class AIAnalysisRequest(BaseModel):
    simulation_id: Optional[str] = None
    experiment_ids: Optional[List[str]] = None
    analysis_type: str = "simulation"  # simulation, comparison, suggestion
    target_accuracy: Optional[float] = None

# In-memory experiment storage (would be MongoDB in production)
experiments_db: Dict[str, Dict] = {}

# ============== Simulation Endpoints ==============

@landingos_router.post("/simulation/create", response_model=SimulationResponse)
async def create_simulation(config: SimulationConfigRequest):
    """Create a new EVO simulation with specified configuration"""
    try:
        terrain = TerrainType(config.terrain_type)
    except ValueError:
        terrain = TerrainType.LUNAR
    
    sim_config = SimulationConfig(
        terrain_type=terrain,
        initial_altitude=config.initial_altitude,
        descent_velocity=config.descent_velocity,
        vibration_amplitude=config.vibration_amplitude,
        vibration_frequency=config.vibration_frequency,
        noise_level=config.noise_level,
        feature_density=config.feature_density,
        use_snn_processing=config.use_snn_processing
    )
    
    simulator = EVOSimulator(sim_config)
    sim_id = simulator.state.id
    active_simulations[sim_id] = simulator
    
    return SimulationResponse(
        id=sim_id,
        status="created",
        time=0,
        altitude=config.initial_altitude,
        events_generated=0,
        metrics={"position_error": 0, "attitude_error": 0, "drift_rate": 0, "latency_ms": 0}
    )

@landingos_router.post("/simulation/{sim_id}/step")
async def step_simulation(sim_id: str, steps: int = 1):
    """Advance simulation by specified number of steps"""
    if sim_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    simulator = active_simulations[sim_id]
    results = []
    
    for _ in range(min(steps, 50)):  # Limit steps per request
        result = simulator.step()
        results.append(result)
        if result["status"] == "landed":
            break
    
    return {
        "simulation_id": sim_id,
        "steps_executed": len(results),
        "final_result": results[-1] if results else None
    }

@landingos_router.get("/simulation/{sim_id}/state")
async def get_simulation_state(sim_id: str):
    """Get current simulation state"""
    if sim_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return active_simulations[sim_id].get_full_state()

@landingos_router.post("/simulation/{sim_id}/reset")
async def reset_simulation(sim_id: str):
    """Reset simulation to initial state"""
    if sim_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    active_simulations[sim_id].reset()
    return {"status": "reset", "simulation_id": sim_id}

@landingos_router.delete("/simulation/{sim_id}")
async def delete_simulation(sim_id: str):
    """Delete a simulation"""
    if sim_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    del active_simulations[sim_id]
    return {"status": "deleted", "simulation_id": sim_id}

@landingos_router.get("/simulation/{sim_id}/3d")
async def get_3d_data(sim_id: str):
    """Get 3D visualization data for simulation"""
    if sim_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    simulator = active_simulations[sim_id]
    return simulator.get_3d_data()

@landingos_router.get("/simulations")
async def list_simulations():
    """List all active simulations"""
    return {
        "simulations": [
            {
                "id": sim_id,
                "status": sim.state.is_running,
                "time": sim.state.current_time,
                "altitude": sim.state.current_pose.z
            }
            for sim_id, sim in active_simulations.items()
        ]
    }

# ============== Experiment Endpoints ==============

@landingos_router.post("/experiment/create", response_model=ExperimentResponse)
async def create_experiment(experiment: ExperimentCreate):
    """Create a new experiment record"""
    exp_id = str(uuid.uuid4())[:8]
    
    exp_data = {
        "id": exp_id,
        "name": experiment.name,
        "description": experiment.description or "",
        "config": experiment.config.model_dump(),
        "status": "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "results": None
    }
    
    experiments_db[exp_id] = exp_data
    return ExperimentResponse(**exp_data)

@landingos_router.post("/experiment/{exp_id}/run")
async def run_experiment(exp_id: str, total_steps: int = 200):
    """Run an experiment to completion"""
    if exp_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    exp = experiments_db[exp_id]
    config = exp["config"]
    
    # Create and run simulation
    try:
        terrain = TerrainType(config.get("terrain_type", "lunar"))
    except ValueError:
        terrain = TerrainType.LUNAR
    
    sim_config = SimulationConfig(
        terrain_type=terrain,
        initial_altitude=config.get("initial_altitude", 1000),
        descent_velocity=config.get("descent_velocity", 50),
        vibration_amplitude=config.get("vibration_amplitude", 0.5),
        vibration_frequency=config.get("vibration_frequency", 10),
        noise_level=config.get("noise_level", 0.1),
        feature_density=config.get("feature_density", 200)
    )
    
    simulator = EVOSimulator(sim_config)
    
    # Run simulation
    results = []
    for _ in range(total_steps):
        result = simulator.step()
        results.append(result)
        if result["status"] == "landed":
            break
    
    final_state = simulator.get_full_state()
    
    # Update experiment with results
    exp["status"] = "completed"
    exp["results"] = {
        "final_state": final_state,
        "steps_executed": len(results),
        "final_metrics": results[-1]["metrics"] if results else {},
        "trajectory_summary": {
            "start_altitude": config.get("initial_altitude", 1000),
            "end_altitude": final_state["altitude"],
            "total_events": final_state["events_generated"],
            "duration": final_state["time"]
        }
    }
    
    experiments_db[exp_id] = exp
    return exp

@landingos_router.get("/experiment/{exp_id}", response_model=ExperimentResponse)
async def get_experiment(exp_id: str):
    """Get experiment details"""
    if exp_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return ExperimentResponse(**experiments_db[exp_id])

@landingos_router.get("/experiments")
async def list_experiments():
    """List all experiments"""
    return {
        "experiments": list(experiments_db.values())
    }

@landingos_router.delete("/experiment/{exp_id}")
async def delete_experiment(exp_id: str):
    """Delete an experiment"""
    if exp_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    del experiments_db[exp_id]
    return {"status": "deleted", "experiment_id": exp_id}

# ============== AI Analysis Endpoints ==============

@landingos_router.post("/ai/analyze")
async def ai_analysis(request: AIAnalysisRequest):
    """Perform AI-powered analysis on simulation/experiment results"""
    
    if request.analysis_type == "simulation":
        # Analyze a specific simulation
        if not request.simulation_id:
            raise HTTPException(status_code=400, detail="simulation_id required for simulation analysis")
        
        if request.simulation_id not in active_simulations:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        sim_data = active_simulations[request.simulation_id].get_full_state()
        sim_data["metrics"] = active_simulations[request.simulation_id]._calculate_metrics()
        
        return await ai_analyzer.analyze_simulation(sim_data)
    
    elif request.analysis_type == "comparison":
        # Compare multiple experiments
        if not request.experiment_ids or len(request.experiment_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 experiment_ids required for comparison")
        
        experiments = []
        for exp_id in request.experiment_ids:
            if exp_id in experiments_db:
                exp = experiments_db[exp_id]
                if exp.get("results"):
                    experiments.append({
                        "config": exp["config"],
                        "metrics": exp["results"].get("final_metrics", {})
                    })
        
        return await ai_analyzer.compare_experiments(experiments)
    
    elif request.analysis_type == "suggestion":
        # Suggest parameters for target accuracy
        if request.target_accuracy is None:
            raise HTTPException(status_code=400, detail="target_accuracy required for suggestion analysis")
        
        # Get current config from most recent experiment or use defaults
        current_config = {}
        if experiments_db:
            latest_exp = max(experiments_db.values(), key=lambda x: x["created_at"])
            current_config = latest_exp["config"]
        else:
            current_config = {
                "terrain_type": "lunar",
                "descent_velocity": 50,
                "vibration_amplitude": 0.5,
                "noise_level": 0.1
            }
        
        return await ai_analyzer.suggest_parameters(current_config, request.target_accuracy)
    
    else:
        raise HTTPException(status_code=400, detail="Invalid analysis_type")

@landingos_router.get("/ai/status")
async def ai_status():
    """Check if AI analysis is available"""
    return {
        "enabled": ai_analyzer.enabled,
        "message": "AI analysis is ready" if ai_analyzer.enabled else "AI analysis disabled - set EMERGENT_LLM_KEY"
    }

# ============== Terrain Data Endpoints ==============

@landingos_router.get("/terrain/types")
async def get_terrain_types():
    """Get available terrain types"""
    return {
        "types": [
            {"id": "lunar", "name": "Lunar Surface", "description": "Moon-like terrain with many craters"},
            {"id": "mars", "name": "Martian Surface", "description": "Mars-like terrain with rocks and small craters"},
            {"id": "custom", "name": "Custom", "description": "Customizable terrain parameters"}
        ]
    }

@landingos_router.get("/terrain/{terrain_type}/features")
async def get_terrain_features(terrain_type: str, count: int = 100):
    """Get sample terrain features for visualization"""
    from evo_engine import TerrainGenerator
    
    try:
        terrain = TerrainType(terrain_type)
    except ValueError:
        terrain = TerrainType.LUNAR
    
    generator = TerrainGenerator(terrain, count)
    return {
        "terrain_type": terrain_type,
        "features": generator.features
    }


# ============== Hardware Data Import Endpoints ==============

@landingos_router.get("/import/formats")
async def get_supported_formats():
    """Get list of supported file formats for import"""
    return {
        "formats": [
            {"id": "csv", "name": "CSV", "description": "Comma-separated values (x, y, timestamp, polarity)", "extensions": [".csv"]},
            {"id": "json", "name": "JSON", "description": "JSON event array", "extensions": [".json"]},
            {"id": "txt", "name": "Text", "description": "Space/tab separated values", "extensions": [".txt"]},
            {"id": "npy", "name": "NumPy", "description": "NumPy array file", "extensions": [".npy"]},
            {"id": "aedat4", "name": "AEDAT 4.0", "description": "Prophesee/iniVation format", "extensions": [".aedat4", ".aedat"]},
            {"id": "raw", "name": "RAW", "description": "Prophesee EVK raw format", "extensions": [".raw"]}
        ],
        "max_file_size_mb": 100,
        "example_csv": "x,y,timestamp,polarity\n320,240,1000,1\n321,241,1001,-1"
    }

@landingos_router.post("/import/upload")
async def upload_hardware_data(
    file: UploadFile = File(...),
    format_hint: Optional[str] = None
):
    """Upload and import event camera data from hardware"""
    try:
        # Read file content
        content = await file.read()
        
        # Check file size (100MB limit)
        if len(content) > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum 100MB allowed.")
        
        # Parse the file
        dataset = event_parser.parse_file(content, file.filename, format_hint)
        
        # Store in memory
        dataset_dict = {
            "id": dataset.id,
            "name": dataset.name,
            "format": dataset.format,
            "resolution": dataset.resolution,
            "events": dataset.events[:10000],  # Limit stored events
            "total_events": dataset.total_events,
            "duration_us": dataset.duration_us,
            "metadata": dataset.metadata,
            "imported_at": dataset.imported_at.isoformat()
        }
        imported_datasets[dataset.id] = dataset_dict
        
        return {
            "success": True,
            "dataset_id": dataset.id,
            "name": dataset.name,
            "format": dataset.format,
            "resolution": dataset.resolution,
            "total_events": dataset.total_events,
            "duration_ms": dataset.duration_us / 1000,
            "sample_events": dataset.events[:10]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@landingos_router.get("/import/datasets")
async def list_imported_datasets():
    """List all imported hardware datasets"""
    return {
        "datasets": [
            {
                "id": d["id"],
                "name": d["name"],
                "format": d["format"],
                "total_events": d["total_events"],
                "duration_ms": d["duration_us"] / 1000,
                "imported_at": d["imported_at"]
            }
            for d in imported_datasets.values()
        ]
    }

@landingos_router.get("/import/dataset/{dataset_id}")
async def get_imported_dataset(dataset_id: str, offset: int = 0, limit: int = 1000):
    """Get events from an imported dataset"""
    if dataset_id not in imported_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    dataset = imported_datasets[dataset_id]
    events = dataset["events"][offset:offset + limit]
    
    return {
        "id": dataset["id"],
        "name": dataset["name"],
        "total_events": dataset["total_events"],
        "offset": offset,
        "limit": limit,
        "events": events
    }

@landingos_router.delete("/import/dataset/{dataset_id}")
async def delete_imported_dataset(dataset_id: str):
    """Delete an imported dataset"""
    if dataset_id not in imported_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    del imported_datasets[dataset_id]
    return {"success": True, "deleted": dataset_id}

# ============== Data Export Endpoints ==============

@landingos_router.get("/export/simulation/{sim_id}/events")
async def export_simulation_events(sim_id: str, format: str = "csv"):
    """Export events from a simulation"""
    if sim_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = active_simulations[sim_id]
    state = sim.get_full_state()
    events = state.get("events_history", [])
    
    if format == "csv":
        content = data_exporter.export_events_csv(events)
        media_type = "text/csv"
        filename = f"events_{sim_id}.csv"
    else:
        content = data_exporter.export_events_json(events, {
            "simulation_id": sim_id,
            "total_events": state.get("events_generated", 0),
            "duration": state.get("time", 0)
        })
        media_type = "application/json"
        filename = f"events_{sim_id}.json"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@landingos_router.get("/export/simulation/{sim_id}/trajectory")
async def export_simulation_trajectory(sim_id: str, format: str = "csv"):
    """Export trajectory from a simulation"""
    if sim_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim = active_simulations[sim_id]
    state = sim.get_full_state()
    
    if format == "csv":
        content = data_exporter.export_trajectory_csv(state.get("ground_truth_poses", []))
        media_type = "text/csv"
        filename = f"trajectory_{sim_id}.csv"
    else:
        content = json.dumps({
            "simulation_id": sim_id,
            "ground_truth": state.get("ground_truth_poses", []),
            "estimated": state.get("estimated_poses", [])
        }, indent=2)
        media_type = "application/json"
        filename = f"trajectory_{sim_id}.json"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@landingos_router.get("/export/experiment/{exp_id}")
async def export_experiment(exp_id: str):
    """Export complete experiment data"""
    if exp_id not in experiments_db:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    exp = experiments_db[exp_id]
    content = data_exporter.export_full_experiment(exp)
    
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=experiment_{exp_id}.json"}
    )

# ============== WebSocket for Real-time Updates ==============

@landingos_router.websocket("/ws/simulation/{sim_id}")
async def websocket_simulation(websocket: WebSocket, sim_id: str):
    """WebSocket endpoint for real-time simulation updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        if sim_id not in active_simulations:
            await websocket.send_json({"error": "Simulation not found"})
            await websocket.close()
            return
        
        sim = active_simulations[sim_id]
        
        while True:
            # Wait for command from client
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "step":
                steps = data.get("steps", 1)
                results = []
                for _ in range(min(steps, 10)):
                    result = sim.step()
                    results.append(result)
                    
                    # Send each step result immediately
                    await websocket.send_json({
                        "type": "step",
                        "data": result
                    })
                    
                    if result["status"] == "landed":
                        await websocket.send_json({
                            "type": "landed",
                            "data": sim.get_full_state()
                        })
                        break
                    
                    await asyncio.sleep(0.05)  # Small delay between steps
            
            elif command == "state":
                await websocket.send_json({
                    "type": "state",
                    "data": sim.get_full_state()
                })
            
            elif command == "reset":
                sim.reset()
                await websocket.send_json({
                    "type": "reset",
                    "data": {"status": "reset"}
                })
            
            elif command == "stop":
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


# ============== VO Comparison Endpoints ==============

class ComparisonConfigRequest(BaseModel):
    frame_rate: int = Field(default=30, ge=10, le=120)
    enable_fvo: bool = True

@landingos_router.post("/simulation/{sim_id}/enable-comparison")
async def enable_vo_comparison(sim_id: str, config: ComparisonConfigRequest = None):
    """Enable Frame-Based VO comparison for a simulation"""
    if sim_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    cfg = config or ComparisonConfigRequest()
    fvo_config = FrameVOConfig(frame_rate=cfg.frame_rate)
    fvo_instances[sim_id] = FrameBasedVO(fvo_config)
    
    return {
        "simulation_id": sim_id,
        "comparison_enabled": True,
        "frame_rate": cfg.frame_rate
    }

@landingos_router.post("/simulation/{sim_id}/step-comparison")
async def step_simulation_with_comparison(sim_id: str, steps: int = 1):
    """Advance simulation with both EVO and FVO running"""
    if sim_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    simulator = active_simulations[sim_id]
    fvo = fvo_instances.get(sim_id)
    
    results = []
    
    for _ in range(min(steps, 50)):
        # Run EVO step
        evo_result = simulator.step()
        
        result = {
            "evo": evo_result,
            "fvo": None
        }
        
        # Run FVO step if enabled
        if fvo and evo_result.get("ground_truth"):
            gt = evo_result["ground_truth"]
            config = simulator.config
            fvo_result = fvo.process_frame(
                evo_result["time"],
                gt,
                config.descent_velocity,
                config.vibration_amplitude
            )
            result["fvo"] = fvo_result
        
        results.append(result)
        
        if evo_result.get("status") == "landed":
            break
    
    return {
        "simulation_id": sim_id,
        "steps_executed": len(results),
        "final_result": results[-1] if results else None,
        "comparison_enabled": sim_id in fvo_instances
    }

@landingos_router.get("/simulation/{sim_id}/comparison")
async def get_vo_comparison(sim_id: str):
    """Get comparison results between EVO and FVO"""
    if sim_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if sim_id not in fvo_instances:
        raise HTTPException(status_code=400, detail="Comparison not enabled. Call /enable-comparison first.")
    
    simulator = active_simulations[sim_id]
    fvo = fvo_instances[sim_id]
    
    # Get EVO data
    evo_state = simulator.get_full_state()
    evo_data = {
        "metrics_history": evo_state.get("metrics_history", []),
        "pose_history": evo_state.get("estimated_poses", [])
    }
    
    # Get FVO data
    fvo_data = fvo.get_comparison_data()
    
    # Compare
    comparison = compare_vo_methods(evo_data, fvo_data)
    
    return {
        "simulation_id": sim_id,
        "comparison": comparison,
        "evo_trajectory": evo_state.get("estimated_poses", [])[-50:],
        "fvo_trajectory": fvo_data.get("pose_history", [])[-50:],
        "ground_truth": evo_state.get("ground_truth_poses", [])[-50:]
    }

@landingos_router.post("/simulation/{sim_id}/reset-comparison")
async def reset_comparison(sim_id: str):
    """Reset FVO for a simulation"""
    if sim_id in fvo_instances:
        fvo_instances[sim_id].reset()
        return {"status": "reset", "simulation_id": sim_id}
    raise HTTPException(status_code=404, detail="Comparison not enabled for this simulation")

@landingos_router.delete("/simulation/{sim_id}/disable-comparison")
async def disable_comparison(sim_id: str):
    """Disable FVO comparison for a simulation"""
    if sim_id in fvo_instances:
        del fvo_instances[sim_id]
        return {"status": "disabled", "simulation_id": sim_id}
    raise HTTPException(status_code=404, detail="Comparison not enabled for this simulation")
