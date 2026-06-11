import os
import time
import joblib
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# 🎨 Professional Web Page Layout Configuration
st.set_page_config(
    page_title="AegisMind | Industrial Predictive Radar",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling to make it look like a high-end enterprise SaaS dashboard
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
    
    /* Global Background and Typography */
    .stApp {
        background-color: #070a0f !important;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(56, 20, 138, 0.15) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(94, 20, 138, 0.12) 0%, transparent 45%),
            radial-gradient(circle at 50% 50%, rgba(59, 130, 246, 0.08) 0%, transparent 60%) !important;
        background-attachment: fixed !important;
        color: #f3f4f6 !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Hide Streamlit default decoration headers */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    div[data-testid="stDecoration"] {
        background: transparent !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0b0d15 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
    
    /* Custom metric cards matching glassmorphism style */
    .metric-card {
        background: rgba(13, 17, 28, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-left: 5px solid #a855f7 !important;
        border-radius: 12px !important;
        padding: 22px !important;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.6) !important;
        margin-bottom: 12px !important;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: rgba(168, 85, 247, 0.3) !important;
    }
    
    .alert-card {
        background: rgba(127, 29, 29, 0.2) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
        border-left: 5px solid #ef4444 !important;
        border-radius: 12px !important;
        padding: 22px !important;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.7), 0 0 20px rgba(239, 68, 68, 0.15) !important;
        margin-bottom: 12px !important;
        animation: pulse-border-red 2s infinite ease-in-out !important;
    }
    
    .success-card {
        background: rgba(20, 83, 45, 0.15) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(34, 197, 94, 0.2) !important;
        border-left: 5px solid #22c55e !important;
        border-radius: 12px !important;
        padding: 22px !important;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.6) !important;
        margin-bottom: 12px !important;
    }
    
    /* Preset button styling */
    .preset-btn {
        margin-bottom: 8px !important;
    }
    
    /* Dataframe layout style */
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    /* Animations */
    @keyframes pulse-border-red {
        0%, 100% { border-color: rgba(239, 68, 68, 0.2); }
        50% { border-color: rgba(239, 68, 68, 0.6); box-shadow: 0 0 20px rgba(239, 68, 68, 0.3); }
    }
    </style>
