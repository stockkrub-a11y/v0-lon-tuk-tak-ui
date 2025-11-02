# Railway Deployment Instructions

## Current Issue: Health Check Failing

Your Railway deployment is **building successfully** but failing the health check because the Supabase environment variables are not set.

## Quick Fix (5 minutes)

### Step 1: Add Environment Variables in Railway

1. Go to your Railway project dashboard
2. Click on your service (web)
3. Click on **"Variables"** tab
4. Add these two environment variables:

\`\`\`
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
\`\`\`

**Where to find these values:**

- Go to your Supabase project dashboard at https://supabase.com/dashboard
- Click on your project
- Go to **Settings** → **API**
- Copy:
  - **Project URL** → Use as `SUPABASE_URL`
  - **anon/public key** → Use as `SUPABASE_KEY`

### Step 2: Redeploy

After adding the environment variables, Railway will automatically redeploy. The health check should now pass!

## What Was Fixed

1. **Backend now handles missing env vars gracefully** - Won't crash if Supabase credentials are missing
2. **Health check works without database** - The `/health` endpoint now responds even if database isn't configured
3. **Increased health check timeout** - Railway now waits up to 300 seconds for the app to start
4. **Better error messages** - You'll see clear warnings if environment variables are missing

## Verify Deployment

Once deployed successfully, your backend will be available at:
\`\`\`
https://your-app.up.railway.app
\`\`\`

Test it:
- Health check: `https://your-app.up.railway.app/health`
- Test endpoint: `https://your-app.up.railway.app/api/test`

## Next Steps

After Railway deployment succeeds:

1. **Copy your Railway URL** (e.g., `https://your-app.up.railway.app`)
2. **Publish your frontend to Vercel** via v0
3. **Add environment variable in Vercel**:
   - Variable name: `NEXT_PUBLIC_API_URL`
   - Value: Your Railway URL (e.g., `https://your-app.up.railway.app`)

Then your full-stack app with ML features will be live! 🚀

## Troubleshooting

If deployment still fails:

1. **Check Deploy Logs** (not Build Logs) in Railway to see runtime errors
2. **Verify environment variables** are set correctly (no extra spaces)
3. **Check Supabase credentials** are valid and project is active

## Free Tier Limits

Railway free tier includes:
- $5/month credit
- 500 hours of usage
- Your backend will sleep after 5 minutes of inactivity
- Wakes up automatically when accessed (takes ~10 seconds)

This is perfect for your ML prediction features!
