"""
Batch Experiment Manager
Run and compare multiple EVO simulations with different configurations.
"""

import uuid
import math
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import json

from evo_engine_enhanced import EVOSimulatorEnhanced, SimulationConfig, TerrainType


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment"""
    name: str
    terrain_type: str = "lunar"
    initial_altitude: float = 1000.0
    descent_velocity: float = 50.0
    vibration_amplitude: float = 0.5
    noise_level: float = 0.1
    feature_density: int = 200
    use_snn_processing: bool = True
    
    def to_sim_config(self) -> SimulationConfig:
        """Convert to SimulationConfig"""
        return SimulationConfig(
            terrain_type=TerrainType(self.terrain_type),
            initial_altitude=self.initial_altitude,
            descent_velocity=self.descent_velocity,
            vibration_amplitude=self.vibration_amplitude,
            noise_level=self.noise_level,
            feature_density=self.feature_density,
            use_snn_processing=self.use_snn_processing
        )


@dataclass
class ExperimentResult:
    """Results from a single experiment run"""
    id: str
    name: str
    config: ExperimentConfig
    # Summary metrics
    final_position_error: float = 0.0
    final_attitude_error: float = 0.0
    average_position_error: float = 0.0
    average_attitude_error: float = 0.0
    max_position_error: float = 0.0
    average_drift_rate: float = 0.0
    average_latency: float = 0.0
    total_events: int = 0
    duration: float = 0.0
    landed_successfully: bool = False
    # Full history
    metrics_history: List[Dict] = field(default_factory=list)
    trajectory_ground_truth: List[Dict] = field(default_factory=list)
    trajectory_estimated: List[Dict] = field(default_factory=list)
    # Timestamps
    started_at: datetime = None
    completed_at: datetime = None


class BatchExperimentManager:
    """Manages batch experiment execution and comparison"""
    
    def __init__(self):
        self.experiments: Dict[str, ExperimentResult] = {}
        self.running_experiments: Dict[str, EVOSimulatorEnhanced] = {}
    
    def create_experiment(self, config: ExperimentConfig) -> str:
        """Create a new experiment"""
        exp_id = str(uuid.uuid4())
        result = ExperimentResult(
            id=exp_id,
            name=config.name,
            config=config,
            started_at=datetime.now(timezone.utc)
        )
        self.experiments[exp_id] = result
        
        # Create simulator
        sim_config = config.to_sim_config()
        self.running_experiments[exp_id] = EVOSimulatorEnhanced(sim_config)
        
        return exp_id
    
    def run_experiment(self, exp_id: str, step_size: float = 0.05) -> ExperimentResult:
        """Run a single experiment to completion"""
        if exp_id not in self.running_experiments:
            raise ValueError(f"Experiment {exp_id} not found")
        
        simulator = self.running_experiments[exp_id]
        result = self.experiments[exp_id]
        
        # Run until landed
        while not simulator.state.is_landed:
            step_result = simulator.step(step_size)
            
            if step_result.get('metrics'):
                result.metrics_history.append({
                    'time': step_result['time'],
                    **step_result['metrics']
                })
        
        # Collect final results
        result.trajectory_ground_truth = simulator.state.ground_truth_poses
        result.trajectory_estimated = simulator.state.estimated_poses
        result.total_events = simulator.state.events_generated
        result.duration = simulator.state.current_time
        result.landed_successfully = simulator.state.is_landed
        result.completed_at = datetime.now(timezone.utc)
        
        # Calculate summary metrics
        if result.metrics_history:
            result.final_position_error = result.metrics_history[-1].get('position_error', 0)
            result.final_attitude_error = result.metrics_history[-1].get('attitude_error', 0)
            result.average_position_error = sum(m.get('position_error', 0) for m in result.metrics_history) / len(result.metrics_history)
            result.average_attitude_error = sum(m.get('attitude_error', 0) for m in result.metrics_history) / len(result.metrics_history)
            result.max_position_error = max(m.get('position_error', 0) for m in result.metrics_history)
            result.average_drift_rate = sum(m.get('drift_rate', 0) for m in result.metrics_history) / len(result.metrics_history)
            result.average_latency = sum(m.get('latency_ms', 0) for m in result.metrics_history) / len(result.metrics_history)
        
        return result
    
    def run_batch(self, configs: List[ExperimentConfig]) -> List[ExperimentResult]:
        """Run multiple experiments"""
        results = []
        for config in configs:
            exp_id = self.create_experiment(config)
            result = self.run_experiment(exp_id)
            results.append(result)
        return results
    
    def compare_experiments(self, exp_ids: List[str]) -> Dict:
        """Compare multiple experiment results"""
        if not exp_ids:
            return {"error": "No experiments to compare"}
        
        results = [self.experiments[eid] for eid in exp_ids if eid in self.experiments]
        
        if not results:
            return {"error": "No valid experiments found"}
        
        comparison = {
            "experiments": [],
            "best_position_accuracy": None,
            "best_attitude_accuracy": None,
            "best_overall": None,
            "rankings": {}
        }
        
        # Collect experiment data
        for result in results:
            exp_data = {
                "id": result.id,
                "name": result.name,
                "final_position_error": result.final_position_error,
                "final_attitude_error": result.final_attitude_error,
                "average_position_error": result.average_position_error,
                "average_attitude_error": result.average_attitude_error,
                "max_position_error": result.max_position_error,
                "average_drift_rate": result.average_drift_rate,
                "average_latency": result.average_latency,
                "total_events": result.total_events,
                "duration": result.duration,
                "config": {
                    "terrain_type": result.config.terrain_type,
                    "use_snn": result.config.use_snn_processing,
                    "vibration": result.config.vibration_amplitude,
                    "noise": result.config.noise_level
                }
            }
            comparison["experiments"].append(exp_data)
        
        # Find best performers
        if results:
            best_pos = min(results, key=lambda r: r.final_position_error)
            best_att = min(results, key=lambda r: r.final_attitude_error)
            
            # Overall score (weighted)
            def overall_score(r):
                return r.final_position_error * 0.5 + r.final_attitude_error * 0.3 + r.average_drift_rate * 100 * 0.2
            
            best_overall = min(results, key=overall_score)
            
            comparison["best_position_accuracy"] = {
                "id": best_pos.id,
                "name": best_pos.name,
                "error": best_pos.final_position_error
            }
            comparison["best_attitude_accuracy"] = {
                "id": best_att.id,
                "name": best_att.name,
                "error": best_att.final_attitude_error
            }
            comparison["best_overall"] = {
                "id": best_overall.id,
                "name": best_overall.name,
                "score": overall_score(best_overall)
            }
            
            # Rankings
            sorted_by_pos = sorted(results, key=lambda r: r.final_position_error)
            comparison["rankings"]["position_error"] = [
                {"rank": i+1, "name": r.name, "value": r.final_position_error}
                for i, r in enumerate(sorted_by_pos)
            ]
            
            sorted_by_att = sorted(results, key=lambda r: r.final_attitude_error)
            comparison["rankings"]["attitude_error"] = [
                {"rank": i+1, "name": r.name, "value": r.final_attitude_error}
                for i, r in enumerate(sorted_by_att)
            ]
        
        return comparison
    
    def get_experiment_result(self, exp_id: str) -> Optional[ExperimentResult]:
        """Get result for a specific experiment"""
        return self.experiments.get(exp_id)
    
    def list_experiments(self) -> List[Dict]:
        """List all experiments"""
        return [
            {
                "id": r.id,
                "name": r.name,
                "status": "completed" if r.completed_at else "running",
                "final_position_error": r.final_position_error,
                "duration": r.duration
            }
            for r in self.experiments.values()
        ]
    
    def export_results(self, exp_id: str, format: str = "json") -> str:
        """Export experiment results"""
        result = self.experiments.get(exp_id)
        if not result:
            return ""
        
        data = {
            "id": result.id,
            "name": result.name,
            "config": {
                "terrain_type": result.config.terrain_type,
                "initial_altitude": result.config.initial_altitude,
                "descent_velocity": result.config.descent_velocity,
                "vibration_amplitude": result.config.vibration_amplitude,
                "noise_level": result.config.noise_level,
                "use_snn_processing": result.config.use_snn_processing
            },
            "summary": {
                "final_position_error": result.final_position_error,
                "final_attitude_error": result.final_attitude_error,
                "average_position_error": result.average_position_error,
                "max_position_error": result.max_position_error,
                "average_drift_rate": result.average_drift_rate,
                "total_events": result.total_events,
                "duration": result.duration
            },
            "metrics_history": result.metrics_history,
            "trajectory": {
                "ground_truth": result.trajectory_ground_truth,
                "estimated": result.trajectory_estimated
            }
        }
        
        if format == "json":
            return json.dumps(data, indent=2, default=str)
        elif format == "csv":
            # CSV format for metrics
            lines = ["time,position_error,attitude_error,drift_rate,latency_ms"]
            for m in result.metrics_history:
                lines.append(f"{m.get('time', 0)},{m.get('position_error', 0)},{m.get('attitude_error', 0)},{m.get('drift_rate', 0)},{m.get('latency_ms', 0)}")
            return "\n".join(lines)
        
        return json.dumps(data, default=str)


# Preset experiment configurations for common scenarios
PRESET_EXPERIMENTS = {
    "lunar_baseline": ExperimentConfig(
        name="Lunar Baseline",
        terrain_type="lunar",
        vibration_amplitude=0.5,
        noise_level=0.1,
        use_snn_processing=True
    ),
    "lunar_high_vibration": ExperimentConfig(
        name="Lunar High Vibration",
        terrain_type="lunar",
        vibration_amplitude=2.0,
        noise_level=0.1,
        use_snn_processing=True
    ),
    "lunar_noisy": ExperimentConfig(
        name="Lunar High Noise",
        terrain_type="lunar",
        vibration_amplitude=0.5,
        noise_level=0.3,
        use_snn_processing=True
    ),
    "mars_baseline": ExperimentConfig(
        name="Mars Baseline",
        terrain_type="mars",
        vibration_amplitude=0.5,
        noise_level=0.1,
        use_snn_processing=True
    ),
    "snn_vs_standard": [
        ExperimentConfig(
            name="SNN Processing",
            terrain_type="lunar",
            vibration_amplitude=1.0,
            use_snn_processing=True
        ),
        ExperimentConfig(
            name="Standard Processing",
            terrain_type="lunar",
            vibration_amplitude=1.0,
            use_snn_processing=False
        )
    ]
}
