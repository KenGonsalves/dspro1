import os
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
    .main { background-color: #0e1117; }
    .metric-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #3b82f6;
        margin-bottom: 10px;
    }
    .alert-card {
        background-color: #7f1d1d;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ef4444;
        margin-bottom: 10px;
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

# 🏢 MAIN HEADER INTERFACE
st.title("🛡️ AEGIS-MIND INDUSTRIAL ANALYTICS PLATFORM")
st.markdown(f"**Deployment Environment:** Production-Edge-Node-01 | **Model Version:** Hybrid-Radar v10.0.0 (`XGBoost + Isolation Forest`)")
st.write("---")

# 🎛️ SIDEBAR CONTROL CONSOLE (Simulating Real-Time Edge Telemetry)
st.sidebar.header("🎛️ Telemetry Control Units")
st.sidebar.markdown("Manipulate these parameters to simulate active factory floor equipment states.")

air_temp = st.sidebar.slider("Ambient Air Temperature [K]", 295.0, 305.0, 300.0, 0.1)
proc_temp = st.sidebar.slider("Internal Process Temperature [K]", 304.0, 315.0, 310.0, 0.1)
speed = st.sidebar.slider("Rotational Shaft Speed [RPM]", 1000.0, 2200.0, 1500.0, 10.0)
torque = st.sidebar.slider("Operational Torque Load [Nm]", 0.0, 90.0, 40.0, 0.5)
tool_wear = st.sidebar.slider("Tool Wear Cumulative Runtime [Min]", 0.0, 250.0, 60.0, 1.0)

# ⚙️ Real-Time Background Calculation Engine
temp_delta = proc_temp - air_temp
power_factor = speed * torque
tool_wear_stress = tool_wear * torque
thermal_acceleration = temp_delta ** 2
machine_volatility = tool_wear_stress / (speed + 1e-5)

# Extract sequential trend vectors based on previous operations history
if len(st.session_state.df_history) > 0:
    torque_velocity = torque - st.session_state.df_history['Torque'].iloc[-1]
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
    air_temp, proc_temp, speed, torque, tool_wear, temp_delta,
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
    'Air_Temp': air_temp, 'Proc_Temp': proc_temp, 'Speed': speed,
    'Torque': torque, 'Tool_Wear': tool_wear, 'Risk_Prob': round(failure_probability * 100, 2),
    'Anomaly_Score': round(raw_anomaly_score, 4)
}])
st.session_state.df_history = pd.concat([st.session_state.df_history, new_record], ignore_index=True).tail(20)


# 📊 EXECUTIVE STATUS PANELS
col1, col2, col3, col4 = st.columns(4)

with col1:
    if is_breached:
        st.markdown(f"""<div class='alert-card'>
            <h4 style='color:#ef4444;margin:0;'>⚠️ CRITICAL ALARM</h4>
            <h2 style='margin:10px 0;'>BREACH</h2>
            <p style='margin:0;font-size:12px;'>Asset requires immediate inspection.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class='metric-card'>
            <h4 style='color:#10b981;margin:0;'>🟢 SYSTEM HEALTH</h4>
            <h2 style='margin:10px 0;'>NOMINAL</h2>
            <p style='margin:0;font-size:12px;'>Equipment operating normally.</p>
        </div>""", unsafe_allow_html=True)

with col2:
    prob_pct = round(failure_probability * 100, 1)
    st.markdown(f"""<div class='metric-card'>
        <h4 style='color:#3b82f6;margin:0;'>📊 PROBABILITY VECTOR</h4>
        <h2 style='margin:10px 0;'>{prob_pct}%</h2>
        <p style='margin:0;font-size:12px;'>Verified Boundary: {round(optimal_threshold*100, 1)}%</p>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""<div class='metric-card'>
        <h4 style='color:#a855f7;margin:0;'>📡 ISOLATION RADAR</h4>
        <h2 style='margin:10px 0;'>{round(raw_anomaly_score, 3)}</h2>
        <p style='margin:0;font-size:12px;'>Unsupervised Anomaly Score</p>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""<div class='metric-card'>
        <h4 style='color:#eab308;margin:0;'>⚙️ STRUCTURAL STRESS</h4>
        <h2 style='margin:10px 0;'>{int(tool_wear_stress)}</h2>
        <p style='margin:0;font-size:12px;'>Tool Wear × Torque Index</p>
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
        mode='lines+markers', name='Failure Risk', line=dict(color='#3b82f6', width=3)
    ))
    fig_risk.add_shape(type="line", x0=0, y0=optimal_threshold*100, x1=1, y1=optimal_threshold*100,
                       xsizemode="scaled", ysizemode="scaled",
                       line=dict(color="Red", width=2, dash="dash"))
    fig_risk.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20), height=300)
    st.plotly_chart(fig_risk, use_container_width=True)

with chart_col2:
    st.write("**Latent Space Structural Anomaly Horizon**")
    fig_score = go.Figure()
    fig_score.add_trace(go.Scatter(
        x=st.session_state.df_history['Timestamp'], 
        y=st.session_state.df_history['Anomaly_Score'],
        mode='lines', fill='tozeroy', name='Radar Score', line=dict(color='#a855f7', width=2)
    ))
    fig_score.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20), height=300)
    st.plotly_chart(fig_score, use_container_width=True)

# 📋 EDGE METRICS DATA ARCHIVE
st.write("### 📋 Recent Edge Diagnostic Telemetry Log")
st.dataframe(
    st.session_state.df_history.iloc[::-1], 
    use_container_width=True,
    hide_index=True
)