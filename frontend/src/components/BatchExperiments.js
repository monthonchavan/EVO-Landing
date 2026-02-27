import React, { useState, useEffect, useCallback } from 'react';
import { 
  Play, Pause, RotateCcw, Plus, Trash2, BarChart3, 
  Download, CheckCircle, XCircle, Clock, Zap, Activity
} from 'lucide-react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Single experiment card
function ExperimentCard({ experiment, onRun, onDelete, isRunning }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-slate-800">{experiment.name}</h4>
        <span className={`px-2 py-1 text-xs rounded-full ${
          experiment.status === 'completed' 
            ? 'bg-green-100 text-green-700' 
            : experiment.status === 'running'
            ? 'bg-blue-100 text-blue-700 animate-pulse'
            : 'bg-slate-100 text-slate-600'
        }`}>
          {experiment.status || 'pending'}
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-2 text-sm mb-3">
        <div>
          <span className="text-slate-500">Terrain:</span>
          <span className="ml-2 font-medium">{experiment.config?.terrain_type || 'lunar'}</span>
        </div>
        <div>
          <span className="text-slate-500">SNN:</span>
          <span className="ml-2 font-medium">{experiment.config?.use_snn ? 'Yes' : 'No'}</span>
        </div>
        <div>
          <span className="text-slate-500">Vibration:</span>
          <span className="ml-2 font-medium">{experiment.config?.vibration}°</span>
        </div>
        <div>
          <span className="text-slate-500">Noise:</span>
          <span className="ml-2 font-medium">{(experiment.config?.noise * 100).toFixed(0)}%</span>
        </div>
      </div>
      
      {experiment.status === 'completed' && (
        <div className="bg-slate-50 rounded p-2 mb-3">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-slate-400">Position Error:</span>
              <span className="ml-1 font-mono font-medium text-blue-600">
                {experiment.final_position_error?.toFixed(3)}m
              </span>
            </div>
            <div>
              <span className="text-slate-400">Attitude Error:</span>
              <span className="ml-1 font-mono font-medium">
                {experiment.final_attitude_error?.toFixed(3)}°
              </span>
            </div>
          </div>
        </div>
      )}
      
      <div className="flex gap-2">
        {experiment.status !== 'completed' && (
          <button
            onClick={() => onRun(experiment)}
            disabled={isRunning}
            className="flex-1 btn-primary text-sm py-2"
          >
            <Play size={14} /> Run
          </button>
        )}
        <button
          onClick={() => onDelete(experiment.id)}
          className="btn-secondary text-sm py-2 px-3"
        >
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  );
}

