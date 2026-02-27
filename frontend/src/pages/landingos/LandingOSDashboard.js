import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import * as THREE from 'three';
import {
  Play, Pause, RotateCcw, Settings, Cpu, Activity, Gauge, 
  Mountain, Zap, Brain, ChevronRight, AlertTriangle, CheckCircle,
  BarChart3, Clock, Target, Layers
} from 'lucide-react';
import { LineChart, Line as RechartsLine, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Terrain mesh component for 3D view
function TerrainMesh({ terrainType }) {
  const color = terrainType === 'mars' ? '#8B4513' : '#4A4A4A';
  
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -50, 0]}>
      <planeGeometry args={[200, 200, 32, 32]} />
      <meshStandardMaterial color={color} roughness={0.9} wireframe={false} />
    </mesh>
  );
}

// Lander visualization
function Lander({ pose }) {
  const { x = 0, y = 0, z = 100 } = pose || {};
  const scale = Math.max(0.5, Math.min(2, z / 200));
  
  return (
    <group position={[x * 0.1, z * 0.1, y * 0.1]}>
      {/* Lander body */}
      <mesh>
        <coneGeometry args={[2 * scale, 4 * scale, 6]} />
        <meshStandardMaterial color="#E2E8F0" metalness={0.8} roughness={0.2} />
      </mesh>
      {/* Legs */}
      {[0, 120, 240].map((angle, i) => (
        <mesh key={i} position={[
          Math.cos(angle * Math.PI / 180) * 1.5 * scale,
          -2 * scale,
          Math.sin(angle * Math.PI / 180) * 1.5 * scale
        ]}>
          <cylinderGeometry args={[0.1 * scale, 0.1 * scale, 2 * scale]} />
          <meshStandardMaterial color="#94A3B8" />
        </mesh>
      ))}
      {/* Thrust indicator */}
      <pointLight position={[0, -3 * scale, 0]} color="#FF5F00" intensity={2} distance={10} />
    </group>
  );
}

// Event cloud visualization
function EventCloud({ events }) {
  if (!events || events.length === 0) return null;
  
  return (
    <group>
      {events.slice(0, 200).map((event, i) => (
        <mesh key={i} position={[
          (event.x - 320) * 0.05,
          20 + (i % 10),
          (event.y - 240) * 0.05
        ]}>
          <sphereGeometry args={[0.15, 4, 4]} />
          <meshBasicMaterial color={event.polarity > 0 ? '#0055FF' : '#FF5F00'} />
        </mesh>
      ))}
    </group>
  );
}

// Trajectory visualization using a mesh-based approach
function TrajectoryPath({ poses, color = '#0055FF' }) {
  if (!poses || poses.length < 2) return null;
  
  return (
    <group>
      {poses.map((pose, i) => (
        <mesh key={i} position={[pose.x * 0.1, pose.z * 0.1, pose.y * 0.1]}>
          <sphereGeometry args={[0.3, 8, 8]} />
          <meshBasicMaterial color={color} />
        </mesh>
      ))}
    </group>
  );
}

