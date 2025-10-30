# Troubleshooting Supabase Connection

## Current Errors

If you're seeing errors like:
- `[v0] Failed to fetch stock levels: {}`
- `[v0] Failed to fetch categories: {}`
- `Error: Failed to fetch`

This means the Supabase client is not properly configured.

## Step-by-Step Fix

### 1. Check Environment Variables

Make sure you have a `.env.local` file in your project root with:

\`\`\`env
NEXT_PUBLIC_SUPABASE_URL=https://julumxzweprvvcnealal.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1bHVteHp3ZXBydnZjbmVhbGFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE1MDU4OTksImV4cCI6MjA3NzA4MTg5OX0.AKluaTWZShPmCcsQZqKJNyz8jC7nwgZEqz0t3mTimBg
\`\`\`

### 2. Restart Dev Server

**CRITICAL**: After creating or modifying `.env.local`, you MUST restart your dev server:

\`\`\`bash
# Stop the server (Ctrl+C)
# Then start it again
npm run dev
\`\`\`

### 3. Check Browser Console

Open your browser console (F12) and look for:
- `[v0] Initializing Supabase client with URL: https://julumxzweprvvcnealal.supabase.co`
- `[v0] Fetching stock levels with params: ...`
- `[v0] Successfully fetched X stock items`

If you see errors about missing environment variables, the `.env.local` file is not being read.

### 4. Disable Row Level Security (RLS)

If the client is initialized but queries are failing, RLS might be blocking access:

1. Go to https://supabase.com/dashboard/project/julumxzweprvvcnealal
2. Click on "Authentication" → "Policies"
3. For each table (base_stock, stock_notifications, etc.):
   - Click on the table
   - Click "Disable RLS" or "Add Policy" → "Enable read access for all users"

### 5. Test Connection

Open your browser console and run:

\`\`\`javascript
console.log('Supabase URL:', process.env.NEXT_PUBLIC_SUPABASE_URL)
console.log('Supabase Key:', process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? 'Set' : 'Missing')
\`\`\`

Both should show values. If they're undefined, restart your dev server.

## Common Issues

### Issue: "Failed to fetch" errors
**Solution**: Restart dev server after creating `.env.local`

### Issue: Empty data arrays but no errors
**Solution**: Disable RLS in Supabase dashboard

### Issue: "Supabase URL is not configured"
**Solution**: Check `.env.local` file exists and has correct variable names (must start with `NEXT_PUBLIC_`)

### Issue: Works in v0 but not locally
**Solution**: v0 automatically injects environment variables. Locally, you need `.env.local` file.

## Verification Checklist

- [ ] `.env.local` file exists in project root
- [ ] File contains `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- [ ] Dev server was restarted after creating `.env.local`
- [ ] Browser console shows Supabase initialization message
- [ ] RLS is disabled or policies are configured in Supabase dashboard
- [ ] No CORS errors in browser console

## Still Not Working?

Check the browser console for detailed error messages. The `[v0]` prefix indicates debug logs from the application that will help identify the issue.