// Comparison chart
function ComparisonChart({ experiments }) {
  if (!experiments || experiments.length < 2) return null;
  
  // Prepare data for chart
  const chartData = experiments.map(exp => ({
    name: exp.name.substring(0, 15),
    position_error: exp.final_position_error,
    attitude_error: exp.final_attitude_error,
    drift_rate: exp.average_drift_rate * 1000  // Scale for visibility
  }));
  
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <h4 className="font-semibold text-slate-800 mb-4">Comparison Chart</h4>
      <div style={{ height: '300px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
            <XAxis dataKey="name" stroke="#94A3B8" fontSize={11} />
            <YAxis stroke="#94A3B8" fontSize={11} />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="position_error" 
              stroke="#0055FF" 
              name="Position Error (m)"
              strokeWidth={2}
            />
            <Line 
              type="monotone" 
              dataKey="attitude_error" 
              stroke="#FF5F00" 
              name="Attitude Error (°)"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Ranking table
function RankingTable({ comparison }) {
  if (!comparison || !comparison.rankings) return null;
  
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <h4 className="font-semibold text-slate-800 mb-4">Rankings</h4>
      
      <div className="grid grid-cols-2 gap-4">
        {/* Position Error Ranking */}
        <div>
          <h5 className="text-sm font-medium text-slate-600 mb-2">Position Accuracy</h5>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 text-xs">
                <th className="text-left py-1">Rank</th>
                <th className="text-left py-1">Name</th>
                <th className="text-right py-1">Error</th>
              </tr>
            </thead>
            <tbody>
              {comparison.rankings.position_error?.map((item, idx) => (
                <tr key={idx} className={idx === 0 ? 'bg-green-50' : ''}>
                  <td className="py-1">
                    {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `#${item.rank}`}
                  </td>
                  <td className="py-1 truncate max-w-[100px]">{item.name}</td>
                  <td className="py-1 text-right font-mono">{item.value.toFixed(3)}m</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Attitude Error Ranking */}
        <div>
          <h5 className="text-sm font-medium text-slate-600 mb-2">Attitude Accuracy</h5>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 text-xs">
                <th className="text-left py-1">Rank</th>
                <th className="text-left py-1">Name</th>
                <th className="text-right py-1">Error</th>
              </tr>
            </thead>
            <tbody>
              {comparison.rankings.attitude_error?.map((item, idx) => (
                <tr key={idx} className={idx === 0 ? 'bg-green-50' : ''}>
                  <td className="py-1">
                    {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `#${item.rank}`}
                  </td>
                  <td className="py-1 truncate max-w-[100px]">{item.name}</td>
                  <td className="py-1 text-right font-mono">{item.value.toFixed(3)}°</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Best Overall */}
      {comparison.best_overall && (
        <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2">
            <CheckCircle size={18} className="text-blue-600" />
            <span className="font-medium text-blue-800">Best Overall:</span>
            <span className="text-blue-600">{comparison.best_overall.name}</span>
          </div>
        </div>
      )}
    </div>
  );
}

// New experiment form
function NewExperimentForm({ onAdd, onClose }) {
  const [form, setForm] = useState({
    name: `Experiment ${Date.now().toString().slice(-6)}`,
    terrain_type: 'lunar',
    initial_altitude: 1000,
    descent_velocity: 50,
    vibration_amplitude: 0.5,
    noise_level: 0.1,
    use_snn_processing: true
  });
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onAdd(form);
    onClose();
  };
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-4">New Experiment</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-600">Name</label>
            <input
              type="text"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              className="input-scientific mt-1"
              required
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-slate-600">Terrain</label>
              <select
                value={form.terrain_type}
                onChange={e => setForm({ ...form, terrain_type: e.target.value })}
                className="select-scientific mt-1"
              >
                <option value="lunar">Lunar</option>
                <option value="mars">Mars</option>
                <option value="asteroid">Asteroid</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-600">SNN Processing</label>
              <select
                value={form.use_snn_processing.toString()}
                onChange={e => setForm({ ...form, use_snn_processing: e.target.value === 'true' })}
                className="select-scientific mt-1"
              >
                <option value="true">Enabled</option>
                <option value="false">Disabled</option>
              </select>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-slate-600">Altitude (m)</label>
              <input
                type="number"
                value={form.initial_altitude}
                onChange={e => setForm({ ...form, initial_altitude: Number(e.target.value) })}
                className="input-scientific mt-1"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-600">Velocity (m/s)</label>
              <input
                type="number"
                value={form.descent_velocity}
                onChange={e => setForm({ ...form, descent_velocity: Number(e.target.value) })}
                className="input-scientific mt-1"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-slate-600">Vibration (°)</label>
              <input
                type="number"
                step="0.1"
                value={form.vibration_amplitude}
                onChange={e => setForm({ ...form, vibration_amplitude: Number(e.target.value) })}
                className="input-scientific mt-1"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-600">Noise Level</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={form.noise_level}
                onChange={e => setForm({ ...form, noise_level: Number(e.target.value) })}
                className="input-scientific mt-1"
              />
            </div>
          </div>
          
          <div className="flex gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
            <button type="submit" className="btn-primary flex-1">
              <Plus size={16} /> Add Experiment
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Main Batch Experiments Panel
export default function BatchExperimentsPanel() {
  const [experiments, setExperiments] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [showNewForm, setShowNewForm] = useState(false);
  const [presets, setPresets] = useState({});
  
  // Load presets
  useEffect(() => {
    axios.get(`${API_URL}/api/landingos/experiments/presets`)
      .then(res => setPresets(res.data))
      .catch(console.error);
  }, []);
  
  // Add new experiment
  const handleAddExperiment = (config) => {
    const newExp = {
      id: `local-${Date.now()}`,
      name: config.name,
      config: {
        terrain_type: config.terrain_type,
        use_snn: config.use_snn_processing,
        vibration: config.vibration_amplitude,
        noise: config.noise_level,
        altitude: config.initial_altitude,
        velocity: config.descent_velocity
      },
      status: 'pending',
      ...config
    };
    setExperiments(prev => [...prev, newExp]);
  };
  
  // Poll task status
  const pollTaskStatus = useCallback(async (taskId, experimentIds) => {
    try {
      const response = await axios.get(`${API_URL}/api/landingos/experiments/task/${taskId}`);
      const taskData = response.data;
      
      if (taskData.status === 'completed') {
        // Fetch results
        const resultsRes = await axios.get(`${API_URL}/api/landingos/experiments/task/${taskId}/results`);
        const results = resultsRes.data.results || [];
        
        // Update experiments with results
        setExperiments(prev => prev.map(e => {
          if (experimentIds.includes(e.id)) {
            const result = results.find(r => r.name === e.name) || results[0];
            if (result) {
              return {
                ...e,
                status: 'completed',
                final_position_error: result.final_position_error,
                final_attitude_error: result.final_attitude_error,
                average_drift_rate: result.average_drift_rate,
                duration: result.duration,
                server_id: result.id
              };
            }
          }
          return e;
        }));
        
        setIsRunning(false);
        return true; // Completed
      } else if (taskData.status === 'failed') {
        // Mark experiments as failed
        setExperiments(prev => prev.map(e => 
          experimentIds.includes(e.id) ? { ...e, status: 'error' } : e
        ));
        setIsRunning(false);
        return true; // Done (with error)
      }
      
      // Still running or pending
      return false;
    } catch (err) {
      console.error('Poll error:', err);
      return false;
    }
  }, []);
  
  // Run single experiment with async polling
  const handleRunExperiment = async (experiment) => {
    setIsRunning(true);
    
    // Update status
    setExperiments(prev => prev.map(e => 
      e.id === experiment.id ? { ...e, status: 'running' } : e
    ));
    
    try {
      const response = await axios.post(`${API_URL}/api/landingos/experiments/run`, [{
        name: experiment.name,
        terrain_type: experiment.config.terrain_type,
        initial_altitude: experiment.config.altitude || 1000,
        descent_velocity: experiment.config.velocity || 50,
        vibration_amplitude: experiment.config.vibration,
        noise_level: experiment.config.noise,
        use_snn_processing: experiment.config.use_snn
      }]);
      
      const taskId = response.data.task_id;
      const experimentIds = [experiment.id];
      
      // Poll for completion
      const pollInterval = setInterval(async () => {
        const isDone = await pollTaskStatus(taskId, experimentIds);
        if (isDone) {
          clearInterval(pollInterval);
        }
      }, 2000); // Poll every 2 seconds
      
    } catch (err) {
      console.error('Run experiment error:', err);
      setExperiments(prev => prev.map(e => 
        e.id === experiment.id ? { ...e, status: 'error' } : e
      ));
      setIsRunning(false);
    }
  };
  
  // Run all pending experiments
  const handleRunAll = async () => {
    const pending = experiments.filter(e => e.status === 'pending');
    for (const exp of pending) {
      await handleRunExperiment(exp);
    }
  };
  
  // Delete experiment
  const handleDelete = (id) => {
    setExperiments(prev => prev.filter(e => e.id !== id));
  };
  
  // Compare completed experiments with async polling
  const handleCompare = async () => {
    const completed = experiments.filter(e => e.status === 'completed' && e.server_id);
    
    if (completed.length < 2) {
      alert('Need at least 2 completed experiments to compare');
      return;
    }
    
    try {
      const response = await axios.post(`${API_URL}/api/landingos/experiments/compare`, 
        completed.map(e => e.server_id)
      );
      
      const taskId = response.data.task_id;
      
      // Poll for comparison results
      const pollComparison = async () => {
        try {
          const statusRes = await axios.get(`${API_URL}/api/landingos/experiments/comparison/${taskId}`);
          if (statusRes.data.status === 'completed') {
            const resultsRes = await axios.get(`${API_URL}/api/landingos/experiments/comparison/${taskId}/results`);
            setComparison(resultsRes.data);
            return true;
          }
          return false;
        } catch (err) {
          console.error('Poll comparison error:', err);
          return false;
        }
      };
      
      // Poll every 2 seconds
      const pollInterval = setInterval(async () => {
        const isDone = await pollComparison();
        if (isDone) {
          clearInterval(pollInterval);
        }
      }, 2000);
      
    } catch (err) {
      console.error('Compare error:', err);
    }
  };
  
  // Load preset
  const handleLoadPreset = (presetName) => {
    const preset = presets[presetName];
    if (Array.isArray(preset)) {
      preset.forEach(p => handleAddExperiment({
        ...p.config,
        name: p.name
      }));
    } else if (preset) {
      handleAddExperiment({
        ...preset.config,
        name: preset.name
      });
    }
  };
  
  const completedCount = experiments.filter(e => e.status === 'completed').length;
  const pendingCount = experiments.filter(e => e.status === 'pending').length;
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">Batch Experiments</h3>
          <p className="text-sm text-slate-500">
            {experiments.length} experiments • {completedCount} completed • {pendingCount} pending
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowNewForm(true)}
            className="btn-primary"
          >
            <Plus size={16} /> New Experiment
          </button>
          {pendingCount > 0 && (
            <button
              onClick={handleRunAll}
              disabled={isRunning}
              className="btn-secondary"
            >
              <Play size={16} /> Run All ({pendingCount})
            </button>
          )}
          {completedCount >= 2 && (
            <button
              onClick={handleCompare}
              className="btn-secondary"
            >
              <BarChart3 size={16} /> Compare
            </button>
          )}
        </div>
      </div>
      
      {/* Presets */}
      <div className="flex gap-2 flex-wrap">
        <span className="text-sm text-slate-500 py-1">Load preset:</span>
        {Object.keys(presets).map(name => (
          <button
            key={name}
            onClick={() => handleLoadPreset(name)}
            className="px-3 py-1 text-xs bg-slate-100 hover:bg-slate-200 rounded-full text-slate-700"
          >
            {name.replace(/_/g, ' ')}
          </button>
        ))}
      </div>
      
      {/* Experiment Grid */}
      {experiments.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {experiments.map(exp => (
            <ExperimentCard
              key={exp.id}
              experiment={exp}
              onRun={handleRunExperiment}
              onDelete={handleDelete}
              isRunning={isRunning}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-slate-50 rounded-lg border-2 border-dashed border-slate-200">
          <Activity size={40} className="mx-auto text-slate-400 mb-3" />
          <p className="text-slate-600">No experiments yet</p>
          <p className="text-sm text-slate-400 mt-1">Add experiments or load a preset to get started</p>
        </div>
      )}
      
      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-slate-800">Comparison Results</h4>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ComparisonChart experiments={comparison.experiments} />
            <RankingTable comparison={comparison} />
          </div>
        </div>
      )}
      
      {/* New Experiment Form Modal */}
      {showNewForm && (
        <NewExperimentForm
          onAdd={handleAddExperiment}
          onClose={() => setShowNewForm(false)}
        />
      )}
    </div>
  );
}
