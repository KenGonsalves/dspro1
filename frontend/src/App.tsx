import { useState, useEffect, useRef } from 'react'
import { 
  Activity, 
  Cpu, 
  AlertTriangle, 
  CheckCircle, 
  Sliders, 
  Download, 
  RefreshCw, 
  Gauge, 
  Wrench,
  TrendingUp,
  Server
} from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  ReferenceLine
} from 'recharts'

interface TelemetryData {
  air_temperature_k: number
  process_temperature_k: number
  rotational_speed_rpm: number
  torque_nm: number
  tool_wear_min: number
}

interface PredictionResponse {
  prediction_status: string
  failure_binary_label: number
  calculated_failure_probability: number
  enforced_hybrid_threshold: string
  extracted_metrics: {
    live_anomaly_score: number
    live_torque_velocity: number
    live_thermal_rolling_std: number
  }
}

interface HistoryRecord extends TelemetryData {
  timestamp: string
  calculated_failure_probability: number
  live_anomaly_score: number
  failure_binary_label: number
  prediction_status: string
}

const PRESETS = {
  nominal: {
    name: 'Nominal Load',
    desc: 'Normal operating conditions on the factory floor.',
    data: { air_temperature_k: 298.5, process_temperature_k: 308.2, rotational_speed_rpm: 1510, torque_nm: 38.5, tool_wear_min: 24 }
  },
  thermal: {
    name: 'Thermal Stress',
    desc: 'Process temperature rises rapidly relative to ambient temperature.',
    data: { air_temperature_k: 300.2, process_temperature_k: 314.8, rotational_speed_rpm: 1350, torque_nm: 48.0, tool_wear_min: 95 }
  },
  overtorque: {
    name: 'High Friction Risk',
    desc: 'Rotational speed drops under high torque loads, creating mechanical friction.',
    data: { air_temperature_k: 299.0, process_temperature_k: 310.5, rotational_speed_rpm: 1120, torque_nm: 82.5, tool_wear_min: 120 }
  },
  criticalwear: {
    name: 'Critical Tool Wear',
    desc: 'Cumulative runtime reaches warning levels, increasing structural load.',
    data: { air_temperature_k: 302.1, process_temperature_k: 312.4, rotational_speed_rpm: 1820, torque_nm: 55.0, tool_wear_min: 235 }
  }
}

