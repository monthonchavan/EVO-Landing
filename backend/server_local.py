"""
LandingOS Local Server
Fully local backend without external API dependencies.
Includes WebSocket support for real-time updates.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import io
import csv
import uuid

from evo_engine_enhanced import EVOSimulatorEnhanced, SimulationConfig, TerrainType
from frame_vo import FrameBasedVO, VOComparator
from batch_experiments import BatchExperimentManager, ExperimentConfig, PRESET_EXPERIMENTS
from hardware_import import EventFileParser, HardwareDataset

app = FastAPI(
    title="LandingOS Local",
    description="Event-Driven Visual Navigation Platform - Local Version",
    version="2.0.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
simulators: Dict[str, EVOSimulatorEnhanced] = {}
comparators: Dict[str, VOComparator] = {}
websocket_connections: Dict[str, List[WebSocket]] = {}
batch_manager = BatchExperimentManager()
file_parser = EventFileParser()
imported_datasets: Dict[str, HardwareDataset] = {}


# ============== Pydantic Models ==============

class SimulationCreateRequest(BaseModel):
    terrain_type: str = "lunar"
    initial_altitude: float = 1000.0
    descent_velocity: float = 50.0
    vibration_amplitude: float = 0.5
    vibration_frequency: float = 10.0
    noise_level: float = 0.1
    feature_density: int = 200
    use_snn_processing: bool = True

class BatchExperimentRequest(BaseModel):
    experiments: List[Dict[str, Any]]

class CustomTerrainRequest(BaseModel):
    simulation_id: str
    features: List[Dict[str, Any]]


# ============== Health Check ==============

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "mode": "local",
        "features": {
            "snn_processing": True,
            "3d_visualization": True,
            "batch_experiments": True,
            "websocket": True,
            "ai_analysis": False  # Removed
        }
    }


# ============== Simulation Endpoints ==============

@app.post("/api/landingos/simulation/create")
async def create_simulation(config: SimulationCreateRequest):
    """Create a new simulation"""
    sim_config = SimulationConfig(
        terrain_type=TerrainType(config.terrain_type),
        initial_altitude=config.initial_altitude,
        descent_velocity=config.descent_velocity,
        vibration_amplitude=config.vibration_amplitude,
        vibration_frequency=config.vibration_frequency,
        noise_level=config.noise_level,
        feature_density=config.feature_density,
        use_snn_processing=config.use_snn_processing
    )
    
    simulator = EVOSimulatorEnhanced(sim_config)
    sim_id = simulator.state.id
    simulators[sim_id] = simulator
    
    return {
        "id": sim_id,
        "status": "created",
        "config": config.dict(),
        "altitude": sim_config.initial_altitude
    }


@app.post("/api/landingos/simulation/{sim_id}/step")
async def step_simulation(sim_id: str, steps: int = Query(default=1, ge=1, le=100)):
    """Advance simulation by steps"""
    if sim_id not in simulators:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    simulator = simulators[sim_id]
    results = []
    
    for _ in range(steps):
        result = simulator.step()
        results.append(result)
        
        # Broadcast to WebSocket clients
        if sim_id in websocket_connections:
            for ws in websocket_connections[sim_id]:
                try:
                    await ws.send_json({"type": "step", "data": result})
                except:
                    pass
        
        if result["status"] == "landed":
            break
    
    return {
        "steps_completed": len(results),
        "final_result": results[-1] if results else None
    }


@app.get("/api/landingos/simulation/{sim_id}/state")
async def get_simulation_state(sim_id: str):
    """Get current simulation state"""
    if sim_id not in simulators:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return simulators[sim_id].get_full_state()


@app.get("/api/landingos/simulation/{sim_id}/3d")
async def get_3d_data(sim_id: str):
    """Get data for 3D visualization"""
    if sim_id not in simulators:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return simulators[sim_id].get_3d_data()


@app.post("/api/landingos/simulation/{sim_id}/reset")
async def reset_simulation(sim_id: str):
    """Reset simulation to initial state"""
    if sim_id not in simulators:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    simulators[sim_id].reset()
    return {"status": "reset", "id": sim_id}


@app.delete("/api/landingos/simulation/{sim_id}")
async def delete_simulation(sim_id: str):
    """Delete a simulation"""
    if sim_id in simulators:
        del simulators[sim_id]
    if sim_id in comparators:
        del comparators[sim_id]
    return {"status": "deleted", "id": sim_id}


# ============== VO Comparison Endpoints ==============

@app.post("/api/landingos/simulation/{sim_id}/enable-comparison")
async def enable_comparison(sim_id: str, frame_rate: int = 30):
    """Enable Frame-Based VO comparison"""
    if sim_id not in simulators:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    comparators[sim_id] = VOComparator(simulators[sim_id], frame_rate)
    return {"status": "comparison_enabled", "frame_rate": frame_rate}


@app.post("/api/landingos/simulation/{sim_id}/step-comparison")
async def step_comparison(sim_id: str, steps: int = Query(default=1)):
    """Step both EVO and FVO simultaneously"""
    if sim_id not in simulators:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if sim_id not in comparators:
        raise HTTPException(status_code=400, detail="Comparison not enabled")
    
    comparator = comparators[sim_id]
    results = []
    
    for _ in range(steps):
        result = comparator.step()
        results.append(result)
        if result["evo"]["status"] == "landed":
            break
    
    return {
        "steps_completed": len(results),
        "final_result": results[-1] if results else None
    }


@app.get("/api/landingos/simulation/{sim_id}/comparison")
async def get_comparison(sim_id: str):
    """Get comparison results"""
    if sim_id not in comparators:
        raise HTTPException(status_code=400, detail="Comparison not enabled")
    
    return {"comparison": comparators[sim_id].get_comparison_summary()}


@app.delete("/api/landingos/simulation/{sim_id}/disable-comparison")
async def disable_comparison(sim_id: str):
    """Disable comparison mode"""
    if sim_id in comparators:
        del comparators[sim_id]
    return {"status": "comparison_disabled"}


# ============== Batch Experiments ==============

@app.get("/api/landingos/experiments/presets")
async def get_experiment_presets():
    """Get available experiment presets"""
    presets = {}
    for name, config in PRESET_EXPERIMENTS.items():
        if isinstance(config, list):
            presets[name] = [{"name": c.name, "config": c.__dict__} for c in config]
        else:
            presets[name] = {"name": config.name, "config": config.__dict__}
    return presets


@app.post("/api/landingos/experiments/run")
async def run_batch_experiments(request: BatchExperimentRequest):
    """Run batch experiments"""
    configs = []
    for exp in request.experiments:
        configs.append(ExperimentConfig(**exp))
    
    results = batch_manager.run_batch(configs)
    
    return {
        "experiments_completed": len(results),
        "results": [
            {
                "id": r.id,
                "name": r.name,
                "final_position_error": r.final_position_error,
                "final_attitude_error": r.final_attitude_error,
                "duration": r.duration
            }
            for r in results
        ]
    }


@app.post("/api/landingos/experiments/run-preset/{preset_name}")
async def run_preset_experiment(preset_name: str):
    """Run a preset experiment"""
    if preset_name not in PRESET_EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    preset = PRESET_EXPERIMENTS[preset_name]
    
    if isinstance(preset, list):
        results = batch_manager.run_batch(preset)
    else:
        exp_id = batch_manager.create_experiment(preset)
        result = batch_manager.run_experiment(exp_id)
        results = [result]
    
    return {
        "preset": preset_name,
        "experiments_completed": len(results),
        "results": [
            {
                "id": r.id,
                "name": r.name,
                "final_position_error": r.final_position_error,
                "final_attitude_error": r.final_attitude_error,
                "average_position_error": r.average_position_error,
                "duration": r.duration
            }
            for r in results
        ]
    }


@app.get("/api/landingos/experiments/list")
async def list_experiments():
    """List all experiments"""
    return batch_manager.list_experiments()


@app.get("/api/landingos/experiments/{exp_id}")
async def get_experiment(exp_id: str):
    """Get experiment details"""
    result = batch_manager.get_experiment_result(exp_id)
    if not result:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return {
        "id": result.id,
        "name": result.name,
        "config": result.config.__dict__,
        "summary": {
            "final_position_error": result.final_position_error,
            "final_attitude_error": result.final_attitude_error,
            "average_position_error": result.average_position_error,
            "max_position_error": result.max_position_error,
            "average_drift_rate": result.average_drift_rate,
            "total_events": result.total_events,
            "duration": result.duration
        },
        "metrics_history": result.metrics_history
    }


@app.post("/api/landingos/experiments/compare")
async def compare_experiments(exp_ids: List[str]):
    """Compare multiple experiments"""
    return batch_manager.compare_experiments(exp_ids)


# ============== Data Export ==============

@app.get("/api/landingos/export/simulation/{sim_id}/events")
async def export_events(sim_id: str, format: str = "csv"):
    """Export event data"""
    if sim_id not in simulators:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    simulator = simulators[sim_id]
    events = simulator.state.events_history
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["x", "y", "timestamp", "polarity"])
        for event in events:
            writer.writerow([event["x"], event["y"], event["timestamp"], event["polarity"]])
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=events_{sim_id}.csv"}
        )
    else:
        return JSONResponse(content={"events": events})


@app.get("/api/landingos/export/simulation/{sim_id}/trajectory")
async def export_trajectory(sim_id: str, format: str = "csv"):
    """Export trajectory data"""
    if sim_id not in simulators:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    simulator = simulators[sim_id]
    
    data = {
        "ground_truth": simulator.state.ground_truth_poses,
        "estimated": simulator.state.estimated_poses,
        "metrics": simulator.state.metrics_history
    }
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["time", "gt_x", "gt_y", "gt_z", "est_x", "est_y", "est_z", "position_error"])
        
        for i, gt in enumerate(data["ground_truth"]):
            est = data["estimated"][i] if i < len(data["estimated"]) else {}
            metrics = data["metrics"][i] if i < len(data["metrics"]) else {}
            writer.writerow([
                gt.get("time", 0),
                gt.get("x", 0), gt.get("y", 0), gt.get("z", 0),
                est.get("x", 0), est.get("y", 0), est.get("z", 0),
                metrics.get("position_error", 0)
            ])
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=trajectory_{sim_id}.csv"}
        )
    else:
        return JSONResponse(content=data)


@app.get("/api/landingos/export/experiment/{exp_id}")
async def export_experiment(exp_id: str, format: str = "json"):
    """Export full experiment data"""
    content = batch_manager.export_results(exp_id, format)
    if not content:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    if format == "csv":
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=experiment_{exp_id}.csv"}
        )
    else:
        return JSONResponse(content=json.loads(content))


# ============== Hardware Import ==============

@app.get("/api/landingos/import/formats")
async def get_supported_formats():
    """Get supported import formats"""
    return {
        "formats": [
            {"extension": ".csv", "name": "CSV", "description": "Comma-separated values with x,y,timestamp,polarity columns"},
            {"extension": ".json", "name": "JSON", "description": "JSON array of event objects"},
            {"extension": ".npy", "name": "NumPy", "description": "NumPy array with event data"},
            {"extension": ".aedat4", "name": "AEDAT 4.0", "description": "Prophesee/iniVation format"},
            {"extension": ".raw", "name": "RAW", "description": "Prophesee EVK raw format"}
        ]
    }


@app.post("/api/landingos/import/upload")
async def upload_hardware_data(file: UploadFile = File(...)):
    """Upload hardware event data"""
    content = await file.read()
    
    try:
        dataset = file_parser.parse_file(content, file.filename)
        dataset_id = str(uuid.uuid4())
        imported_datasets[dataset_id] = dataset
        
        return {
            "id": dataset_id,
            "name": file.filename,
            "format": dataset.format,
            "total_events": dataset.total_events,
            "duration_ms": dataset.duration_ms,
            "resolution": dataset.resolution,
            "sample_events": dataset.events[:10] if dataset.events else []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")


@app.get("/api/landingos/import/datasets")
async def list_imported_datasets():
    """List imported datasets"""
    return [
        {
            "id": did,
            "name": d.name,
            "total_events": d.total_events,
            "duration_ms": d.duration_ms
        }
        for did, d in imported_datasets.items()
    ]


# ============== WebSocket Endpoint ==============

@app.websocket("/api/landingos/ws/simulation/{sim_id}")
async def websocket_endpoint(websocket: WebSocket, sim_id: str):
    """WebSocket for real-time simulation updates"""
    await websocket.accept()
    
    if sim_id not in websocket_connections:
        websocket_connections[sim_id] = []
    websocket_connections[sim_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            command = data.get("command")
            
            if sim_id not in simulators:
                await websocket.send_json({"error": "Simulation not found"})
                continue
            
            simulator = simulators[sim_id]
            
            if command == "step":
                steps = data.get("steps", 1)
                for _ in range(steps):
                    result = simulator.step()
                    await websocket.send_json({"type": "step", "data": result})
                    if result["status"] == "landed":
                        break
                    await asyncio.sleep(0.05)  # 50ms between steps
            
            elif command == "state":
                await websocket.send_json({
                    "type": "state",
                    "data": simulator.get_full_state()
                })
            
            elif command == "3d":
                await websocket.send_json({
                    "type": "3d",
                    "data": simulator.get_3d_data()
                })
            
            elif command == "reset":
                simulator.reset()
                await websocket.send_json({"type": "reset", "status": "ok"})
            
            elif command == "stop":
                break
    
    except WebSocketDisconnect:
        pass
    finally:
        if sim_id in websocket_connections:
            websocket_connections[sim_id].remove(websocket)


# ============== Run Server ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
