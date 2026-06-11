import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="AegisMind Live Hybrid Radar",
    description="Production-Grade Leakage-Proof Isolation Forest + XGBoost Gateway.",
    version="10.0.0"
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "machine_failure_model.joblib")

# 🔒 Safely unpack the four-part production champion artifact
if os.path.exists(MODEL_PATH):
    payload = joblib.load(MODEL_PATH)
    scaler = payload['scaler']
    anomaly_extractor = payload['anomaly_extractor']
    core_predictor = payload['core_predictor']
    optimal_threshold = payload['optimal_threshold']
else:
    raise RuntimeError(f"⚠️ Production Error: Hybrid model artifact missing at {MODEL_PATH}")

TELEMETRY_HISTORY: List[dict] = []
MAX_HISTORY_LEN = 10

class MachineTelemetry(BaseModel):
    air_temperature_k: float
    process_temperature_k: float
    rotational_speed_rpm: float
    torque_nm: float
    tool_wear_min: float

@app.post("/predict")
def predict_machine_status(telemetry: MachineTelemetry):
    global TELEMETRY_HISTORY
    try:
        current_snapshot = telemetry.model_dump()
        TELEMETRY_HISTORY.append(current_snapshot)
        
        if len(TELEMETRY_HISTORY) > MAX_HISTORY_LEN:
            TELEMETRY_HISTORY.pop(0)
            
        history_df = pd.DataFrame(TELEMETRY_HISTORY)
        history_df['temp_delta_k'] = history_df['process_temperature_k'] - history_df['air_temperature_k']
        
        # ⏳ Real-time incremental sequence parsing (Time-Aware context)
        if len(history_df) > 1:
            torque_velocity = float(history_df['torque_nm'].diff(periods=1).iloc[-1])
        else:
            torque_velocity = 0.0
            
        if len(history_df) >= 2:
            thermal_rolling_std = float(history_df['temp_delta_k'].tail(5).std())
            if pd.isna(thermal_rolling_std):
                thermal_rolling_std = 0.0
        else:
            thermal_rolling_std = 0.0
            
        temp_delta = current_snapshot['process_temperature_k'] - current_snapshot['air_temperature_k']
        power_factor = current_snapshot['rotational_speed_rpm'] * current_snapshot['torque_nm']
        tool_wear_stress = current_snapshot['tool_wear_min'] * current_snapshot['torque_nm']
        thermal_acceleration = temp_delta ** 2
        machine_volatility = tool_wear_stress / (current_snapshot['rotational_speed_rpm'] + 1e-5)
        
        feature_names = [
            'air_temperature_k', 'process_temperature_k', 'rotational_speed_rpm', 
            'torque_nm', 'tool_wear_min', 'temp_delta_k', 'mechanical_power_factor',
            'tool_wear_stress_index', 'thermal_strain_acceleration', 'machine_volatility_index',
            'torque_velocity', 'thermal_rolling_std'
        ]
        
        # Create base features dataframe
        base_features_df = pd.DataFrame([[
            current_snapshot['air_temperature_k'],
            current_snapshot['process_temperature_k'],
            current_snapshot['rotational_speed_rpm'],
            current_snapshot['torque_nm'],
            current_snapshot['tool_wear_min'],
            temp_delta,
            power_factor,
            tool_wear_stress,
            thermal_acceleration,
            machine_volatility,
            torque_velocity,
            thermal_rolling_std
        ]], columns=feature_names)
        
        # 🛡️ STEP 1: Extract the anomaly score incrementally without leakage
        base_features_df['unsupervised_anomaly_score'] = anomaly_extractor.score_samples(base_features_df)
        
        # 🛡️ STEP 2: Scale and pass to the core XGBoost predictor
        input_scaled = scaler.transform(base_features_df)
        raw_probability = float(core_predictor.predict_proba(input_scaled)[0][1])
        
        # Enforce our verified hybrid threshold boundary
        if raw_probability >= optimal_threshold:
            decision_label = 1
            status_message = "ALERT: Hybrid engine isolated a validated risk pattern!"
        else:
            decision_label = 0
            status_message = "Operational Status: Nominal"
            
        return {
            "prediction_status": status_message,
            "failure_binary_label": decision_label,
            "calculated_failure_probability": round(raw_probability * 100, 2),
            "enforced_hybrid_threshold": f"{round(optimal_threshold * 100, 2)}%",
            "extracted_metrics": {
                "live_anomaly_score": round(float(base_features_df['unsupervised_anomaly_score'].iloc[0]), 4),
                "live_torque_velocity": round(torque_velocity, 4),
                "live_thermal_rolling_std": round(thermal_rolling_std, 4)
            }
        }
        
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Hybrid Core Exception: {str(err)}")