export default function App() {
  // Telemetry Sliders state
  const [airTemp, setAirTemp] = useState<number>(300.0)
  const [procTemp, setProcTemp] = useState<number>(310.0)
  const [speed, setSpeed] = useState<number>(1500.0)
  const [torque, setTorque] = useState<number>(40.0)
  const [toolWear, setToolWear] = useState<number>(60.0)

  // Simulation controls
  const [isLiveMode, setIsLiveMode] = useState<boolean>(false)
  const [optimalThreshold, setOptimalThreshold] = useState<number>(0.4312) // Default placeholder, will load from backend
  const [isConnected, setIsConnected] = useState<boolean>(true)
  const [isFetching, setIsFetching] = useState<boolean>(false)

  // Prediction output
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null)
  
  // History queue for charts (last 20 ticks)
  const [history, setHistory] = useState<HistoryRecord[]>([])

  const liveModeRef = useRef<boolean>(isLiveMode)
  const timerRef = useRef<any>(null)

  // Sync ref to avoid closure issues in intervals
  useEffect(() => {
    liveModeRef.current = isLiveMode
  }, [isLiveMode])

  // Load backend info on mount
  useEffect(() => {
    fetch('/info')
      .then(res => {
        if (!res.ok) throw new Error('Info endpoint offline')
        return res.json()
      })
      .then(data => {
        if (data.optimal_threshold) {
          setOptimalThreshold(data.optimal_threshold)
        }
      })
      .catch(err => {
        console.warn('Failed to load info from FastAPI:', err)
        setIsConnected(false)
      })
  }, [])

  // Query /predict
  const queryPrediction = async (telemetry: TelemetryData) => {
    setIsFetching(true)
    try {
      const res = await fetch('/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(telemetry)
      })
      if (!res.ok) throw new Error('Prediction API error')
      
      const data: PredictionResponse = await res.json()
      setPrediction(data)
      setIsConnected(true)

      // Add to history
      const now = new Date()
      const timeStr = now.toTimeString().split(' ')[0]
      const newRecord: HistoryRecord = {
        ...telemetry,
        timestamp: timeStr,
        calculated_failure_probability: data.calculated_failure_probability,
        live_anomaly_score: data.extracted_metrics.live_anomaly_score,
        failure_binary_label: data.failure_binary_label,
        prediction_status: data.prediction_status
      }

      setHistory(prev => {
        const next = [...prev, newRecord]
        if (next.length > 20) {
          next.shift()
        }
        return next
      })
    } catch (err) {
      console.error(err)
      setIsConnected(false)
    } finally {
      setIsFetching(false)
    }
  }

  // Trigger prediction when inputs change (throttled when manually adjusting)
  useEffect(() => {
    if (!isLiveMode) {
      const delayDebounce = setTimeout(() => {
        queryPrediction({
          air_temperature_k: airTemp,
          process_temperature_k: procTemp,
          rotational_speed_rpm: speed,
          torque_nm: torque,
          tool_wear_min: toolWear
        })
      }, 250) // 250ms debounce for sliders
      return () => clearTimeout(delayDebounce)
    }
  }, [airTemp, procTemp, speed, torque, toolWear, isLiveMode])

  // Live Mode Simulation loop
  useEffect(() => {
    if (isLiveMode) {
      // Setup interval to query and walk values
      timerRef.current = setInterval(() => {
        setAirTemp(prev => {
          const delta = (Math.random() - 0.5) * 0.4
          return Math.min(305.0, Math.max(295.0, Number((prev + delta).toFixed(1))))
        })
        setProcTemp(prev => {
          const delta = (Math.random() - 0.5) * 0.6
          return Math.min(315.0, Math.max(304.0, Number((prev + delta).toFixed(1))))
        })
        setSpeed(prev => {
          const delta = (Math.random() - 0.5) * 60
          return Math.min(2200.0, Math.max(1000.0, Math.round(prev + delta)))
        })
        setTorque(prev => {
          const delta = (Math.random() - 0.5) * 4.0
          return Math.min(90.0, Math.max(0.0, Number((prev + delta).toFixed(1))))
        })
        setToolWear(prev => {
          const delta = 0.5 + Math.random() * 0.5
          let next = prev + delta
          if (next > 250.0) next = 0.0 // reset on full wear
          return Number(next.toFixed(1))
        })
      }, 1000)
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [isLiveMode])

  // Trigger query immediately when walking variables change in Live Mode
  useEffect(() => {
    if (isLiveMode) {
      queryPrediction({
        air_temperature_k: airTemp,
        process_temperature_k: procTemp,
        rotational_speed_rpm: speed,
        torque_nm: torque,
        tool_wear_min: toolWear
      })
    }
  }, [airTemp, procTemp, speed, torque, toolWear])

  // Apply a preset
  const applyPreset = (presetKey: keyof typeof PRESETS) => {
    setIsLiveMode(false)
    const preset = PRESETS[presetKey].data
    setAirTemp(preset.air_temperature_k)
    setProcTemp(preset.process_temperature_k)
    setSpeed(preset.rotational_speed_rpm)
    setTorque(preset.torque_nm)
    setToolWear(preset.tool_wear_min)
  }

  // Export history to CSV
  const exportCSV = () => {
    if (history.length === 0) return
    const headers = [
      'Timestamp',
      'Ambient Air Temp (K)',
      'Process Temp (K)',
      'Rotational Speed (RPM)',
      'Torque (Nm)',
      'Tool Wear (Min)',
      'Failure Probability (%)',
      'Anomaly Score',
      'Status'
    ]
    const rows = history.map(h => [
      h.timestamp,
      h.air_temperature_k,
      h.process_temperature_k,
      h.rotational_speed_rpm,
      h.torque_nm,
      h.tool_wear_min,
      h.calculated_failure_probability,
      h.live_anomaly_score,
      h.failure_binary_label === 1 ? 'BREACH' : 'NOMINAL'
    ])
    
    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers.join(','), ...rows.map(e => e.join(','))].join('\n')
    
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement("a")
    link.setAttribute("href", encodedUri)
    link.setAttribute("download", `aegismind_telemetry_${Date.now()}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Derived calculations
  const toolWearStress = Math.round(toolWear * torque)
  const isBreached = prediction ? prediction.failure_binary_label === 1 : false
  const failureProb = prediction ? prediction.calculated_failure_probability : 0.0
  const anomalyScore = prediction ? prediction.extracted_metrics.live_anomaly_score : 0.0

  return (
    <div className="dashboard-wrapper">
      {/* HEADER HUD */}
      <header className="header-hud">
        <div className="header-logo-container">
          <Activity className="logo-icon-glow" size={32} />
          <div>
            <h1 className="header-title-main">AegisMind</h1>
            <p style={{ fontSize: '0.75rem', letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
              Industrial Predictive Radar
            </p>
          </div>
        </div>

        <div className="header-meta-details">
          <div className="meta-pill">
            <Server size={14} className="kpi-icon" />
            Node: <span>Edge-Node-01</span>
          </div>
          <div className="meta-pill">
            <Cpu size={14} className="kpi-icon" />
            Model: <span>Hybrid v10.0.0</span>
          </div>
          <div className={`meta-pill ${isConnected ? 'live-status' : ''}`} style={{ borderColor: isConnected ? '' : 'var(--color-danger)' }}>
            {isConnected ? (
              <span>ONLINE</span>
            ) : (
              <span style={{ color: 'var(--color-danger)' }}>DISCONNECTED</span>
            )}
          </div>
        </div>
      </header>

      {/* DISCONNECTED WARNING ALERT */}
      {!isConnected && (
        <div className="glass-panel danger-status" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <AlertTriangle size={24} style={{ color: 'var(--color-danger)' }} />
          <div>
            <h4 style={{ color: 'var(--color-danger)', fontWeight: 600 }}>Connection Interrupted</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Could not communicate with the AegisMind live hybrid prediction gateway. Ensure FastAPI server is running on port 8000.
            </p>
          </div>
        </div>
      )}

      {/* EXECUTIVE KPI CARD PANELS */}
      <section className="hud-kpi-grid">
        {/* Status card */}
        <div className={`glass-panel kpi-card ${isBreached ? 'danger-glow danger-status' : 'nominal-glow'}`}>
          <div className="kpi-header">
            <span>System Health</span>
            {isBreached ? (
              <AlertTriangle className="kpi-icon" size={18} style={{ color: 'var(--color-danger)' }} />
            ) : (
              <CheckCircle className="kpi-icon" size={18} style={{ color: 'var(--color-success)' }} />
            )}
          </div>
          <div>
            <div className="kpi-value" style={{ color: isBreached ? 'var(--color-danger)' : 'var(--color-success)' }}>
              {isBreached ? 'BREACH' : 'NOMINAL'}
            </div>
            <div className="kpi-footer-note">
              {isBreached ? 'Immediate inspection required' : 'Equipment operating normally'}
            </div>
          </div>
        </div>

        {/* Probability card */}
        <div className="glass-panel kpi-card indigo-glow">
          <div className="kpi-header">
            <span>Failure Probability</span>
            <TrendingUp className="kpi-icon" size={18} style={{ color: 'var(--color-primary)' }} />
          </div>
          <div>
            <div className="kpi-value">
              {failureProb}
              <span className="unit">%</span>
            </div>
            <div className="kpi-footer-note" style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '0.25rem' }}>
              <span>Boundary: {Math.round(optimalThreshold * 10000) / 100}%</span>
              <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                <div 
                  style={{ 
                    width: `${Math.min(100, failureProb)}%`, 
                    height: '100%', 
                    background: failureProb >= optimalThreshold * 100 ? 'var(--color-danger)' : 'var(--color-primary)',
                    boxShadow: failureProb >= optimalThreshold * 100 ? '0 0 8px var(--color-danger)' : '0 0 8px var(--color-primary)',
                    transition: 'width 0.3s ease'
                  }} 
                />
              </div>
            </div>
          </div>
        </div>

        {/* Anomaly Radar card */}
        <div className="glass-panel kpi-card blue-glow">
          <div className="kpi-header">
            <span>Isolation Radar</span>
            <Gauge className="kpi-icon" size={18} style={{ color: 'var(--color-secondary)' }} />
          </div>
          <div>
            <div className="kpi-value">
              {anomalyScore.toFixed(4)}
            </div>
            <div className="kpi-footer-note">
              Unsupervised anomaly score index
            </div>
          </div>
        </div>

        {/* Structural Stress card */}
        <div className="glass-panel kpi-card amber-glow">
          <div className="kpi-header">
            <span>Structural Stress</span>
            <Wrench className="kpi-icon" size={18} style={{ color: 'var(--color-warning)' }} />
          </div>
          <div>
            <div className="kpi-value">
              {toolWearStress}
              <span className="unit">idx</span>
            </div>
            <div className="kpi-footer-note">
              Tool Wear × Torque stress index
            </div>
          </div>
        </div>
      </section>

      {/* MAIN LAYOUT GRID */}
      <main className="main-grid">
        {/* SIDEBAR telemetry console */}
        <section className="glass-panel">
          <div className="glass-panel-header">
            <h3 className="glass-panel-title">
              <Sliders size={18} /> Telemetry Console
            </h3>
            {isFetching && <RefreshCw size={14} className="kpi-icon" style={{ animation: 'spin 1s linear infinite' }} />}
          </div>

          <div className="glass-panel-content">
            {/* Ambient Air Temp */}
            <div className="slider-container">
              <div className="slider-info">
                <span className="slider-label">Ambient Air Temp</span>
                <span className="slider-value-readout">{airTemp.toFixed(1)} K</span>
              </div>
              <input 
                type="range" 
                min="295.0" 
                max="305.0" 
                step="0.1" 
                value={airTemp} 
                onChange={(e) => setAirTemp(parseFloat(e.target.value))} 
                disabled={isLiveMode}
                className="custom-slider"
              />
            </div>

            {/* Internal Process Temp */}
            <div className="slider-container">
              <div className="slider-info">
                <span className="slider-label">Process Temp</span>
                <span className="slider-value-readout">{procTemp.toFixed(1)} K</span>
              </div>
              <input 
                type="range" 
                min="304.0" 
                max="315.0" 
                step="0.1" 
                value={procTemp} 
                onChange={(e) => setProcTemp(parseFloat(e.target.value))} 
                disabled={isLiveMode}
                className="custom-slider"
              />
            </div>

            {/* Rotational Speed */}
            <div className="slider-container">
              <div className="slider-info">
                <span className="slider-label">Rotational Shaft Speed</span>
                <span className="slider-value-readout">{speed} RPM</span>
              </div>
              <input 
                type="range" 
                min="1000" 
                max="2200" 
                step="10" 
                value={speed} 
                onChange={(e) => setSpeed(parseInt(e.target.value))} 
                disabled={isLiveMode}
                className="custom-slider"
              />
            </div>

            {/* Torque */}
            <div className="slider-container">
              <div className="slider-info">
                <span className="slider-label">Operational Torque</span>
                <span className="slider-value-readout">{torque.toFixed(1)} Nm</span>
              </div>
              <input 
                type="range" 
                min="0.0" 
                max="90.0" 
                step="0.5" 
                value={torque} 
                onChange={(e) => setTorque(parseFloat(e.target.value))} 
                disabled={isLiveMode}
                className="custom-slider"
              />
            </div>

            {/* Tool Wear */}
            <div className="slider-container">
              <div className="slider-info">
                <span className="slider-label">Tool Wear Runtime</span>
                <span className="slider-value-readout">{toolWear.toFixed(0)} Min</span>
              </div>
              <input 
                type="range" 
                min="0.0" 
                max="250.0" 
                step="1.0" 
                value={toolWear} 
                onChange={(e) => setToolWear(parseFloat(e.target.value))} 
                disabled={isLiveMode}
                className="custom-slider"
              />
            </div>

            {/* Live mode toggle */}
            <div className="sim-toggle-container">
              <div className="toggle-label">
                <Activity size={16} style={{ color: isLiveMode ? 'var(--color-accent)' : 'var(--text-muted)' }} />
                <span>Live Feed Simulator</span>
              </div>
              <label className="toggle-switch">
                <input 
                  type="checkbox" 
                  checked={isLiveMode} 
                  onChange={(e) => setIsLiveMode(e.target.checked)} 
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            {/* Presets list */}
            <div style={{ marginTop: '1.5rem' }}>
              <h4 style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                Load Simulation Presets
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {(Object.keys(PRESETS) as Array<keyof typeof PRESETS>).map((key) => (
                  <button 
                    key={key} 
                    className="action-button" 
                    onClick={() => applyPreset(key)} 
                    style={{ fontSize: '0.8rem', width: '100%', justifyContent: 'flex-start', padding: '0.4rem 0.8rem' }}
                  >
                    <span style={{ fontWeight: 600 }}>{PRESETS[key].name}</span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginLeft: 'auto', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {PRESETS[key].desc}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* MAIN VIEWS - Charts & Table Logs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Charts section */}
          <section className="charts-grid">
            {/* Threat Probability chart */}
            <div className="glass-panel chart-card">
              <div className="glass-panel-header">
                <div>
                  <h3 className="glass-panel-title">Real-Time Risk Loop</h3>
                  <p className="chart-subtitle">Calculated system failure probability (%)</p>
                </div>
              </div>
              <div className="glass-panel-content chart-container-inner">
                {history.length === 0 ? (
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Awaiting telemetry records...
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="timestamp" stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                      <YAxis stroke="var(--text-muted)" domain={[0, 100]} style={{ fontSize: '0.75rem' }} />
                      <ChartTooltip 
                        contentStyle={{ background: 'var(--bg-surface)', borderColor: 'var(--border-light)', borderRadius: '6px' }}
                        labelClassName="mono"
                        itemStyle={{ color: 'var(--text-primary)' }}
                      />
                      <ReferenceLine y={optimalThreshold * 100} stroke="var(--color-danger)" strokeDasharray="5 5" label={{ value: 'Boundary', fill: 'var(--color-danger)', fontSize: 10, position: 'top' }} />
                      <Line 
                        type="monotone" 
                        dataKey="calculated_failure_probability" 
                        name="Failure Risk (%)" 
                        stroke="var(--color-primary)" 
                        strokeWidth={3} 
                        dot={{ r: 3, strokeWidth: 1 }} 
                        activeDot={{ r: 6 }} 
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            {/* Unsupervised Anomaly area chart */}
            <div className="glass-panel chart-card">
              <div className="glass-panel-header">
                <div>
                  <h3 className="glass-panel-title">Latent Anomaly Horizon</h3>
                  <p className="chart-subtitle">Isolation Forest anomaly score projection</p>
                </div>
              </div>
              <div className="glass-panel-content chart-container-inner">
                {history.length === 0 ? (
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Awaiting telemetry records...
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorAnomaly" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--color-secondary)" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="var(--color-secondary)" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="timestamp" stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                      <YAxis stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                      <ChartTooltip 
                        contentStyle={{ background: 'var(--bg-surface)', borderColor: 'var(--border-light)', borderRadius: '6px' }}
                        labelClassName="mono"
                        itemStyle={{ color: 'var(--text-primary)' }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="live_anomaly_score" 
                        name="Anomaly Index" 
                        stroke="var(--color-secondary)" 
                        fillOpacity={1} 
                        fill="url(#colorAnomaly)" 
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </section>

          {/* Diagnostic Log table */}
          <section className="glass-panel">
            <div className="glass-panel-header">
              <h3 className="glass-panel-title">
                Diagnostic Telemetry Archive
              </h3>
              {history.length > 0 && (
                <button className="action-button" onClick={exportCSV} style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}>
                  <Download size={14} /> Export CSV
                </button>
              )}
            </div>

            <div className="glass-panel-content" style={{ padding: '0 0 1rem 0' }}>
              <div className="table-container">
                <table className="diagnostic-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Air (K)</th>
                      <th>Process (K)</th>
                      <th>Speed (RPM)</th>
                      <th>Torque (Nm)</th>
                      <th>Wear (Min)</th>
                      <th>Risk (%)</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.length === 0 ? (
                      <tr>
                        <td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                          No diagnostic records registered. Move sliders or start the Live Simulator.
                        </td>
                      </tr>
                    ) : (
                      [...history].reverse().map((row, idx) => (
                        <tr key={idx}>
                          <td className="mono" style={{ color: 'var(--text-secondary)' }}>{row.timestamp}</td>
                          <td className="mono">{row.air_temperature_k.toFixed(1)}</td>
                          <td className="mono">{row.process_temperature_k.toFixed(1)}</td>
                          <td className="mono">{row.rotational_speed_rpm}</td>
                          <td className="mono">{row.torque_nm.toFixed(1)}</td>
                          <td className="mono">{row.tool_wear_min.toFixed(0)}</td>
                          <td className="mono" style={{ fontWeight: 600, color: row.calculated_failure_probability >= optimalThreshold * 100 ? 'var(--color-danger)' : 'var(--text-primary)' }}>
                            {row.calculated_failure_probability}%
                          </td>
                          <td>
                            <span className={`status-badge ${row.failure_binary_label === 1 ? 'breach' : 'nominal'}`}>
                              {row.failure_binary_label === 1 ? 'Breach' : 'Nominal'}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
