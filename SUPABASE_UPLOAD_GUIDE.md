# Supabase Upload Guide

Your app now uploads data directly to Supabase without needing the FastAPI backend!

## What Changed

### Before (Required Backend):
1. Upload files → Send to FastAPI backend
2. Backend trains ML model
3. Backend inserts data into database
4. Frontend fetches data from backend

### After (No Backend Needed):
1. Upload files → Parse in browser using xlsx library
2. Insert data directly into Supabase tables
3. Frontend fetches data from Supabase
4. ML training is optional (can be done separately)

## How to Upload Files

1. Go to **Stocks** page
2. Click **"Upload Product List"** or **"Upload Sale Stock"**
3. Select your Excel file (.xlsx or .csv)
4. Upload both files (product and sales)
5. Data is automatically inserted into Supabase

## File Format Requirements

### Product File (Stock.xlsx)
Required columns:
- `SKU` or `Product SKU` - Product identifier
- `Name` or `Product Name` - Product name
- `Category` or `หมวดหมู่` - Product category
- `Quantity` or `Stock` - Current stock level

### Sales File (Sales Order.xlsx)
Required columns:
- `SKU` or `Product SKU` - Product identifier
- `Name` or `Product Name` - Product name
- `Quantity` or `Total Quantity` - Sales quantity
- `Date` or `Sales Date` - Sale date

## What Happens During Upload

1. **Product file** → Inserted into `all_products` and `base_stock` tables
2. **Sales file** → Inserted into `base_data` table
3. Data is automatically parsed and formatted
4. Existing products are updated (upsert)

## ML Training (Optional)

The upload no longer trains ML models automatically. To generate predictions:

### Option 1: Use Your FastAPI Backend
1. Modify your backend to read from Supabase (see BACKEND_SUPABASE_MIGRATION.md)
2. Run training endpoint manually
3. Backend writes predictions to `forecasts` table
4. Frontend displays existing forecasts

### Option 2: Use Supabase Edge Functions
1. Create an Edge Function for ML training
2. Trigger it manually or on schedule
3. Write predictions to `forecasts` table

### Option 3: Manual Training
1. Export data from Supabase
2. Train models locally
3. Import predictions back to `forecasts` table

## Benefits

- No need to run backend server for data uploads
- Faster uploads (no network round-trip to backend)
- Data goes directly to Supabase
- Simpler architecture
- Works offline (once data is uploaded)

## Troubleshooting

### Upload fails with "Failed to insert products"
- Check that your Excel file has the required columns
- Ensure SKU column is not empty
- Verify Supabase connection in environment variables

### Data not showing after upload
- Refresh the page
- Check browser console for errors
- Verify data was inserted in Supabase dashboard

### Excel file not parsing correctly
- Ensure file is .xlsx or .csv format
- Check that column names match expected format
- Try opening file in Excel to verify it's not corrupted
