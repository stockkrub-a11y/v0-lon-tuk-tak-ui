# IMPORTANT: Restart Your Dev Server Now!

## The Problem
Your app is showing "Supabase error: {}" because the environment variables are not loaded.

## The Solution
I've created the `.env.local` file with your Supabase credentials. Now you need to restart your dev server.

## Steps to Fix:

### 1. Stop Your Current Server
Press `Ctrl + C` in your terminal to stop the dev server.

### 2. Restart the Server
\`\`\`bash
npm run dev
\`\`\`

### 3. Refresh Your Browser
Go to `http://localhost:3000/dashboard/stocks` and refresh the page.

## What Should Happen:
- The console should show: "[v0] ✓ Supabase client created successfully"
- Stock items should load from the database
- Categories should appear in the filter dropdown
- No more "Supabase error: {}" messages

## If It Still Doesn't Work:

### Check Row Level Security (RLS)
Your Supabase database might have Row Level Security enabled, which blocks all queries by default.

**To disable RLS:**
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to "Database" → "Tables"
4. For each table (`base_stock`, `stock_notifications`, `base_data`, `all_products`, `forecasts`):
   - Click on the table
   - Click "RLS" tab
   - Click "Disable RLS" button

**Or run this SQL in the SQL Editor:**
\`\`\`sql
ALTER TABLE base_stock DISABLE ROW LEVEL SECURITY;
ALTER TABLE stock_notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE base_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE all_products DISABLE ROW LEVEL SECURITY;
ALTER TABLE forecasts DISABLE ROW LEVEL SECURITY;
\`\`\`

## Still Having Issues?
Check the browser console for the detailed error messages. The logs will show exactly what's failing.
