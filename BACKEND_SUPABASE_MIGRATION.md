# Backend Migration to Supabase

This guide explains how to modify your FastAPI backend to work with Supabase instead of a local database.

## Architecture Overview

**New Data Flow:**
1. Frontend → Supabase (for reading data: notifications, stock, analytics)
2. Backend → Supabase (for ML operations: read training data, write predictions)
3. Frontend never calls Backend directly anymore

## Step 1: Install Supabase Python Client

\`\`\`bash
pip install supabase
\`\`\`

## Step 2: Configure Supabase Connection

Create a `supabase_client.py` file in your backend:

\`\`\`python
from supabase import create_client, Client
import os

# Your Supabase credentials
SUPABASE_URL = "https://oscypcfrridgqwgqvdsl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9zY3lwY2ZycmlkZ3F3Z3F2ZHNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE0OTQwMzksImV4cCI6MjA3NzA3MDAzOX0.QBnN-xZklTFkBVQCeAoKlVPrfHYFiRD7DSBcF0h5Muk"

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    return supabase
\`\`\`

## Step 3: Read Training Data from Supabase

Replace your database queries with Supabase queries:

\`\`\`python
from supabase_client import get_supabase_client

def get_historical_sales_data():
    """Fetch historical sales data for training"""
    supabase = get_supabase_client()
    
    # Query base_data table
    response = supabase.table('base_data').select('*').execute()
    
    return response.data

def get_stock_data():
    """Fetch current stock levels"""
    supabase = get_supabase_client()
    
    # Query base_stock table
    response = supabase.table('base_stock').select('*').execute()
    
    return response.data
\`\`\`

## Step 4: Write Predictions to Supabase

After generating predictions, write them back to Supabase:

\`\`\`python
def save_forecast_to_supabase(forecast_data):
    """Save forecast predictions to Supabase"""
    supabase = get_supabase_client()
    
    # Insert into forecasts table
    response = supabase.table('forecasts').insert(forecast_data).execute()
    
    return response.data

def save_stock_notifications(notifications):
    """Save stock notifications to Supabase"""
    supabase = get_supabase_client()
    
    # Insert into stock_notifications table
    response = supabase.table('stock_notifications').insert(notifications).execute()
    
    return response.data
\`\`\`

## Step 5: Update Your ML Training Endpoint

Example of how to modify your `/train` endpoint:

\`\`\`python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase_client import get_supabase_client
import pandas as pd

app = FastAPI()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/train")
async def train_model():
    """Train ML model using data from Supabase"""
    supabase = get_supabase_client()
    
    # 1. Fetch training data from Supabase
    response = supabase.table('base_data').select('*').execute()
    data = pd.DataFrame(response.data)
    
    # 2. Train your model
    # ... your ML training code ...
    
    # 3. Save model (to file or Supabase storage)
    # model.save('model.pkl')
    
    return {"status": "success", "message": "Model trained successfully"}

@app.post("/predict")
async def predict_sales(n_forecast: int = 1):
    """Generate predictions and save to Supabase"""
    supabase = get_supabase_client()
    
    # 1. Load your trained model
    # model = load_model('model.pkl')
    
    # 2. Fetch recent data from Supabase
    response = supabase.table('base_data').select('*').order('date', desc=True).limit(100).execute()
    data = pd.DataFrame(response.data)
    
    # 3. Generate predictions
    # predictions = model.predict(data, n_forecast)
    
    # 4. Save predictions to Supabase
    forecast_data = [
        {
            "date": "2024-01-01",
            "sku": "SKU001",
            "predicted_sales": 100,
            "forecast_months": n_forecast
        }
        # ... more predictions
    ]
    
    supabase.table('forecasts').insert(forecast_data).execute()
    
    return {"status": "success", "predictions": forecast_data}
\`\`\`

## Step 6: Database Tables Structure

Your Supabase database should have these tables:

### `base_data` (Historical Sales)
- date
- sku
- product_name
- category
- quantity
- price

### `base_stock` (Current Stock)
- sku
- product_name
- category
- current_stock
- min_stock
- reorder_qty

### `forecasts` (Predictions)
- id
- date
- sku
- product_name
- predicted_sales
- forecast_months
- created_at

### `stock_notifications` (Alerts)
- id
- product
- stock
- last_stock
- decrease_rate
- weeks_to_empty
- min_stock
- buffer
- reorder_qty
- status
- description
- created_at

## Step 7: Run Your Backend

\`\`\`bash
# Start your backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

## Important Notes

1. **Frontend doesn't call backend anymore** - All data reading is done directly from Supabase
2. **Backend is now ML-only** - Only used for training models and generating predictions
3. **Predictions are stored in Supabase** - Frontend reads them from the `forecasts` table
4. **Use service role key for backend** - For write operations, you may need the service role key (not the anon key)

## Optional: Scheduled Predictions

You can set up a cron job or Supabase Edge Function to automatically generate predictions:

\`\`\`python
# Run this daily to generate fresh predictions
import schedule
import time

def daily_prediction_job():
    """Generate predictions daily"""
    # Call your predict endpoint
    predict_sales(n_forecast=3)

schedule.every().day.at("00:00").do(daily_prediction_job)

while True:
    schedule.run_pending()
    time.sleep(60)
\`\`\`

## Testing

Test your backend endpoints:

\`\`\`bash
# Test training
curl -X POST "http://localhost:8000/train"

# Test prediction
curl -X POST "http://localhost:8000/predict?n_forecast=3"
\`\`\`

Then check your Supabase dashboard to verify the data was written correctly.
