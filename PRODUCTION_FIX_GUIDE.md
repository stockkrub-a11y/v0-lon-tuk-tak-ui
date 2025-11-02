# Production Deployment Fix Guide

## Issue Summary

Your app works perfectly on localhost but fails in production with:
- ❌ Predict function returns 400 errors
- ❌ Upload function returns 500 errors  
- ❌ Stock color coding (Red/Yellow/Green) not updating correctly

## Root Cause

The Railway backend hasn't been redeployed with the updated `supabase==2.10.0` dependency, causing the Supabase client initialization to fail with a `proxy` parameter error.

## Quick Fix (5 minutes)

### Step 1: Verify Railway Environment Variables

1. Go to your Railway project: https://railway.app
2. Click on your backend service
3. Go to **Variables** tab
4. Verify these variables are set:

\`\`\`
SUPABASE_URL=https://julumxzweprvvcnealal.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
PORT=8000
\`\`\`

### Step 2: Force Railway Redeploy

**Option A: Push a small change to trigger redeploy**

\`\`\`bash
# Add a comment to trigger rebuild
echo "# Force rebuild $(date)" >> README.md
git add README.md
git commit -m "Force Railway redeploy with supabase 2.10.0"
git push origin main
\`\`\`

**Option B: Manual redeploy in Railway dashboard**

1. Go to your Railway project
2. Click on your backend service
3. Go to **Deployments** tab
4. Click the three dots on the latest deployment
5. Click **Redeploy**

### Step 3: Verify Deployment

Once Railway finishes deploying (2-3 minutes):

1. **Test the health endpoint:**
   \`\`\`
   https://your-railway-url.up.railway.app/health
   \`\`\`
   
   Should return:
   \`\`\`json
   {
     "status": "healthy",
     "database": "connected",
     "supabase_url_set": true,
     "supabase_key_set": true
   }
   \`\`\`

2. **Check Railway logs:**
   - Look for: `✅ Supabase client initialized successfully`
   - Should NOT see: `⚠️ Supabase client initialization failed: Client.__init__() got an unexpected keyword argument 'proxy'`

### Step 4: Test Your App

1. Go to your Vercel app: https://v0-lon-tuk-tak-3hl5zli6b-stockkrub-1951s-projects.vercel.app
2. Test the Predict function:
   - Go to Predict page
   - Click "Predict System"
   - Should generate forecasts without errors
3. Test the Upload function:
   - Go to Notifications page
   - Upload a stock file
   - Should process without 500 errors
4. Test color coding:
   - Go to Notifications page
   - Click on a product to edit MinStock/Buffer
   - Change the values
   - The status color (Red/Yellow/Green) should update correctly

## What Was Fixed

### 1. Updated Supabase Dependency
- Changed from `supabase==2.3.0` to `supabase==2.10.0`
- Fixes the `proxy` parameter compatibility issue

### 2. Better Error Handling
- Backend now handles missing Supabase credentials gracefully
- Clear error messages when database is unavailable
- Health check works even without database connection

### 3. Stock Color Logic
The color coding is calculated by the backend based on:

**RED Status:**
- Stock level < MinStock, OR
- Decrease rate > 50%

**YELLOW Status:**
- Decrease rate > 20% (but not red)

**GREEN Status:**
- Everything else (stock is sufficient)

When you update MinStock or Buffer:
1. Frontend calls `/notifications/update_manual_values`
2. Backend recalculates the status based on new values
3. Database is updated with new status
4. Frontend refreshes to show new colors

## Troubleshooting

### Issue: Railway deployment fails

**Check Railway build logs:**
- Look for Python dependency errors
- Verify `requirements.txt` is being read correctly

**Solution:**
\`\`\`bash
# Ensure requirements.txt is in the root directory
ls -la requirements.txt

# Should show: supabase==2.10.0
cat requirements.txt | grep supabase
\`\`\`

### Issue: Health check still shows "not configured"

**Check environment variables in Railway:**
- `SUPABASE_URL` must start with `https://`
- `SUPABASE_KEY` must be the anon/public key (not service role key)

**Get correct values:**
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to Settings → API
4. Copy "Project URL" and "anon public" key

### Issue: Colors still not updating

**Check browser console:**
- Look for errors when updating MinStock/Buffer
- Should see: `[v0] Writing final values for {product_sku}`

**Check Railway logs:**
- Should see: `[Backend] ✅ Updated manual values and recalculated status`
- Should NOT see: `[Backend] ❌ Error updating manual values`

**Verify the update endpoint:**
\`\`\`bash
# Test directly (replace with your Railway URL and product SKU)
curl -X POST "https://your-railway-url.up.railway.app/notifications/update_manual_values?product_sku=TEST-SKU&minstock=100&buffer=20"
\`\`\`

### Issue: Predict still returns 400

**This means no training data exists:**

1. Go to your app
2. Go to Predict page
3. Click "Upload Training Data"
4. Upload your sales and product files
5. Wait for training to complete
6. Then try predicting again

## Environment Variables Reference

### Vercel (Frontend)
\`\`\`
NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://julumxzweprvvcnealal.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
\`\`\`

### Railway (Backend)
\`\`\`
SUPABASE_URL=https://julumxzweprvvcnealal.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
PORT=8000
\`\`\`

## Success Checklist

- [ ] Railway environment variables are set correctly
- [ ] Railway has been redeployed
- [ ] Health endpoint returns "connected" for database
- [ ] Railway logs show "Supabase client initialized successfully"
- [ ] Predict function works without 400 errors
- [ ] Upload function works without 500 errors
- [ ] Stock colors (Red/Yellow/Green) update correctly when changing MinStock/Buffer
- [ ] No console errors in browser when using the app

## Still Having Issues?

If you've followed all steps and still have issues:

1. **Share your Railway logs:**
   - Go to Railway → Your Service → Logs
   - Copy the startup logs (first 50 lines)
   - Look for any errors or warnings

2. **Share your browser console:**
   - Open browser console (F12)
   - Try the failing action
   - Copy any error messages

3. **Verify your Railway URL:**
   - Make sure `NEXT_PUBLIC_API_URL` in Vercel matches your Railway URL exactly
   - No trailing slashes
   - Must start with `https://`

## Summary

The fix is simple: **Railway needs to redeploy with the updated `supabase==2.10.0` dependency**. Once that's done, all your functions will work exactly like they did on localhost!
