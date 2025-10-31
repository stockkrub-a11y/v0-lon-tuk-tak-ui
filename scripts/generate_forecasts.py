"""
Generate forecasts and save to Supabase
"""
import pandas as pd
import numpy as np
from datetime import datetime
from Auto_cleaning import auto_cleaning
from Predict import update_model_and_train, forcast_loop
from DB_server import insert_data, delete_data, execute_query
import joblib

def main():
    print("Loading test data...")
    # Use the last month of data from base_data as test data
    df_cleaned = execute_query("SELECT * FROM base_data ORDER BY sales_date DESC")
    
    if df_cleaned.empty:
        print("❌ No data found in base_data table")
        return
    
    # Convert date columns
    print("Converting date columns...")
    df_cleaned['sales_date'] = pd.to_datetime(df_cleaned['sales_date'])
    
    print(f"✅ Loaded {len(df_cleaned)} records from base_data")
    
    try:
        print("Training model...")
        df_window_raw, df_window, base_model, X_train, y_train, X_test, y_test, product_sku_last = update_model_and_train(df_cleaned)
        print("✅ Model training completed successfully")
        
        # Generate forecasts
        print("Generating forecasts...")
        long_forecast, forecast_results = forcast_loop(X_train, y_train, df_window_raw, product_sku_last, base_model)
        
        if forecast_results and len(forecast_results) > 0:
            print(f"✅ Generated {len(forecast_results)} forecasts")
            
            # Convert forecast results to DataFrame
            print("Processing forecast results...")
            forecast_df = pd.DataFrame(forecast_results)
            print(f"Forecast columns: {forecast_df.columns.tolist()}")
            
            # Clean up data for Supabase
            records = forecast_df.to_dict(orient='records')
            print(f"Cleaning {len(records)} forecast records...")
            for record in records:
                for key, value in list(record.items()):
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, pd.Timestamp):
                        record[key] = value.isoformat()
                    elif isinstance(value, datetime):
                        record[key] = value.isoformat()
            
            # Clear old forecasts and insert new ones
            print("Clearing old forecasts...")
            delete_data('forecasts', 'product_sku', '*')
            
            print("Inserting new forecasts...")
            result = insert_data('forecasts', records)
            if result is not None:
                print(f"✅ Successfully saved {len(records)} forecasts to forecasts table")
            else:
                print("⚠️ Failed to save forecasts to forecasts table")
        else:
            print("⚠️ No forecasts generated")
            
    except Exception as e:
        print(f"❌ Error generating forecasts: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
