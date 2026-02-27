import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Play, Pause, RotateCcw, Settings, Cpu, Activity, Gauge, 
  Mountain, Zap, Brain, AlertTriangle, CheckCircle,
  BarChart3, Clock, Layers, Box, Upload, Download, FileText, X
} from 'lucide-react';
import { LineChart, Line as RechartsLine, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// 2D Event visualization canvas
function EventCanvas({ events }) {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.fillStyle = '#0F172A';
    ctx.fillRect(0, 0, width, height);
    
    // Draw grid
    ctx.strokeStyle = '#1E293B';
    ctx.lineWidth = 1;
    for (let x = 0; x < width; x += 32) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += 32) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
    
    // Draw events
    if (events && events.length > 0) {
      events.slice(0, 500).forEach(event => {
        const x = (event.x / 640) * width;
        const y = (event.y / 480) * height;
        
        ctx.fillStyle = event.polarity > 0 ? '#0055FF' : '#FF5F00';
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      });
    }
    
    // Draw center crosshair
    ctx.strokeStyle = '#64748B';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(width / 2, 0);
    ctx.lineTo(width / 2, height);
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();
    ctx.setLineDash([]);
    
  }, [events]);
  
  return (
    <canvas 
      ref={canvasRef} 
      width={640} 
      height={480} 
      className="w-full h-full rounded-lg"
      data-testid="event-canvas"
    />
  );
}

// Altitude indicator
function AltitudeIndicator({ altitude, maxAltitude }) {
  const percentage = Math.min(100, (altitude / maxAltitude) * 100);
  
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Altitude</div>
      <div className="relative w-16 h-48 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
        <div 
          className="absolute bottom-0 w-full bg-gradient-to-t from-blue-600 to-blue-400 transition-all duration-300"
          style={{ height: `${percentage}%` }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-mono text-sm font-bold text-slate-800 bg-white/80 px-2 py-1 rounded">
            {altitude.toFixed(0)}m
          </span>
        </div>
      </div>
      <div className="text-xs text-slate-400">Ground</div>
    </div>
  );
}

// Pose display
function PoseDisplay({ pose, label, color }) {
  if (!pose) return null;
  
  return (
    <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
        <span className="text-xs font-medium text-slate-600 uppercase">{label}</span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-xs text-slate-400">X</div>
          <div className="font-mono text-sm">{(pose.x || 0).toFixed(2)}</div>
        </div>
        <div>
          <div className="text-xs text-slate-400">Y</div>
          <div className="font-mono text-sm">{(pose.y || 0).toFixed(2)}</div>
        </div>
        <div>
          <div className="text-xs text-slate-400">Z</div>
          <div className="font-mono text-sm">{(pose.z || 0).toFixed(2)}</div>
        </div>
      </div>
    </div>
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  const metrics = simData?.metrics || {};
  const altitude = simData?.altitude || config.initial_altitude;
  const currentGT = groundTruth[groundTruth.length - 1];
  const currentEst = estimated[estimated.length - 1];
  
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
          {/* Event Visualization - Large */}
          <div className="bento-card col-span-8 row-span-2" style={{ minHeight: '400px' }}>
            <div className="bento-card-header">
              <span className="bento-card-title">Event Camera View</span>
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
            <div className="bento-card-content flex gap-4" style={{ height: 'calc(100% - 64px)' }}>
              <div className="flex-1 bg-slate-900 rounded-lg overflow-hidden">
                <EventCanvas events={events} />
              </div>
              <AltitudeIndicator altitude={altitude} maxAltitude={config.initial_altitude} />
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
          
          {/* Pose Comparison */}
          <div className="bento-card col-span-4">
            <div className="bento-card-header">
              <span className="bento-card-title">Pose Estimation</span>
              <Box size={16} className="text-slate-400" />
            </div>
            <div className="bento-card-content space-y-3">
              <PoseDisplay pose={currentGT} label="Ground Truth" color="#0055FF" />
              <PoseDisplay pose={currentEst} label="EVO Estimate" color="#FF5F00" />
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
                    tickFormatter={v => `${v?.toFixed(1) || 0}s`}
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
                    tickFormatter={v => `${v?.toFixed(1) || 0}s`}
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
