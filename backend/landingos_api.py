"""
LandingOS API - Event-Driven Visual Navigation Platform
FastAPI backend for EVO simulation and experiment management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid

from evo_engine import EVOSimulator, SimulationConfig, TerrainType
from ai_analysis import ai_analyzer

# Router for LandingOS API
landingos_router = APIRouter(prefix="/api/landingos", tags=["LandingOS"])

# In-memory storage for active simulations
active_simulations: Dict[str, EVOSimulator] = {}

# ============== Pydantic Models ==============

class SimulationConfigRequest(BaseModel):
    terrain_type: str = "lunar"
    initial_altitude: float = Field(default=1000.0, ge=100, le=10000)
    descent_velocity: float = Field(default=50.0, ge=5, le=200)
    vibration_amplitude: float = Field(default=0.5, ge=0, le=5)
    vibration_frequency: float = Field(default=10.0, ge=1, le=100)
    noise_level: float = Field(default=0.1, ge=0, le=1)
    feature_density: int = Field(default=200, ge=50, le=500)

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
        feature_density=config.feature_density
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
