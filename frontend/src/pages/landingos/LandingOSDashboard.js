import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Play, Pause, RotateCcw, Settings, Cpu, Activity, Gauge, 
  Mountain, Zap, Box, Upload, Download, FileText, X, GitCompare,
  Layers, BarChart3, Clock, Eye, EyeOff, Maximize2, Grid3X3
} from 'lucide-react';
import { LineChart, Line as RechartsLine, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import axios from 'axios';
import Scene3D from '../../components/Scene3D';
import BatchExperimentsPanel from '../../components/BatchExperiments';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// 2D Event visualization canvas
function EventCanvas({ events, corners }) {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas with gradient background
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#0F172A');
    gradient.addColorStop(1, '#1E293B');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
    
    // Draw grid
    ctx.strokeStyle = '#1E3A5F';
    ctx.lineWidth = 0.5;
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
    
    // Draw events with glow effect
    if (events && events.length > 0) {
      events.slice(0, 500).forEach(event => {
        const x = (event.x / 640) * width;
        const y = (event.y / 480) * height;
        
        // Glow effect
        ctx.shadowBlur = 8;
        ctx.shadowColor = event.polarity > 0 ? '#0088FF' : '#FF6600';
        
        ctx.fillStyle = event.polarity > 0 ? '#0055FF' : '#FF5F00';
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.shadowBlur = 0;
    }
    
    // Draw detected corners (SNN)
    if (corners && corners.length > 0) {
      ctx.strokeStyle = '#FFFF00';
      ctx.lineWidth = 2;
      corners.forEach(corner => {
        const x = (corner.x / 640) * width;
        const y = (corner.y / 480) * height;
        
        ctx.beginPath();
        ctx.moveTo(x - 8, y);
        ctx.lineTo(x + 8, y);
        ctx.moveTo(x, y - 8);
        ctx.lineTo(x, y + 8);
        ctx.stroke();
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
    
  }, [events, corners]);
  
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

// Hardware Import Modal
function ImportModal({ isOpen, onClose, onImport }) {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);
  
  const handleFileSelect = async (file) => {
    if (!file) return;
    
    setUploading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await axios.post(`${API_URL}/api/landingos/import/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      onImport(res.data);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4">
        <div className="flex items-center justify-between p-4 border-b border-slate-200">
          <h3 className="font-heading text-lg font-semibold text-slate-800">Import Hardware Data</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={20} />
          </button>
        </div>
        <div className="p-6">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragOver ? 'border-blue-500 bg-blue-50' : 'border-slate-300'
            }`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
          >
            <Upload size={40} className="mx-auto text-slate-400 mb-4" />
            <p className="text-slate-600 mb-2">Drag & drop event camera file here</p>
            <p className="text-sm text-slate-400 mb-4">or</p>
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept=".csv,.json,.txt,.npy,.aedat,.aedat4,.raw"
              onChange={(e) => handleFileSelect(e.target.files[0])}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="btn-primary"
              disabled={uploading}
            >
              {uploading ? 'Uploading...' : 'Browse Files'}
            </button>
          </div>
          
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}
          
          <div className="mt-4 text-xs text-slate-500">
            <p className="font-medium mb-1">Supported formats:</p>
            <p>CSV, JSON, TXT, NumPy (.npy), AEDAT 4.0, Prophesee RAW</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Export Menu
function ExportMenu({ simulationId, onClose }) {
  const handleExport = async (type, format) => {
    if (!simulationId) return;
    
    let url;
    if (type === 'events') {
      url = `${API_URL}/api/landingos/export/simulation/${simulationId}/events?format=${format}`;
    } else if (type === 'trajectory') {
      url = `${API_URL}/api/landingos/export/simulation/${simulationId}/trajectory?format=${format}`;
    }
    
    window.open(url, '_blank');
    onClose();
  };
  
  return (
    <div className="absolute right-0 top-full mt-2 bg-white rounded-lg shadow-lg border border-slate-200 py-2 w-48 z-20">
      <div className="px-3 py-1 text-xs font-medium text-slate-400 uppercase">Events</div>
      <button
        onClick={() => handleExport('events', 'csv')}
        className="w-full px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
      >
        Export as CSV
      </button>
      <button
        onClick={() => handleExport('events', 'json')}
        className="w-full px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
      >
        Export as JSON
      </button>
      <div className="border-t border-slate-100 my-1" />
      <div className="px-3 py-1 text-xs font-medium text-slate-400 uppercase">Trajectory</div>
      <button
        onClick={() => handleExport('trajectory', 'csv')}
        className="w-full px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
      >
        Export as CSV
      </button>
      <button
        onClick={() => handleExport('trajectory', 'json')}
        className="w-full px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
      >
        Export as JSON
      </button>
    </div>
  );
}

// Main Dashboard Component
export default function LandingOSDashboard() {
  const [simulationId, setSimulationId] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [simData, setSimData] = useState(null);
  const [events, setEvents] = useState([]);
  const [corners, setCorners] = useState([]);
  const [groundTruth, setGroundTruth] = useState([]);
  const [estimated, setEstimated] = useState([]);
  const [metricsHistory, setMetricsHistory] = useState([]);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [importedDataset, setImportedDataset] = useState(null);
  // View state
  const [activeView, setActiveView] = useState('dashboard'); // dashboard, 3d, batch
  const [show3D, setShow3D] = useState(false);
  const [terrain3DData, setTerrain3DData] = useState(null);
  // Comparison state
  const [comparisonEnabled, setComparisonEnabled] = useState(false);
  const [comparisonResults, setComparisonResults] = useState(null);
  // SNN state
  const [snnEnabled, setSnnEnabled] = useState(true);
  const intervalRef = useRef(null);
  const wsRef = useRef(null);
  
  // Configuration state
  const [config, setConfig] = useState({
    terrain_type: 'lunar',
    initial_altitude: 1000,
    descent_velocity: 50,
    vibration_amplitude: 0.5,
    noise_level: 0.1,
    feature_density: 200,
    use_snn_processing: true
  });
  
  // Create simulation
  const createSimulation = useCallback(async () => {
    try {
      const res = await axios.post(`${API_URL}/api/landingos/simulation/create`, {
        ...config,
        use_snn_processing: snnEnabled
      });
      setSimulationId(res.data.id);
      setSimData(res.data);
      setEvents([]);
      setCorners([]);
      setGroundTruth([]);
      setEstimated([]);
      setMetricsHistory([]);
      setComparisonResults(null);
      
      // Fetch 3D data
      const data3D = await axios.get(`${API_URL}/api/landingos/simulation/${res.data.id}/3d`);
      setTerrain3DData(data3D.data.terrain);
      
      if (comparisonEnabled) {
        await axios.post(`${API_URL}/api/landingos/simulation/${res.data.id}/enable-comparison`);
      }
    } catch (err) {
      console.error('Failed to create simulation:', err);
    }
  }, [config, comparisonEnabled, snnEnabled]);
  
  // Toggle comparison mode
  const toggleComparison = async () => {
    if (!simulationId) {
      setComparisonEnabled(!comparisonEnabled);
      return;
    }
    
    try {
      if (!comparisonEnabled) {
        await axios.post(`${API_URL}/api/landingos/simulation/${simulationId}/enable-comparison`);
        setComparisonEnabled(true);
      } else {
        await axios.delete(`${API_URL}/api/landingos/simulation/${simulationId}/disable-comparison`);
        setComparisonEnabled(false);
        setComparisonResults(null);
      }
    } catch (err) {
      console.error('Toggle comparison error:', err);
    }
  };
  
  // Get comparison results
  const fetchComparison = async () => {
    if (!simulationId || !comparisonEnabled) return;
    
    try {
      const res = await axios.get(`${API_URL}/api/landingos/simulation/${simulationId}/comparison`);
      setComparisonResults(res.data.comparison);
    } catch (err) {
      console.error('Fetch comparison error:', err);
    }
  };
  
  // Step simulation
  const stepSimulation = useCallback(async () => {
    if (!simulationId) return;
    
    try {
      const endpoint = comparisonEnabled 
        ? `${API_URL}/api/landingos/simulation/${simulationId}/step-comparison`
        : `${API_URL}/api/landingos/simulation/${simulationId}/step`;
      
      const res = await axios.post(endpoint, null, {
        params: { steps: 5 }
      });
      
      const result = comparisonEnabled ? res.data.final_result?.evo : res.data.final_result;
      
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
          if (comparisonEnabled) {
            fetchComparison();
          }
        }
      }
    } catch (err) {
      console.error('Simulation step error:', err);
      setIsRunning(false);
    }
  }, [simulationId, comparisonEnabled]);
  
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
      setCorners([]);
      setGroundTruth([]);
      setEstimated([]);
      setMetricsHistory([]);
      setComparisonResults(null);
    } catch (err) {
      console.error('Reset error:', err);
    }
  };
  
  // Auto-create simulation on mount
  useEffect(() => {
    createSimulation();
  }, []);
  
  const metrics = simData?.metrics || {};
  const altitude = simData?.altitude || config.initial_altitude;
  const currentGT = groundTruth[groundTruth.length - 1];
  const currentEst = estimated[estimated.length - 1];
  
  return (
    <div className="min-h-screen bg-[#F8F9FA]">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1 className="font-heading text-xl font-bold text-slate-900">LandingOS</h1>
          <p className="text-xs text-slate-500 mt-1">Event-Driven Navigation</p>
          <span className="text-xs text-blue-600 font-medium mt-1 block">Local Mode</span>
        </div>
        <nav className="sidebar-nav">
          <div 
            className={`nav-item ${activeView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveView('dashboard')}
          >
            <Layers size={18} />
            <span>Dashboard</span>
          </div>
          <div 
            className={`nav-item ${activeView === '3d' ? 'active' : ''}`}
            onClick={() => setActiveView('3d')}
          >
            <Box size={18} />
            <span>3D View</span>
          </div>
          <div 
            className={`nav-item ${activeView === 'batch' ? 'active' : ''}`}
            onClick={() => setActiveView('batch')}
          >
            <Grid3X3 size={18} />
            <span>Batch Experiments</span>
          </div>
          <div className="nav-item" onClick={() => setShowImportModal(true)}>
            <Upload size={18} />
            <span>Import Data</span>
          </div>
          <div className="nav-item relative">
            <Download size={18} />
            <span onClick={() => setShowExportMenu(!showExportMenu)}>Export Data</span>
            {showExportMenu && (
              <ExportMenu simulationId={simulationId} onClose={() => setShowExportMenu(false)} />
            )}
          </div>
          
          <div className="border-t border-slate-200 my-3" />
          
          <a 
            href="/docs/README.md" 
            target="_blank" 
            rel="noopener noreferrer"
            className="nav-item"
          >
            <FileText size={18} />
            <span>Documentation</span>
          </a>
        </nav>
      </aside>
      
      {/* Main Content */}
      <main className="main-content">
        {/* Top Bar */}
        <header className="top-bar">
          <div className="flex items-center gap-4">
            <h2 className="font-heading text-lg font-semibold text-slate-800">
              {activeView === 'dashboard' ? 'Mission Control' : 
               activeView === '3d' ? '3D Visualization' : 'Batch Experiments'}
            </h2>
            <div className="flex items-center gap-2">
              <div className={`status-indicator ${isRunning ? 'running' : simData?.status === 'landed' ? 'idle' : 'stopped'}`} />
              <span className="text-sm text-slate-600">
                {isRunning ? 'Descending' : simData?.status === 'landed' ? 'Landed' : 'Ready'}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-6">
            {/* SNN Toggle */}
            <div className="toggle-container">
              <Cpu size={16} className={snnEnabled ? 'text-purple-600' : 'text-slate-400'} />
              <span className="toggle-label">SNN Processing</span>
              <button
                onClick={() => setSnnEnabled(!snnEnabled)}
                className={`relative w-11 h-6 rounded-full transition-colors ${
                  snnEnabled ? 'bg-purple-500' : 'bg-slate-300'
                }`}
              >
                <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                  snnEnabled ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
            {/* Comparison Toggle */}
            <div className="toggle-container">
              <GitCompare size={16} className={comparisonEnabled ? 'text-orange-600' : 'text-slate-400'} />
              <span className="toggle-label">Compare FVO</span>
              <button
                onClick={toggleComparison}
                className={`relative w-11 h-6 rounded-full transition-colors ${
                  comparisonEnabled ? 'bg-orange-500' : 'bg-slate-300'
                }`}
              >
                <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                  comparisonEnabled ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>
        </header>
        
        {/* View Content */}
        {activeView === 'dashboard' && (
          <div className="bento-grid">
            {/* Event Visualization */}
            <div className="bento-card col-span-8 row-span-2" style={{ minHeight: '400px' }}>
              <div className="bento-card-header">
                <span className="bento-card-title">
                  Event Camera View {snnEnabled && <span className="text-purple-600 text-xs ml-2">(SNN)</span>}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShow3D(!show3D)}
                    className="btn-secondary"
                  >
                    {show3D ? <Eye size={16} /> : <EyeOff size={16} />}
                    {show3D ? '2D' : '3D'}
                  </button>
                  <button
                    onClick={() => setIsRunning(!isRunning)}
                    className="btn-primary btn-lift"
                    disabled={!simulationId || simData?.status === 'landed'}
                  >
                    {isRunning ? <Pause size={16} /> : <Play size={16} />}
                    {isRunning ? 'Pause' : 'Start'}
                  </button>
                  <button
                    onClick={resetSimulation}
                    className="btn-secondary"
                  >
                    <RotateCcw size={16} />
                  </button>
                </div>
              </div>
              <div className="bento-card-content flex gap-4" style={{ height: 'calc(100% - 64px)' }}>
                {show3D ? (
                  <div className="flex-1 rounded-lg overflow-hidden">
                    <Scene3D
                      terrainData={terrain3DData}
                      currentPose={currentGT}
                      groundTruthTrajectory={groundTruth}
                      estimatedTrajectory={estimated}
                      events={events}
                      corners={corners}
                      isRunning={isRunning}
                    />
                  </div>
                ) : (
                  <div className="flex-1 bg-slate-900 rounded-lg overflow-hidden">
                    <EventCanvas events={events} corners={corners} />
                  </div>
                )}
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
                  <div className="metric-item">
                    <div className="metric-label">Altitude</div>
                    <div className={`metric-value ${altitude < 100 ? 'warning' : ''}`}>
                      {altitude.toFixed(1)}m
                    </div>
                  </div>
                  <div className="metric-item">
                    <div className="metric-label">Position Error</div>
                    <div className={`metric-value ${metrics.position_error > 5 ? 'error' : metrics.position_error < 1 ? 'success' : ''}`}>
                      {(metrics.position_error || 0).toFixed(2)}m
                    </div>
                  </div>
                  <div className="metric-item">
                    <div className="metric-label">Attitude Error</div>
                    <div className="metric-value">
                      {(metrics.attitude_error || 0).toFixed(2)}°
                    </div>
                  </div>
                  <div className="metric-item">
                    <div className="metric-label">Latency</div>
                    <div className={`metric-value ${metrics.latency_ms > 5 ? 'warning' : 'success'}`}>
                      {(metrics.latency_ms || 0).toFixed(1)}ms
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-slate-100">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">Events Generated</span>
                    <span className="font-mono font-medium text-blue-600">
                      {(simData?.total_events || 0).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm mt-2">
                    <span className="text-slate-500">Drift Rate</span>
                    <span className="font-mono font-medium">
                      {(metrics.drift_rate || 0).toFixed(4)} m/s
                    </span>
                  </div>
                  {snnEnabled && (
                    <>
                      <div className="flex justify-between text-sm mt-2">
                        <span className="text-slate-500">Corners Detected</span>
                        <span className="font-mono font-medium text-purple-600">
                          {simData?.corners_detected || 0}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm mt-2">
                        <span className="text-slate-500">Features Tracked</span>
                        <span className="font-mono font-medium text-purple-600">
                          {simData?.features_tracked || 0}
                        </span>
                      </div>
                    </>
                  )}
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
                    className="select-scientific mt-1"
                    value={config.terrain_type}
                    onChange={e => setConfig({ ...config, terrain_type: e.target.value })}
                    disabled={isRunning}
                  >
                    <option value="lunar">Lunar Surface</option>
                    <option value="mars">Martian Surface</option>
                    <option value="asteroid">Asteroid</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-500 uppercase">Altitude (m)</label>
                    <input
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
                    <label className="text-xs font-medium text-slate-500 uppercase">Vibration (°)</label>
                    <input
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
                    <Tooltip />
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
                    <Tooltip />
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
            
            {/* VO Comparison Panel */}
            {comparisonEnabled && comparisonResults && (
              <div className="bento-card col-span-12">
                <div className="bento-card-header">
                  <span className="bento-card-title">Visual Odometry Comparison: Event-Based vs Frame-Based</span>
                  <button
                    onClick={fetchComparison}
                    className="btn-secondary"
                    disabled={!simulationId || isRunning}
                  >
                    <GitCompare size={16} /> Refresh
                  </button>
                </div>
                <div className="bento-card-content">
                  <div className="grid grid-cols-3 gap-6">
                    {/* EVO Results */}
                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                      <div className="flex items-center gap-2 mb-3">
                        <Zap size={18} className="text-blue-600" />
                        <span className="font-semibold text-blue-900">Event-Based VO {snnEnabled && '(SNN)'}</span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-600">Avg Position Error</span>
                          <span className="font-mono font-medium text-blue-600">
                            {comparisonResults.event_based_vo?.average_position_error?.toFixed(3)}m
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">Avg Attitude Error</span>
                          <span className="font-mono font-medium">
                            {comparisonResults.event_based_vo?.average_attitude_error?.toFixed(3)}°
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    {/* FVO Results */}
                    <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                      <div className="flex items-center gap-2 mb-3">
                        <Activity size={18} className="text-orange-600" />
                        <span className="font-semibold text-orange-900">Frame-Based VO</span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-600">Avg Position Error</span>
                          <span className="font-mono font-medium text-orange-600">
                            {comparisonResults.frame_based_vo?.average_position_error?.toFixed(3)}m
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">Avg Attitude Error</span>
                          <span className="font-mono font-medium">
                            {comparisonResults.frame_based_vo?.average_attitude_error?.toFixed(3)}°
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Winner */}
                    <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                      <div className="flex items-center gap-2 mb-3">
                        <GitCompare size={18} className="text-slate-600" />
                        <span className="font-semibold text-slate-900">Winner</span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-600">Position</span>
                          <span className={`font-medium ${
                            comparisonResults.comparison?.position_accuracy_winner === 'EVO' 
                              ? 'text-blue-600' : 'text-orange-600'
                          }`}>
                            {comparisonResults.comparison?.position_accuracy_winner}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-600">Improvement</span>
                          <span className={`font-mono font-medium ${
                            comparisonResults.comparison?.evo_position_improvement_percent > 0 
                              ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {comparisonResults.comparison?.evo_position_improvement_percent > 0 ? '+' : ''}
                            {comparisonResults.comparison?.evo_position_improvement_percent}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* 3D View */}
        {activeView === '3d' && (
          <div className="h-[calc(100vh-120px)] rounded-lg overflow-hidden">
            <Scene3D
              terrainData={terrain3DData}
              currentPose={currentGT}
              groundTruthTrajectory={groundTruth}
              estimatedTrajectory={estimated}
              events={events}
              corners={corners}
              isRunning={isRunning}
              followCamera={true}
            />
            {/* 3D Controls Overlay */}
            <div className="absolute bottom-4 left-4 bg-white/90 rounded-lg p-4 shadow-lg">
              <div className="flex gap-3">
                <button
                  onClick={() => setIsRunning(!isRunning)}
                  className="btn-primary"
                  disabled={!simulationId || simData?.status === 'landed'}
                >
                  {isRunning ? <Pause size={16} /> : <Play size={16} />}
                  {isRunning ? 'Pause' : 'Start'}
                </button>
                <button onClick={resetSimulation} className="btn-secondary">
                  <RotateCcw size={16} /> Reset
                </button>
              </div>
              <div className="mt-3 text-sm text-slate-600">
                <div>Altitude: <span className="font-mono font-medium">{altitude.toFixed(1)}m</span></div>
                <div>Events: <span className="font-mono font-medium">{(simData?.total_events || 0).toLocaleString()}</span></div>
              </div>
            </div>
          </div>
        )}
        
        {/* Batch Experiments View */}
        {activeView === 'batch' && (
          <div className="p-6">
            <BatchExperimentsPanel />
          </div>
        )}
      </main>
      
      {/* Import Modal */}
      <ImportModal 
        isOpen={showImportModal} 
        onClose={() => setShowImportModal(false)}
        onImport={(data) => setImportedDataset(data)}
      />
    </div>
  );
}
