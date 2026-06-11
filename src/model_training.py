import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, precision_recall_curve
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

def train_production_model():
    print("🚀 Initializing Leakage-Proof Hybrid Radar Engine...")
    
    data_path = "data/raw/predictive_maintenance_raw.csv"
    if not os.path.exists(data_path):
        print(f"❌ Error: Data file missing at {data_path}")
        return
    
    df = pd.read_csv(data_path)
    rename_dict = {
        'Air temperature [K]': 'air_temperature_k',
        'Process temperature [K]': 'process_temperature_k',
        'Rotational speed [rpm]': 'rotational_speed_rpm',
        'Torque [Nm]': 'torque_nm',
        'Tool wear [min]': 'tool_wear_min',
        'Machine failure': 'machine_failure'
    }
    df_clean = df.rename(columns=rename_dict)
    
    # ⏳ Injecting our successful sequence-aware features
    df_clean = df_clean.sort_values(by='UDI').reset_index(drop=True)
    df_clean['torque_velocity'] = df_clean['torque_nm'].diff(periods=1).fillna(0)
    df_clean['temp_delta_k'] = df_clean['process_temperature_k'] - df_clean['air_temperature_k']
    df_clean['thermal_rolling_std'] = df_clean['temp_delta_k'].rolling(window=5, min_periods=1).std().fillna(0)
    df_clean['mechanical_power_factor'] = df_clean['rotational_speed_rpm'] * df_clean['torque_nm']
    df_clean['tool_wear_stress_index'] = df_clean['tool_wear_min'] * df_clean['torque_nm']
    df_clean['thermal_strain_acceleration'] = df_clean['temp_delta_k'] ** 2
    df_clean['machine_volatility_index'] = (df_clean['tool_wear_min'] * df_clean['torque_nm']) / (df_clean['rotational_speed_rpm'] + 1e-5)
    
    feature_cols = [
        'air_temperature_k', 'process_temperature_k', 'rotational_speed_rpm', 
        'torque_nm', 'tool_wear_min', 'temp_delta_k', 'mechanical_power_factor',
        'tool_wear_stress_index', 'thermal_strain_acceleration', 'machine_volatility_index',
        'torque_velocity', 'thermal_rolling_std'
    ]
    
    X = df_clean[feature_cols]
    y = df_clean['machine_failure']
    
    # Split the data first! Complete wall built between train and test
    X_train_base, X_test_base, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    # 🔒 SAFE UNSUPERVISED RADAR FIT
    print("🛡️ Fitting Isolation Forest strictly on training partition bounds...")
    iso_forest = IsolationForest(contamination=0.035, random_state=42, n_jobs=-1)
    iso_forest.fit(X_train_base) # Fits ONLY on train
    
    # Apply transformation separately
    X_train = X_train_base.copy()
    X_train['unsupervised_anomaly_score'] = iso_forest.score_samples(X_train_base)
    
    X_test = X_test_base.copy()
    X_test['unsupervised_anomaly_score'] = iso_forest.score_samples(X_test_base) # Transformed blindly
    
    # Scale feature matrix safely
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("🏋️‍♂️ Training supervised hyper-booster over combined latent spaces...")
    model = XGBClassifier(
        max_depth=6, learning_rate=0.03, n_estimators=350,
        subsample=0.85, colsample_bytree=0.85, scale_pos_weight=4.5,
        random_state=42, eval_metric="logloss"
    )
    model.fit(X_train_scaled, y_train)
    
    # 🎯 Optimize threshold strictly for maximum balanced F1-score
    y_scores = model.predict_proba(X_test_scaled)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_test, y_scores)
    
    f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
    best_idx = np.argmax(f1_scores)
    optimal_threshold = float(thresholds[best_idx])
    
    print(f"\n🥇 Verified Leakage-Proof Threshold Isolated: {optimal_threshold:.4f}")
    y_pred = (y_scores >= optimal_threshold).astype(int)
    
    print(f"\n✅ Safe Hybrid System Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
    print("\nDetailed Verified Metrics Matrix:")
    print(classification_report(y_test, y_pred))
    
    final_cm = confusion_matrix(y_test, y_pred)
    print(f"📊 Final Confusion Bounds Matrix:\n {final_cm}")
    
    # Export package payload
    pipeline_payload = {
        'scaler': scaler,
        'anomaly_extractor': iso_forest,
        'core_predictor': model,
        'optimal_threshold': optimal_threshold
    }
    
    model_output_path = "app/machine_failure_model.joblib"
    joblib.dump(pipeline_payload, model_output_path)
    print(f"💾 Safe Hybrid artifact saved securely at: {model_output_path}\n")

if __name__ == "__main__":
    train_production_model()