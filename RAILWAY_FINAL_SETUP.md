# Railway Deployment - Final Setup Guide

## What We Fixed

The deployment was failing because Railway's Nixpacks wasn't properly detecting and installing Python. We've now added explicit Python configuration.

## Files Configuration

### 1. `nixpacks.toml` (NEW)
Explicitly tells Railway to:
- Install Python 3.11 and pip
- Install dependencies from requirements.txt
- Run the FastAPI backend with uvicorn

### 2. `Procfile`
Defines the web process command (backup for Railway)

### 3. `runtime.txt`
Specifies Python 3.11 version

### 4. `requirements.txt`
Lists all Python dependencies

## Deployment Steps

### Step 1: Push to GitHub
\`\`\`bash
git add .
git commit -m "fix: Add nixpacks.toml for explicit Python configuration"
git push origin main
\`\`\`

### Step 2: Verify Environment Variables in Railway
Make sure these are set in Railway dashboard → Variables tab:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon/public key

### Step 3: Railway Will Auto-Deploy
- Railway detects the GitHub push
- Nixpacks installs Python 3.11
- Installs all requirements
- Starts the FastAPI backend
- Health check on `/health` should pass

## Expected Result

✅ Build succeeds (installs Python and dependencies)
✅ Deploy succeeds (starts uvicorn server)
✅ Health check passes (backend responds on `/health`)
✅ Service is Active and accessible

## Troubleshooting

If it still fails:

1. **Check Build Logs** - Verify Python 3.11 is being installed
2. **Check Deploy Logs** - Look for any startup errors
3. **Verify Environment Variables** - Ensure SUPABASE_URL and SUPABASE_KEY are set
4. **Check Health Endpoint** - The backend should respond to GET `/health`

## Testing Your Deployment

Once deployed, test the backend:

\`\`\`bash
# Replace with your Railway URL
curl https://your-app.railway.app/health

# Should return:
# {"status": "healthy", "supabase_connected": true}
\`\`\`

## Next Steps

After successful deployment:
1. Update your frontend API URL to point to the Railway backend
2. Test all API endpoints
3. Monitor logs for any issues

## Support

If you continue to have issues:
- Check Railway logs in the dashboard
- Verify all environment variables are correct
- Ensure your Supabase project is accessible
