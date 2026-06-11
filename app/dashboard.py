import os
import time
import hashlib
import json
import joblib
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# Initialize authentication session states early
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "auth_username" not in st.session_state:
    st.session_state.auth_username = ""

# 🎨 Professional Web Page Layout Configuration
st.set_page_config(
    page_title="AegisMind | Industrial Predictive Radar",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded" if st.session_state.authenticated else "collapsed"
)

# User Database Helper Functions
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)
    except Exception as e:
        st.error(f"Error saving user data: {e}")

def hash_password(password, salt="aegis_salt_993"):
    hash_obj = hashlib.sha256()
    hash_obj.update((password + salt).encode('utf-8'))
    return hash_obj.hexdigest()

def create_user(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    users[username] = hash_password(password)
    save_users(users)
    return True, "Operator account registered successfully."

def verify_user(username, password):
    users = load_users()
    if username not in users:
        return False
    return users[username] == hash_password(password)

ALARM_WAV_B64 = "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"

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
    
    /* Authentication Panel */
    .auth-title {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
        background: linear-gradient(135deg, #f3f4f6 30%, #a855f7) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        margin-bottom: 5px !important;
        text-align: center !important;
    }
    .auth-subtitle {
        font-size: 0.85rem !important;
        color: #9ca3af !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        margin-bottom: 25px !important;
        text-align: center !important;
    }
    .auth-card {
        background: rgba(13, 17, 28, 0.75) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 40px !important;
        box-shadow: 0 20px 50px -15px rgba(0,0,0,0.8), 0 0 30px rgba(168, 85, 247, 0.12) !important;
        margin-top: 50px !important;
    }
    
    /* Animations */
    @keyframes pulse-border-red {
        0%, 100% { border-color: rgba(239, 68, 68, 0.2); }
        50% { border-color: rgba(239, 68, 68, 0.6); box-shadow: 0 0 20px rgba(239, 68, 68, 0.3); }
    }
    </style>
""", unsafe_allow_html=True)

# 🔒 ACCESS CONTROL / ROUTING GATEWAY
if not st.session_state.authenticated:
    col_l, col_c, col_r = st.columns([1, 1.6, 1])
    with col_c:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<h1 class="auth-title">🛡️ AEGIS-MIND</h1>', unsafe_allow_html=True)
        st.markdown('<p class="auth-subtitle">Industrial Prediction Gateway</p>', unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔒 Secure Login", "📝 Operator Registration"])
        
        with tab_login:
            login_user = st.text_input("Operator Username", key="login_user_input", placeholder="Enter username")
            login_pass = st.text_input("Security Access Code", type="password", key="login_pass_input", placeholder="••••••••")
            
            if st.button("Authorize Access", use_container_width=True):
                if not login_user or not login_pass:
                    st.error("Please fill in all operator identification credentials.")
                elif verify_user(login_user, login_pass):
                    st.session_state.authenticated = True
                    st.session_state.auth_username = login_user
                    st.success("Authorization granted. Initializing AegisMind Radar...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Access denied. Invalid operator credentials.")
                    
        with tab_register:
            reg_user = st.text_input("New Operator Username", key="reg_user_input", placeholder="Choose username")
            reg_pass = st.text_input("New Security Access Code", type="password", key="reg_pass_input", placeholder="At least 6 characters")
            reg_confirm = st.text_input("Confirm Access Code", type="password", key="reg_confirm_input", placeholder="Re-enter access code")
            
            if st.button("Register Operator", use_container_width=True):
                if not reg_user or not reg_pass:
                    st.error("Username and access code are required.")
                elif reg_pass != reg_confirm:
                    st.error("Access codes do not match.")
                elif len(reg_pass) < 6:
                    st.error("Access code must be at least 6 characters.")
                else:
                    success, msg = create_user(reg_user, reg_pass)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.auth_username = reg_user
                        st.success(f"Registration complete. Welcome {reg_user}!")
                        time.sleep(0.8)
                        st.rerun()
                    else:
                        st.error(msg)
                        
        st.markdown('</div>', unsafe_allow_html=True)
    # Stop rendering the rest of the app
    st.stop()


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
        </div>
        <audio id="alarm-audio" autoplay loop>
            <source src="data:audio/wav;base64,{ALARM_WAV_B64}" type="audio/wav">
        </audio>
        <script>
            var audio = document.getElementById("alarm-audio");
            if (audio) {{
                audio.play().catch(function(error) {{
                    console.log("Autoplay blocked. Registering interaction listener...");
                    var playAudio = function() {{
                        audio.play().then(function() {{
                            console.log("Audio playing successfully.");
                            document.removeEventListener('click', playAudio);
                            document.removeEventListener('touchstart', playAudio);
                        }});
                    }};
                    document.addEventListener('click', playAudio);
                    document.addEventListener('touchstart', playAudio);
                }});
            }}
        </script>
        """, unsafe_allow_html=True)
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

# 🔒 Sidebar Operator Controls & Logout
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Authorized Operator:** `{st.session_state.auth_username}`")
if st.sidebar.button("Logout Session", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.auth_username = ""
    # Reset history
    st.session_state.df_history = pd.DataFrame(columns=[
        'Timestamp', 'Air_Temp', 'Proc_Temp', 'Speed', 'Torque', 'Tool_Wear', 'Risk_Prob', 'Anomaly_Score'
    ])
    st.rerun()

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