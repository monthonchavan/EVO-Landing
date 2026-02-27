"""
AI-Powered Analysis Module for EVO Experiments
Uses LLM to provide insights on simulation results and pose estimation accuracy.
"""

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Import emergent integrations
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    EMERGENT_AVAILABLE = True
except ImportError:
    logger.warning("emergentintegrations not available, AI analysis will be disabled")
    EMERGENT_AVAILABLE = False

class AIAnalyzer:
    """AI-powered analysis for EVO experiment results"""
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('EMERGENT_API_KEY')
        self.enabled = EMERGENT_AVAILABLE and bool(self.api_key)
        
        if self.enabled:
            self.chat = LlmChat(
                api_key=self.api_key,
                session_id="evo-analysis",
                system_message="""You are an expert aerospace engineer and computer vision scientist 
specializing in visual odometry for spacecraft navigation. You analyze experiment results from 
Event-Based Visual Odometry (EVO) systems designed for planetary landing.

Your role is to:
1. Identify anomalies and potential issues in pose estimation
2. Suggest parameter optimizations based on results
3. Compare performance against expected benchmarks
4. Provide actionable recommendations for improving accuracy

Be concise, technical, and data-driven in your analysis. Use metric units.
Format your responses with clear sections using markdown."""
            ).with_model("openai", "gpt-4o")
    
    async def analyze_simulation(self, simulation_data: Dict) -> Dict:
        """Analyze a completed simulation and provide insights"""
        if not self.enabled:
            return {
                "enabled": False,
                "message": "AI analysis is disabled. Enable by providing EMERGENT_LLM_KEY."
            }
        
        try:
            # Prepare analysis prompt
            metrics = simulation_data.get("metrics", {})
            config = simulation_data.get("config", {})
            
            prompt = f"""Analyze this EVO simulation result:

**Configuration:**
- Terrain: {config.get('terrain_type', 'unknown')}
- Initial Altitude: {config.get('initial_altitude', 0)}m
- Descent Velocity: {config.get('descent_velocity', 0)} m/s
- Vibration Amplitude: {config.get('vibration_amplitude', 0)}°
- Noise Level: {config.get('noise_level', 0)}

**Final Metrics:**
- Position Error: {metrics.get('position_error', 0)}m
- Attitude Error: {metrics.get('attitude_error', 0)}°
- Drift Rate: {metrics.get('drift_rate', 0)} m/s
- Processing Latency: {metrics.get('latency_ms', 0)}ms

**Simulation Stats:**
- Duration: {simulation_data.get('time', 0):.1f}s
- Total Events Generated: {simulation_data.get('events_generated', 0)}
- Final Altitude: {simulation_data.get('altitude', 0):.1f}m

Provide:
1. Performance Assessment (1-2 sentences)
2. Key Issues Identified (bullet points)
3. Optimization Recommendations (bullet points)
4. Risk Assessment for Landing (1 sentence)"""
            
            message = UserMessage(text=prompt)
            response = await self.chat.send_message(message)
            
            return {
                "enabled": True,
                "analysis": response,
                "simulation_id": simulation_data.get("id"),
                "analyzed_at": simulation_data.get("time")
            }
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {
                "enabled": True,
                "error": str(e),
                "message": "Failed to generate AI analysis"
            }
    
    async def compare_experiments(self, experiments: List[Dict]) -> Dict:
        """Compare multiple experiments and identify trends"""
        if not self.enabled:
            return {"enabled": False, "message": "AI analysis disabled"}
        
        if len(experiments) < 2:
            return {"enabled": True, "message": "Need at least 2 experiments to compare"}
        
        try:
            # Build comparison prompt
            exp_summaries = []
            for i, exp in enumerate(experiments[:5]):  # Limit to 5
                metrics = exp.get("metrics", {})
                config = exp.get("config", {})
                exp_summaries.append(
                    f"Exp {i+1}: Terrain={config.get('terrain_type')}, "
                    f"Noise={config.get('noise_level')}, "
                    f"PosErr={metrics.get('position_error', 0):.2f}m, "
                    f"AttErr={metrics.get('attitude_error', 0):.2f}°"
                )
            
            prompt = f"""Compare these EVO experiments:

{chr(10).join(exp_summaries)}

Provide:
1. Best Performing Configuration
2. Worst Performing Configuration
3. Key Trends Observed
4. Recommended Next Experiment"""
            
            message = UserMessage(text=prompt)
            response = await self.chat.send_message(message)
            
            return {
                "enabled": True,
                "comparison": response,
                "experiments_compared": len(experiments)
            }
            
        except Exception as e:
            logger.error(f"AI comparison error: {e}")
            return {"enabled": True, "error": str(e)}
    
    async def suggest_parameters(self, current_config: Dict, target_accuracy: float) -> Dict:
        """Suggest parameter adjustments to achieve target accuracy"""
        if not self.enabled:
            return {"enabled": False, "message": "AI analysis disabled"}
        
        try:
            prompt = f"""Current EVO Configuration:
- Terrain: {current_config.get('terrain_type', 'lunar')}
- Descent Velocity: {current_config.get('descent_velocity', 50)} m/s
- Vibration: {current_config.get('vibration_amplitude', 0.5)}°
- Noise Level: {current_config.get('noise_level', 0.1)}

Target Position Accuracy: {target_accuracy}m

Suggest specific parameter changes to achieve target accuracy.
Consider physical constraints and computational limits."""
            
            message = UserMessage(text=prompt)
            response = await self.chat.send_message(message)
            
            return {
                "enabled": True,
                "suggestions": response,
                "target_accuracy": target_accuracy
            }
            
        except Exception as e:
            logger.error(f"AI suggestion error: {e}")
            return {"enabled": True, "error": str(e)}

# Global instance
ai_analyzer = AIAnalyzer()
