# Railway Deployment Guide

## Quick Deploy Steps

1. **Push to GitHub** (if not done already)
   \`\`\`bash
   git add .
   git commit -m "Add Railway deployment config"
   git push origin main
   \`\`\`

2. **Go to Railway.app**
   - Sign up/login at https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Add Environment Variables**
   In Railway dashboard, go to Variables tab and add:
   \`\`\`
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   PORT=8000
   \`\`\`

4. **Deploy**
   - Railway will automatically detect Python and install dependencies
   - It will use the `Procfile` to start your backend
   - You'll get a URL like: `https://your-app.up.railway.app`

5. **Update Frontend**
   - Copy your Railway URL
   - In Vercel (when you publish), add environment variable:
     \`\`\`
     NEXT_PUBLIC_API_URL=https://your-app.up.railway.app
     \`\`\`

## Troubleshooting

### If deployment fails:
1. Check the logs in Railway dashboard
2. Make sure all environment variables are set
3. Verify your Supabase credentials are correct

### If backend is slow to wake up:
- Railway free tier puts apps to sleep after inactivity
- First request after sleep takes 10-20 seconds
- Subsequent requests are fast

## Testing Your Backend

Once deployed, test these endpoints:
- `https://your-app.up.railway.app/health` - Should return {"status": "healthy"}
- `https://your-app.up.railway.app/api/test` - Should return success message
- `https://your-app.up.railway.app/api/notifications` - Should return your notifications

## Free Tier Limits

Railway free tier includes:
- $5/month credit
- 500 hours of usage
- Apps sleep after 10 minutes of inactivity
- Perfect for your ML prediction features!