""", unsafe_allow_html=True)

# 🔒 Load the Core Hybrid Pipeline Component Safely
MODEL_PATH = os.path.join(os.path.dirname(__file__), "machine_failure_model.joblib")

@st.cache_resource
def load_production_pipeline():
    if os.path.exists(MODEL_PATH):
        payload = joblib.load(MODEL_PATH)
        return (payload['scaler'], payload['anomaly_extractor'], 
                payload['core_predictor'], payload['optimal_threshold'])
    else:
        st.error(f"❌ Structural Critical Error: Model binary missing at {MODEL_PATH}")
        return None, None, None, None

scaler, anomaly_extractor, core_predictor, optimal_threshold = load_production_pipeline()

# ⏳ Maintain stateful history queues across page re-runs
if "df_history" not in st.session_state:
    st.session_state.df_history = pd.DataFrame(columns=[
        'Timestamp', 'Air_Temp', 'Proc_Temp', 'Speed', 'Torque', 'Tool_Wear', 'Risk_Prob', 'Anomaly_Score'
    ])

# Initialize slider parameters in session state for dynamic changes (presets/simulator)
if "air_temp" not in st.session_state:
    st.session_state.air_temp = 300.0
if "proc_temp" not in st.session_state:
    st.session_state.proc_temp = 310.0
if "speed" not in st.session_state:
    st.session_state.speed = 1500.0
if "torque" not in st.session_state:
    st.session_state.torque = 40.0
if "tool_wear" not in st.session_state:
    st.session_state.tool_wear = 60.0

# 🏢 MAIN HEADER INTERFACE
st.title("🛡️ AEGIS-MIND INDUSTRIAL ANALYTICS PLATFORM")
st.markdown(f"**Deployment Environment:** Production-Edge-Node-01 | **Model Version:** Hybrid-Radar v10.0.0 (`XGBoost + Isolation Forest`)")
st.write("---")

# 🎛️ SIDEBAR CONTROL CONSOLE (Simulating Real-Time Edge Telemetry)
st.sidebar.header("🎛️ Telemetry Control Units")
st.sidebar.markdown("Manipulate these parameters to simulate active factory floor equipment states.")

# Preset handlers in sidebar
st.sidebar.subheader("Presets")
col_p1, col_p2 = st.sidebar.columns(2)
with col_p1:
    if st.button("Nominal Load", use_container_width=True):
        st.session_state.air_temp = 298.5
        st.session_state.proc_temp = 308.2
        st.session_state.speed = 1510.0
        st.session_state.torque = 38.5
        st.session_state.tool_wear = 24.0
        st.rerun()
        
    if st.button("High Friction", use_container_width=True):
        st.session_state.air_temp = 299.0
        st.session_state.proc_temp = 310.5
        st.session_state.speed = 1120.0
        st.session_state.torque = 82.5
        st.session_state.tool_wear = 120.0
        st.rerun()

with col_p2:
    if st.button("Thermal Stress", use_container_width=True):
        st.session_state.air_temp = 300.2
        st.session_state.proc_temp = 314.8
        st.session_state.speed = 1350.0
        st.session_state.torque = 48.0
        st.session_state.tool_wear = 95.0
        st.rerun()
        
    if st.button("Critical Wear", use_container_width=True):
        st.session_state.air_temp = 302.1
        st.session_state.proc_temp = 312.4
        st.session_state.speed = 1820.0
        st.session_state.torque = 55.0
        st.session_state.tool_wear = 235.0
        st.rerun()

st.sidebar.markdown("---")

# Live simulator mode toggle
is_live = st.sidebar.toggle("Live Telemetry Simulator Feed", value=False)
st.sidebar.markdown("---")

# Render sliders bound to session state
air_temp = st.sidebar.slider(
    "Ambient Air Temperature [K]", 295.0, 305.0, 
    value=st.session_state.air_temp, step=0.1, disabled=is_live
)
proc_temp = st.sidebar.slider(
    "Internal Process Temperature [K]", 304.0, 315.0, 
    value=st.session_state.proc_temp, step=0.1, disabled=is_live
)
speed = st.sidebar.slider(
    "Rotational Shaft Speed [RPM]", 1000.0, 2200.0, 
    value=st.session_state.speed, step=10.0, disabled=is_live
)
torque = st.sidebar.slider(
    "Operational Torque Load [Nm]", 0.0, 90.0, 
    value=st.session_state.torque, step=0.5, disabled=is_live
)
tool_wear = st.sidebar.slider(
    "Tool Wear Cumulative Runtime [Min]", 0.0, 250.0, 
    value=st.session_state.tool_wear, step=1.0, disabled=is_live
)

# Update session_state variables to keep them in sync with manual adjustments
if not is_live:
    st.session_state.air_temp = air_temp
    st.session_state.proc_temp = proc_temp
    st.session_state.speed = speed
    st.session_state.torque = torque
    st.session_state.tool_wear = tool_wear

# ⚙️ Real-Time Background Calculation Engine
temp_delta = st.session_state.proc_temp - st.session_state.air_temp
power_factor = st.session_state.speed * st.session_state.torque
tool_wear_stress = st.session_state.tool_wear * st.session_state.torque
thermal_acceleration = temp_delta ** 2
machine_volatility = tool_wear_stress / (st.session_state.speed + 1e-5)

# Extract sequential trend vectors based on previous operations history
if len(st.session_state.df_history) > 0:
    torque_velocity = st.session_state.torque - st.session_state.df_history['Torque'].iloc[-1]
    recent_deltas = list(st.session_state.df_history['Proc_Temp'] - st.session_state.df_history['Air_Temp'])[-4:]
    recent_deltas.append(temp_delta)
    thermal_rolling_std = np.std(recent_deltas) if len(recent_deltas) >= 2 else 0.0
else:
    torque_velocity = 0.0
    thermal_rolling_std = 0.0

# Shape input data vector to exactly match feature matrix specifications
feature_names = [
    'air_temperature_k', 'process_temperature_k', 'rotational_speed_rpm', 
    'torque_nm', 'tool_wear_min', 'temp_delta_k', 'mechanical_power_factor',
    'tool_wear_stress_index', 'thermal_strain_acceleration', 'machine_volatility_index',
    'torque_velocity', 'thermal_rolling_std'
]

input_df = pd.DataFrame([[
    st.session_state.air_temp, st.session_state.proc_temp, st.session_state.speed, 
    st.session_state.torque, st.session_state.tool_wear, temp_delta,
    power_factor, tool_wear_stress, thermal_acceleration, machine_volatility,
    torque_velocity, thermal_rolling_std
]], columns=feature_names)

# Execute Safe Machine Learning Logic Steps
raw_anomaly_score = float(anomaly_extractor.score_samples(input_df)[0])
input_df['unsupervised_anomaly_score'] = raw_anomaly_score

input_scaled = scaler.transform(input_df)
failure_probability = float(core_predictor.predict_proba(input_scaled)[0][1])
is_breached = failure_probability >= optimal_threshold

# Save records into stateful memory queue for chart plotting
new_record = pd.DataFrame([{
    'Timestamp': datetime.now().strftime('%H:%M:%S'),
    'Air_Temp': st.session_state.air_temp, 
    'Proc_Temp': st.session_state.proc_temp, 
    'Speed': st.session_state.speed,
    'Torque': st.session_state.torque, 
    'Tool_Wear': st.session_state.tool_wear, 
    'Risk_Prob': round(failure_probability * 100, 2),
    'Anomaly_Score': round(raw_anomaly_score, 4)
}])
st.session_state.df_history = pd.concat([st.session_state.df_history, new_record], ignore_index=True).tail(20)


# 📊 EXECUTIVE STATUS PANELS
col1, col2, col3, col4 = st.columns(4)

with col1:
    if is_breached:
        st.markdown(f"""<div class='alert-card'>
            <h4 style='color:#ef4444;margin:0;font-size:0.8rem;text-transform:uppercase;letter-spacing:1px;'>⚠️ CRITICAL ALARM</h4>
            <h2 style='margin:10px 0;font-size:1.8rem;font-weight:700;'>BREACH</h2>
            <p style='margin:0;font-size:12px;color:rgba(255,255,255,0.7);'>Asset requires immediate inspection.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class='success-card'>
            <h4 style='color:#22c55e;margin:0;font-size:0.8rem;text-transform:uppercase;letter-spacing:1px;'>🟢 SYSTEM HEALTH</h4>
            <h2 style='margin:10px 0;font-size:1.8rem;font-weight:700;'>NOMINAL</h2>
            <p style='margin:0;font-size:12px;color:rgba(255,255,255,0.7);'>Equipment operating normally.</p>
        </div>""", unsafe_allow_html=True)

with col2:
    prob_pct = round(failure_probability * 100, 1)
    card_class = 'alert-card' if is_breached else 'metric-card'
    st.markdown(f"""<div class='{card_class}'>
        <h4 style='color:#a855f7;margin:0;font-size:0.8rem;text-transform:uppercase;letter-spacing:1px;'>📊 PROBABILITY VECTOR</h4>
        <h2 style='margin:10px 0;font-size:1.8rem;font-weight:700;'>{prob_pct}%</h2>
        <p style='margin:0;font-size:12px;color:rgba(255,255,255,0.7);'>Verified Boundary: {round(optimal_threshold*100, 1)}%</p>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""<div class='metric-card' style='border-left-color: #06b6d4 !important;'>
        <h4 style='color:#06b6d4;margin:0;font-size:0.8rem;text-transform:uppercase;letter-spacing:1px;'>📡 ISOLATION RADAR</h4>
        <h2 style='margin:10px 0;font-size:1.8rem;font-weight:700;'>{round(raw_anomaly_score, 3)}</h2>
        <p style='margin:0;font-size:12px;color:rgba(255,255,255,0.7);'>Unsupervised Anomaly Score</p>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""<div class='metric-card' style='border-left-color: #f59e0b !important;'>
        <h4 style='color:#f59e0b;margin:0;font-size:0.8rem;text-transform:uppercase;letter-spacing:1px;'>⚙️ STRUCTURAL STRESS</h4>
        <h2 style='margin:10px 0;font-size:1.8rem;font-weight:700;'>{int(tool_wear_stress)}</h2>
        <p style='margin:0;font-size:12px;color:rgba(255,255,255,0.7);'>Tool Wear × Torque Index</p>
    </div>""", unsafe_allow_html=True)


# 📈 ANALYTICS AND HISTORICAL LINE GRAPHS SECTION
st.write("### 📈 Time-Series Threat Assessment")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.write("**Real-Time Risk Propagation Loop (%)**")
    fig_risk = go.Figure()
    fig_risk.add_trace(go.Scatter(
        x=st.session_state.df_history['Timestamp'], 
        y=st.session_state.df_history['Risk_Prob'],
        mode='lines+markers', name='Failure Risk', 
        line=dict(color='#a855f7', width=3),
        marker=dict(color='#c084fc', size=6)
    ))
    # Add horizontal threshold boundary line
    fig_risk.add_shape(type="line", x0=0, y0=optimal_threshold*100, x1=1, y1=optimal_threshold*100,
                       xsizemode="scaled", ysizemode="scaled",
                       line=dict(color="#ef4444", width=2, dash="dash"))
    fig_risk.update_layout(
        template="plotly_dark", 
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=10, b=20), 
        height=280,
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=True),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=True, range=[0, 100]),
        showlegend=False
    )
    st.plotly_chart(fig_risk, width='stretch')

with chart_col2:
    st.write("**Latent Space Structural Anomaly Horizon**")
    fig_score = go.Figure()
    fig_score.add_trace(go.Scatter(
        x=st.session_state.df_history['Timestamp'], 
        y=st.session_state.df_history['Anomaly_Score'],
        mode='lines', fill='tozeroy', name='Radar Score', 
        line=dict(color='#06b6d4', width=2),
        fillcolor='rgba(6, 182, 212, 0.12)'
    ))
    fig_score.update_layout(
        template="plotly_dark", 
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=10, b=20), 
        height=280,
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=True),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=True),
        showlegend=False
    )
    st.plotly_chart(fig_score, width='stretch')

# 📋 EDGE METRICS DATA ARCHIVE
st.write("### 📋 Recent Edge Diagnostic Telemetry Log")
st.dataframe(
    st.session_state.df_history.iloc[::-1], 
    width='stretch',
    hide_index=True
)

# ⏳ Live Mode Simulation Random Walk Loop
if is_live:
    time.sleep(1.0)
    # Perform random walks on the variables
    st.session_state.air_temp = float(np.clip(st.session_state.air_temp + np.random.uniform(-0.15, 0.15), 295.0, 305.0))
    st.session_state.proc_temp = float(np.clip(st.session_state.proc_temp + np.random.uniform(-0.25, 0.25), 304.0, 315.0))
    st.session_state.speed = float(np.clip(st.session_state.speed + np.random.randint(-40, 40), 1000.0, 2200.0))
    st.session_state.torque = float(np.clip(st.session_state.torque + np.random.uniform(-1.5, 1.5), 0.0, 90.0))
    st.session_state.tool_wear = float(np.clip(st.session_state.tool_wear + np.random.uniform(0.5, 1.5), 0.0, 250.0))
    st.rerun()