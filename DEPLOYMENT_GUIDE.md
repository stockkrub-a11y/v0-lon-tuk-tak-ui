# Backend Deployment Guide - Railway (Free Tier)

This guide will help you deploy your Python FastAPI backend to Railway's free tier so your ML prediction features work when you publish to Vercel.

## Prerequisites

- GitHub account (to push your code)
- Railway account (free - sign up at https://railway.app)

## Step 1: Prepare Your Code

Your backend files are already set up in the repository:
- `backend/main.py` - Entry point that imports from scripts
- `scripts/Backend.py` - Main FastAPI application
- `scripts/DB_server.py` - Supabase database connection
- `scripts/Predict.py` - ML prediction logic
- `requirements.txt` - Python dependencies
- `Procfile` - Railway startup command
- `railway.json` - Railway configuration

## Step 2: Push to GitHub

1. Make sure all your backend files are committed:
   \`\`\`bash
   git add .
   git commit -m "Add backend deployment files"
   git push origin main
   \`\`\`

## Step 3: Deploy to Railway

### 3.1 Create Railway Project

1. Go to https://railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub
5. Select your repository: `v0-lon-tuk-tak-ui`
6. Railway will automatically detect it's a Python project

### 3.2 Configure Environment Variables

In your Railway project dashboard, go to **Variables** tab and add:

\`\`\`
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
PORT=8000
\`\`\`

**Where to find these values:**
- Go to your Supabase project dashboard
- Click "Project Settings" → "API"
- Copy "Project URL" → use as `SUPABASE_URL`
- Copy "anon public" key → use as `SUPABASE_KEY`

### 3.3 Deploy

1. Railway will automatically start deploying
2. Wait for the build to complete (2-3 minutes)
3. Once deployed, Railway will give you a public URL like:
   `https://your-app-name.up.railway.app`

## Step 4: Update Frontend Environment Variable

### In v0 (before publishing):

1. In v0, go to the **Vars** section in the sidebar
2. Update `NEXT_PUBLIC_API_URL` to your Railway URL:
   \`\`\`
   NEXT_PUBLIC_API_URL=https://your-app-name.up.railway.app
   \`\`\`

### After publishing to Vercel:

1. Go to your Vercel project dashboard
2. Go to **Settings** → **Environment Variables**
3. Add or update:
   \`\`\`
   NEXT_PUBLIC_API_URL=https://your-app-name.up.railway.app
   \`\`\`
4. Redeploy your Vercel app for changes to take effect

## Step 5: Test Your Deployment

1. Visit your Railway URL in a browser:
   \`\`\`
   https://your-app-name.up.railway.app/health
   \`\`\`
   
   You should see:
   \`\`\`json
   {
     "status": "healthy",
     "timestamp": "2025-..."
   }
   \`\`\`

2. Test from your published Vercel app:
   - Go to the Predict page
   - Click "Predict System"
   - Generate forecasts
   - It should work without needing to run anything locally!

## Railway Free Tier Limits

- **$5 free credit per month**
- **500 hours of execution time**
- **100 GB outbound bandwidth**
- **1 GB RAM, 1 vCPU**

This is more than enough for your ML prediction features!

## Troubleshooting

### Build Fails

Check Railway logs for errors. Common issues:
- Missing dependencies in `requirements.txt`
- Python version mismatch (Railway uses Python 3.11 by default)

### Backend Not Responding

1. Check Railway logs for errors
2. Verify environment variables are set correctly
3. Make sure `PORT` variable is set to `8000`

### Frontend Can't Connect

1. Verify `NEXT_PUBLIC_API_URL` is set correctly in Vercel
2. Make sure the URL doesn't have a trailing slash
3. Check CORS settings in `scripts/Backend.py` (already configured)

## Cost Optimization

To stay within free tier:
- Railway sleeps inactive apps after 5 minutes (first request wakes it up)
- ML predictions may take 10-20 seconds on first request after sleep
- Subsequent requests are fast

## Alternative: Keep Backend Local

If you prefer not to deploy the backend:
- Most features (notifications, stocks, analysis) work without it
- Only ML prediction features require the backend
- You can run the backend locally when needed:
  \`\`\`bash
  python scripts/Backend.py
  \`\`\`

## Summary

✅ **With Backend Deployed:**
- All features work including ML predictions
- No need to run anything locally
- Users can generate forecasts anytime

✅ **Without Backend (Supabase Only):**
- Notifications, stocks, and analysis work perfectly
- ML predictions require local backend
- Still fully functional for inventory management

Choose the option that works best for you!
