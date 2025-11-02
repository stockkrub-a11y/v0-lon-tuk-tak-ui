# Railway Deployment Fix Guide

## Issues Found

Based on your Railway logs, there are 2 main issues:

### 1. Buffer Column Error (500 errors on upload)
**Problem:** The code was trying to read a `buffer` column from `stock_notifications` table, but this column doesn't exist in your Supabase database.

**Solution:** ✅ Fixed in the code above
- Changed `Notification.py` to only query `min_stock` from the database
- Buffer is now calculated dynamically based on `decrease_rate` (same as before)
- Updated `Backend.py` to handle buffer as a calculation parameter, not a stored value

### 2. ML Model File Missing (400 errors on predict)
**Problem:** The Railway backend can't find the trained ML model file (`xgb_sales_model.pkl`).

**Solution:** You need to train the model on production OR upload the model file to Railway.

## Quick Fix Steps

### Step 1: Redeploy Railway Backend

The code fixes are already in your repository. Railway should automatically redeploy when you push to GitHub.

1. **Check if Railway is connected to your GitHub repo:**
   - Go to your Railway project
   - Click on the "web" service
   - Check the "Deployments" tab
   - It should show "Deployed from GitHub"

2. **If Railway doesn't auto-deploy:**
   - Go to Railway dashboard
   - Click "Deploy" button manually
   - Or trigger a redeploy by clicking the three dots → "Redeploy"

### Step 2: Train the ML Model

After the backend is redeployed, you need to train the model:

**Option A: Train via the Frontend (Recommended)**
1. Go to your Vercel app: https://v0-lon-tuk-tak-7owo7744d-stockkrub-1951s-projects.vercel.app
2. Navigate to the "Train" or "Analysis" page (if you have one)
3. Upload your product and sales Excel files
4. The backend will train the model and save it to Railway

**Option B: Train via API directly**
\`\`\`bash
curl -X POST "https://web-production-ea66c.up.railway.app/train" \
  -F "product_file=@your_product_file.xlsx" \
  -F "sales_file=@your_sales_file.xlsx"
\`\`\`

### Step 3: Verify Everything Works

1. **Test Upload Function:**
   - Go to Notifications page
   - Click "Upload Current Stock"
   - Upload a stock file
   - Should see success message (no more 500 errors)

2. **Test Predict Function:**
   - Go to Predict page
   - Click "Predict System"
   - Should generate forecasts (no more 400 errors)

3. **Test Min Stock / Buffer Changes:**
   - Go to Stocks page
   - Change min_stock or buffer values
   - The color coding should update correctly

## What Was Fixed

### Before:
\`\`\`python
# ❌ This was causing KeyError: 'buffer'
manual_values_df = execute_query("SELECT product_sku, min_stock, buffer FROM stock_notifications")
manual_buf_map = manual_values_df.set_index('product_sku')['buffer'].to_dict()
\`\`\`

### After:
\`\`\`python
# ✅ Only query min_stock (buffer doesn't exist in database)
manual_values_df = execute_query("SELECT product_sku, min_stock FROM stock_notifications")
manual_min_map = manual_values_df.set_index('product_sku')['min_stock'].to_dict()

# ✅ Calculate buffer dynamically based on decrease_rate
dyn_buf = np.select(
    [curr['decrease_rate'] > 50, curr['decrease_rate'] > 20],
    [20, 10],
    default=5
)
buffer_values = np.minimum(dyn_buf, MAX_BUFFER).astype(int)
\`\`\`

## Expected Timeline

- **Code deployment:** 2-3 minutes (Railway auto-deploys from GitHub)
- **Model training:** 5-10 minutes (depends on data size)
- **Total time to fix:** ~10-15 minutes

## Troubleshooting

If you still see errors after redeployment:

1. **Check Railway logs:**
   - Go to Railway dashboard
   - Click on "web" service
   - Click "Deploy Logs" tab
   - Look for any new errors

2. **Check Supabase connection:**
   - Verify `SUPABASE_URL` and `SUPABASE_KEY` are set in Railway
   - Go to Railway → Settings → Variables
   - Make sure they match your Supabase project

3. **Clear browser cache:**
   - Hard refresh your Vercel app (Ctrl+Shift+R or Cmd+Shift+R)
   - This ensures you're using the latest frontend code

## Need Help?

If you're still experiencing issues:
1. Check the Railway logs and share any new error messages
2. Verify the Supabase database schema matches what's expected
3. Make sure the model training completed successfully