// Main Dashboard Component
export default function LandingOSDashboard() {
  const [simulationId, setSimulationId] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [simData, setSimData] = useState(null);
  const [events, setEvents] = useState([]);
  const [groundTruth, setGroundTruth] = useState([]);
  const [estimated, setEstimated] = useState([]);
  const [metricsHistory, setMetricsHistory] = useState([]);
  const [aiEnabled, setAiEnabled] = useState(true);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiAvailable, setAiAvailable] = useState(true);
  const intervalRef = useRef(null);
  
  // Configuration state
  const [config, setConfig] = useState({
    terrain_type: 'lunar',
    initial_altitude: 1000,
    descent_velocity: 50,
    vibration_amplitude: 0.5,
    noise_level: 0.1,
    feature_density: 200
  });
  
  // Check AI availability
  useEffect(() => {
    axios.get(`${API_URL}/api/landingos/ai/status`)
      .then(res => setAiAvailable(res.data.enabled))
      .catch(() => setAiAvailable(false));
  }, []);
  
  // Create simulation
  const createSimulation = useCallback(async () => {
    try {
      const res = await axios.post(`${API_URL}/api/landingos/simulation/create`, config);
      setSimulationId(res.data.id);
      setSimData(res.data);
      setEvents([]);
      setGroundTruth([]);
      setEstimated([]);
      setMetricsHistory([]);
      setAiAnalysis(null);
    } catch (err) {
      console.error('Failed to create simulation:', err);
    }
  }, [config]);
  
  // Step simulation
  const stepSimulation = useCallback(async () => {
    if (!simulationId) return;
    
    try {
      const res = await axios.post(`${API_URL}/api/landingos/simulation/${simulationId}/step`, null, {
        params: { steps: 5 }
      });
      
      const result = res.data.final_result;
      if (result) {
        setSimData(result);
        
        if (result.events) {
          setEvents(result.events);
        }
        
        if (result.ground_truth) {
          setGroundTruth(prev => [...prev.slice(-100), result.ground_truth]);
        }
        
        if (result.estimated) {
          setEstimated(prev => [...prev.slice(-100), result.estimated]);
        }
        
        if (result.metrics) {
          setMetricsHistory(prev => [...prev.slice(-50), {
            time: result.time,
            ...result.metrics
          }]);
        }
        
        if (result.status === 'landed') {
          setIsRunning(false);
        }
      }
    } catch (err) {
      console.error('Simulation step error:', err);
      setIsRunning(false);
    }
  }, [simulationId]);
  
  // Run/pause simulation
  useEffect(() => {
    if (isRunning && simulationId) {
      intervalRef.current = setInterval(stepSimulation, 100);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRunning, simulationId, stepSimulation]);
  
  // Reset simulation
  const resetSimulation = async () => {
    if (!simulationId) return;
    
    setIsRunning(false);
    try {
      await axios.post(`${API_URL}/api/landingos/simulation/${simulationId}/reset`);
      setSimData(null);
      setEvents([]);
      setGroundTruth([]);
      setEstimated([]);
      setMetricsHistory([]);
      setAiAnalysis(null);
    } catch (err) {
      console.error('Reset error:', err);
    }
  };
  
  // Request AI analysis
  const requestAiAnalysis = async () => {
    if (!simulationId || !aiEnabled || !aiAvailable) return;
    
    setAiLoading(true);
    try {
      const res = await axios.post(`${API_URL}/api/landingos/ai/analyze`, {
        simulation_id: simulationId,
        analysis_type: 'simulation'
      });
      setAiAnalysis(res.data);
    } catch (err) {
      console.error('AI analysis error:', err);
      setAiAnalysis({ error: 'Failed to get AI analysis' });
    }
    setAiLoading(false);
  };
  
  // Auto-create simulation on mount
  useEffect(() => {
    createSimulation();
  }, []);
  
  const metrics = simData?.metrics || {};
  const altitude = simData?.altitude || config.initial_altitude;
  
  return (
    <div className="min-h-screen bg-[#F8F9FA]">
      {/* Sidebar */}
      <aside className="sidebar" data-testid="sidebar">
        <div className="sidebar-logo">
          <h1 className="font-heading text-xl font-bold text-slate-900">LandingOS</h1>
          <p className="text-xs text-slate-500 mt-1">Event-Driven Navigation</p>
        </div>
        <nav className="sidebar-nav">
          <div className="nav-item active" data-testid="nav-dashboard">
            <Layers size={18} />
            <span>Dashboard</span>
          </div>
          <div className="nav-item" data-testid="nav-simulation">
            <Mountain size={18} />
            <span>Simulation</span>
          </div>
          <div className="nav-item" data-testid="nav-events">
            <Zap size={18} />
            <span>Event Stream</span>
          </div>
          <div className="nav-item" data-testid="nav-trajectory">
            <Activity size={18} />
            <span>Trajectory</span>
          </div>
          <div className="nav-item" data-testid="nav-experiments">
            <BarChart3 size={18} />
            <span>Experiments</span>
          </div>
          <div className="nav-item" data-testid="nav-ai">
            <Brain size={18} />
            <span>AI Analysis</span>
          </div>
          <div className="nav-item" data-testid="nav-settings">
            <Settings size={18} />
            <span>Settings</span>
          </div>
        </nav>
      </aside>
      
      {/* Main Content */}
      <main className="main-content">
        {/* Top Bar */}
        <header className="top-bar">
          <div className="flex items-center gap-4">
            <h2 className="font-heading text-lg font-semibold text-slate-800">Mission Control</h2>
            <div className="flex items-center gap-2">
              <div className={`status-indicator ${isRunning ? 'running' : simData?.status === 'landed' ? 'idle' : 'stopped'}`} />
              <span className="text-sm text-slate-600">
                {isRunning ? 'Descending' : simData?.status === 'landed' ? 'Landed' : 'Ready'}
              </span>
            </div>
          </div>
          <div className="toggle-container">
            <Brain size={16} className={aiEnabled ? 'text-blue-600' : 'text-slate-400'} />
            <span className="toggle-label">AI Analysis</span>
            <button
              data-testid="ai-toggle"
              onClick={() => setAiEnabled(!aiEnabled)}
              className={`relative w-11 h-6 rounded-full transition-colors ${
                aiEnabled ? 'bg-blue-600' : 'bg-slate-300'
              }`}
            >
              <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                aiEnabled ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </button>
          </div>
        </header>
        
        {/* Bento Grid Dashboard */}
        <div className="bento-grid">
          {/* 3D Viewport - Large */}
          <div className="bento-card col-span-8 row-span-2" style={{ minHeight: '400px' }}>
            <div className="bento-card-header">
              <span className="bento-card-title">3D Simulation View</span>
              <div className="flex gap-2">
                <button
                  data-testid="btn-play"
                  onClick={() => setIsRunning(!isRunning)}
                  className="btn-primary btn-lift"
                  disabled={!simulationId || simData?.status === 'landed'}
                >
                  {isRunning ? <Pause size={16} /> : <Play size={16} />}
                  {isRunning ? 'Pause' : 'Start'}
                </button>
                <button
                  data-testid="btn-reset"
                  onClick={resetSimulation}
                  className="btn-secondary"
                >
                  <RotateCcw size={16} />
                </button>
              </div>
            </div>
            <div className="viewport-3d" style={{ height: 'calc(100% - 64px)' }}>
              <Canvas camera={{ position: [50, 80, 50], fov: 60 }}>
                <ambientLight intensity={0.4} />
                <directionalLight position={[50, 100, 50]} intensity={1} />
                <Stars radius={200} depth={100} count={2000} factor={4} fade />
                
                <TerrainMesh terrainType={config.terrain_type} />
                <Lander pose={simData?.ground_truth || { z: altitude }} />
                <EventCloud events={events} />
                <TrajectoryPath poses={groundTruth} color="#0055FF" />
                <TrajectoryPath poses={estimated} color="#FF5F00" />
                
                <OrbitControls enablePan enableZoom enableRotate />
                <gridHelper args={[200, 40, '#334155', '#1E293B']} position={[0, -50, 0]} />
              </Canvas>
              
              {/* Overlay Info */}
              <div className="absolute bottom-4 left-4 glass-panel rounded-lg px-4 py-2">
                <div className="flex items-center gap-4 text-sm">
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded-full bg-blue-600" /> Ground Truth
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded-full bg-orange-500" /> Estimated
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Metrics Panel */}
          <div className="bento-card col-span-4">
            <div className="bento-card-header">
              <span className="bento-card-title">Performance Metrics</span>
              <Gauge size={16} className="text-slate-400" />
            </div>
            <div className="bento-card-content">
              <div className="metric-grid">
                <div className="metric-item" data-testid="metric-altitude">
                  <div className="metric-label">Altitude</div>
                  <div className={`metric-value ${altitude < 100 ? 'warning' : ''}`}>
                    {altitude.toFixed(1)}m
                  </div>
                </div>
                <div className="metric-item" data-testid="metric-pos-error">
                  <div className="metric-label">Position Error</div>
                  <div className={`metric-value ${metrics.position_error > 5 ? 'error' : metrics.position_error < 1 ? 'success' : ''}`}>
                    {(metrics.position_error || 0).toFixed(2)}m
                  </div>
                </div>
                <div className="metric-item" data-testid="metric-att-error">
                  <div className="metric-label">Attitude Error</div>
                  <div className="metric-value">
                    {(metrics.attitude_error || 0).toFixed(2)}&deg;
                  </div>
                </div>
                <div className="metric-item" data-testid="metric-latency">
                  <div className="metric-label">Latency</div>
                  <div className={`metric-value ${metrics.latency_ms > 5 ? 'warning' : 'success'}`}>
                    {(metrics.latency_ms || 0).toFixed(1)}ms
                  </div>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-slate-100">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Events Generated</span>
                  <span className="font-mono font-medium text-blue-600" data-testid="total-events">
                    {(simData?.total_events || 0).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between text-sm mt-2">
                  <span className="text-slate-500">Drift Rate</span>
                  <span className="font-mono font-medium">
                    {(metrics.drift_rate || 0).toFixed(4)} m/s
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Configuration Panel */}
          <div className="bento-card col-span-4">
            <div className="bento-card-header">
              <span className="bento-card-title">Configuration</span>
              <Settings size={16} className="text-slate-400" />
            </div>
            <div className="bento-card-content space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-500 uppercase">Terrain</label>
                <select
                  data-testid="select-terrain"
                  className="select-scientific mt-1"
                  value={config.terrain_type}
                  onChange={e => setConfig({ ...config, terrain_type: e.target.value })}
                  disabled={isRunning}
                >
                  <option value="lunar">Lunar Surface</option>
                  <option value="mars">Martian Surface</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-500 uppercase">Altitude (m)</label>
                  <input
                    data-testid="input-altitude"
                    type="number"
                    className="input-scientific mt-1"
                    value={config.initial_altitude}
                    onChange={e => setConfig({ ...config, initial_altitude: Number(e.target.value) })}
                    disabled={isRunning}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500 uppercase">Velocity (m/s)</label>
                  <input
                    data-testid="input-velocity"
                    type="number"
                    className="input-scientific mt-1"
                    value={config.descent_velocity}
                    onChange={e => setConfig({ ...config, descent_velocity: Number(e.target.value) })}
                    disabled={isRunning}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-500 uppercase">Vibration (&deg;)</label>
                  <input
                    data-testid="input-vibration"
                    type="number"
                    step="0.1"
                    className="input-scientific mt-1"
                    value={config.vibration_amplitude}
                    onChange={e => setConfig({ ...config, vibration_amplitude: Number(e.target.value) })}
                    disabled={isRunning}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500 uppercase">Noise Level</label>
                  <input
                    data-testid="input-noise"
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    className="input-scientific mt-1"
                    value={config.noise_level}
                    onChange={e => setConfig({ ...config, noise_level: Number(e.target.value) })}
                    disabled={isRunning}
                  />
                </div>
              </div>
              <button
                data-testid="btn-new-sim"
                onClick={createSimulation}
                className="btn-secondary w-full mt-2"
                disabled={isRunning}
              >
                New Simulation
              </button>
            </div>
          </div>
          
          {/* Performance Chart */}
          <div className="bento-card col-span-6">
            <div className="bento-card-header">
              <span className="bento-card-title">Position Error Over Time</span>
              <Activity size={16} className="text-slate-400" />
            </div>
            <div className="bento-card-content" style={{ height: '200px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={metricsHistory}>
                  <defs>
                    <linearGradient id="colorError" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0055FF" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#0055FF" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis 
                    dataKey="time" 
                    tickFormatter={v => `${v.toFixed(1)}s`}
                    stroke="#94A3B8"
                    fontSize={11}
                  />
                  <YAxis stroke="#94A3B8" fontSize={11} />
                  <Tooltip 
                    contentStyle={{ 
                      background: 'white', 
                      border: '1px solid #E2E8F0',
                      borderRadius: '6px',
                      fontSize: '12px'
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="position_error" 
                    stroke="#0055FF" 
                    fill="url(#colorError)" 
                    strokeWidth={2}
                    name="Position Error (m)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          {/* Latency Chart */}
          <div className="bento-card col-span-6">
            <div className="bento-card-header">
              <span className="bento-card-title">Processing Latency</span>
              <Clock size={16} className="text-slate-400" />
            </div>
            <div className="bento-card-content" style={{ height: '200px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metricsHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis 
                    dataKey="time" 
                    tickFormatter={v => `${v.toFixed(1)}s`}
                    stroke="#94A3B8"
                    fontSize={11}
                  />
                  <YAxis stroke="#94A3B8" fontSize={11} />
                  <Tooltip 
                    contentStyle={{ 
                      background: 'white', 
                      border: '1px solid #E2E8F0',
                      borderRadius: '6px',
                      fontSize: '12px'
                    }}
                  />
                  <RechartsLine 
                    type="monotone" 
                    dataKey="latency_ms" 
                    stroke="#FF5F00" 
                    strokeWidth={2}
                    dot={false}
                    name="Latency (ms)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          {/* AI Analysis Panel */}
          <div className="bento-card col-span-12">
            <div className="bento-card-header">
              <span className="bento-card-title">AI-Powered Analysis</span>
              <div className="flex items-center gap-2">
                {aiAvailable ? (
                  <span className="flex items-center gap-1 text-xs text-green-600">
                    <CheckCircle size={14} /> Available
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs text-amber-600">
                    <AlertTriangle size={14} /> Disabled
                  </span>
                )}
                <button
                  data-testid="btn-ai-analyze"
                  onClick={requestAiAnalysis}
                  className="btn-primary btn-lift"
                  disabled={!simulationId || !aiEnabled || !aiAvailable || aiLoading}
                >
                  {aiLoading ? (
                    <><span className="spinner" /> Analyzing...</>
                  ) : (
                    <><Brain size={16} /> Analyze Results</>
                  )}
                </button>
              </div>
            </div>
            <div className="bento-card-content">
              {!aiEnabled ? (
                <div className="ai-panel disabled text-center py-8">
                  <Brain size={32} className="mx-auto text-slate-400 mb-2" />
                  <p className="text-slate-500">AI Analysis is disabled. Enable it using the toggle above.</p>
                </div>
              ) : aiAnalysis ? (
                <div className="ai-panel">
                  {aiAnalysis.error ? (
                    <div className="flex items-center gap-2 text-red-600">
                      <AlertTriangle size={16} />
                      <span>{aiAnalysis.error}</span>
                    </div>
                  ) : (
                    <div className="prose prose-sm max-w-none">
                      <div className="whitespace-pre-wrap text-slate-700 text-sm leading-relaxed">
                        {aiAnalysis.analysis || aiAnalysis.message}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="ai-panel text-center py-8">
                  <Cpu size={32} className="mx-auto text-blue-400 mb-2" />
                  <p className="text-slate-600">Run a simulation and click "Analyze Results" for AI-powered insights.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
