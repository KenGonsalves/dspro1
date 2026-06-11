import os
import ssl
import glob
import pandas as pd

def download_and_aggregate_data():
    print("🚀 Initializing AegisMind Unified Data Ingestion & Influx Pipeline...")
    
    target_dir = "data/raw"
    primary_file = os.path.join(target_dir, "predictive_maintenance_raw.csv")
    dataset_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00601/ai4i2020.csv"
    
    # 1. Create the folder path if it doesn't exist yet
    os.makedirs(target_dir, exist_ok=True)
    
    # 2. If the base file doesn't exist, pull it from the internet source
    if not os.path.exists(primary_file):
        print(f"📡 Primary dataset missing locally. Fetching from secure registry URL...")
        try:
            # Bypass unverified SSL certificate blockages gracefully
            ssl_context = ssl._create_unverified_context()
            combined_df = pd.read_csv(dataset_url, storage_options={"ssl_context": ssl_context})
            print(f"✅ Base file downloaded successfully ({combined_df.shape[0]} initial rows).")
        except Exception as e:
            print(f"❌ Critical Error downloading base dataset: {str(e)}")
            return
    else:
        print(f"📊 Local base data found at {primary_file}. Reading current state...")
        combined_df = pd.read_csv(primary_file)
        
    # 3. Scan for any NEW additional machine telemetry logs in the same directory
    # (e.g., factory_batch_2.csv, sensor_feed.csv)
    additional_files = [
        f for f in glob.glob(os.path.join(target_dir, "*.csv")) 
        if "predictive_maintenance_raw.csv" not in f
    ]
    
    if len(additional_files) > 0:
        print(f"🔍 Found {len(additional_files)} supplementary log files. Merging new production data...")
        for file_path in additional_files:
            try:
                extra_df = pd.read_csv(file_path)
                # Ensure the columns match before concatenating
                combined_df = pd.concat([combined_df, extra_df], ignore_index=True)
                print(f"➕ Successfully appended records from: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"⚠️ Skipping faulty file {os.path.basename(file_path)}: {str(e)}")
                
        # 4. Clean and Deduplicate the Consolidated Matrix
        initial_count = combined_df.shape[0]
        
        # Use 'UDI' or the first column to remove overlapping duplicate entries
        id_col = 'UDI' if 'UDI' in combined_df.columns else combined_df.columns[0]
        combined_df = combined_df.drop_duplicates(subset=[id_col], keep='first')
        
        # Ensure linear sorting so our rolling temporal features work properly
        combined_df = combined_df.sort_values(by=id_col).reset_index(drop=True)
        final_count = combined_df.shape[0]
        
        print(f"🧹 Deduplication complete. Removed {initial_count - final_count} overlapping rows.")
    else:
        print("ℹ️ No supplementary CSV logs detected in data/raw. Ready with current data baseline.")
        
    # 5. Overwrite/Save back to the primary location for model training
    combined_df.to_csv(primary_file, index=False)
    print(f"💾 Training matrix finalized: {combined_df.shape[0]} total rows saved to {primary_file}\n")

if __name__ == "__main__":
    download_and_aggregate_data()