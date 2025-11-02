# 🚂 Railway Deployment Guide for Lon TukTak Backend

## Quick Setup (3 Steps)

### Step 1: Push Code to GitHub
Make sure all your code is pushed to GitHub:
\`\`\`bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
\`\`\`

### Step 2: Deploy to Railway

1. Go to [Railway.app](https://railway.app)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically detect Python and start building

### Step 3: Add Environment Variables

In Railway dashboard, go to your project → Variables tab and add:

**Required Variables:**
\`\`\`
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
PORT=8000
\`\`\`

**Where to find these values:**
- Go to your Supabase project dashboard
- Click on "Project Settings" → "API"
- Copy the "Project URL" → Use as `SUPABASE_URL`
- Copy the "anon public" key → Use as `SUPABASE_KEY`

### Step 4: Get Your Backend URL

After deployment succeeds:
1. Railway will give you a URL like: `https://your-app.up.railway.app`
2. Test it by visiting: `https://your-app.up.railway.app/health`
3. You should see: `{"status":"healthy","timestamp":"..."}`

### Step 5: Update Frontend

Add this environment variable to your Vercel project:
\`\`\`
NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
\`\`\`

Then redeploy your frontend on Vercel.

---

## Troubleshooting

### Health Check Failing?

**Problem:** Railway shows "Healthcheck failed" or "service unavailable"

**Solution:**
1. Check that environment variables are set correctly
2. Make sure `SUPABASE_URL` and `SUPABASE_KEY` are added
3. Check the Deploy Logs (not Build Logs) for error messages
4. The app needs these variables to start

### Build Succeeds but Deploy Fails?

**Check Deploy Logs:**
1. In Railway, click on your deployment
2. Switch from "Build Logs" to "Deploy Logs"
3. Look for Python errors or missing dependencies

**Common Issues:**
- Missing environment variables → Add them in Variables tab
- Import errors → Make sure all dependencies are in `requirements.txt`
- Database connection errors → Verify Supabase credentials

### Port Issues?

Railway automatically sets the `PORT` environment variable. The Procfile is configured to use it:
\`\`\`
web: cd scripts && python -m uvicorn Backend:app --host 0.0.0.0 --port $PORT
\`\`\`

---

## Free Tier Limits

Railway free tier includes:
- **$5/month credit** (plenty for your backend)
- **500 hours/month** execution time
- **100 GB/month** bandwidth
- **1 GB** RAM per service

Your backend will:
- Sleep after 5 minutes of inactivity (saves credits)
- Wake up automatically when a request comes in (takes ~5 seconds)
- Use minimal resources when idle

---

## Testing Your Deployment

### Test Health Endpoint
\`\`\`bash
curl https://your-app.up.railway.app/health
\`\`\`

Expected response:
\`\`\`json
{"status":"healthy","timestamp":"2025-11-02T..."}
\`\`\`

### Test Notifications Endpoint
\`\`\`bash
curl https://your-app.up.railway.app/api/notifications
\`\`\`

Should return your notifications data.

---

## Next Steps

1. ✅ Backend deployed on Railway
2. ✅ Frontend published on Vercel
3. ✅ Add `NEXT_PUBLIC_API_URL` to Vercel
4. ✅ Test ML features in your live app

Your full-stack app with ML features is now live! 🎉
