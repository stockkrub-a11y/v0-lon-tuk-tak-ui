# Fix Supabase Connection Issues

## Problem
The app shows "Supabase Connected" but fails to fetch data with errors like:
- `[v0] Failed to fetch stock levels: {}`
- `[v0] Failed to fetch categories: {}`
- `Upload failed: Failed to fetch`

## Root Cause
The environment variables for Supabase are not being loaded properly.

## Solution

### Step 1: Create .env.local File

I've created a `.env.local` file with your Supabase credentials. This file is already in your project root.

**Important:** If you cloned this project from Git, the `.env.local` file might not exist (it's in `.gitignore`). In that case:

1. Copy the `.env.local.example` file to `.env.local`:
   \`\`\`bash
   cp .env.local.example .env.local
   \`\`\`

2. Or create `.env.local` manually with this content:
   \`\`\`
   NEXT_PUBLIC_SUPABASE_URL=https://julumxzweprvvcnealal.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1bHVteHp3ZXBydnZjbmVhbGFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE1MDU4OTksImV4cCI6MjA3NzA4MTg5OX0.AKluaTWZShPmCcsQZqKJNyz8jC7nwgZEqz0t3mTimBg
   \`\`\`

### Step 2: Restart the Dev Server

**This is the most important step!** Next.js only loads environment variables when the server starts.

1. Stop your dev server (Ctrl+C in the terminal)
2. Start it again:
   \`\`\`bash
   npm run dev
   \`\`\`

### Step 3: Verify Connection

After restarting, open the browser console and look for these messages:
- `[v0] Supabase URL: ✓ Found`
- `[v0] Supabase Key: ✓ Found`

If you see `✗ Missing`, the `.env.local` file is not being loaded.

### Step 4: Check Supabase RLS (Row Level Security)

If the environment variables are loaded but you still can't fetch data, the issue might be Row Level Security in Supabase.

1. Go to your Supabase dashboard: https://supabase.com/dashboard/project/julumxzweprvvcnealal
2. Click on "Authentication" → "Policies"
3. For each table (base_stock, stock_notifications, etc.), you need to either:
   - **Option A (Quick Fix):** Disable RLS temporarily for testing
   - **Option B (Secure):** Add a policy to allow public read access

**To disable RLS (for testing only):**
\`\`\`sql
ALTER TABLE base_stock DISABLE ROW LEVEL SECURITY;
ALTER TABLE stock_notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE base_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE all_products DISABLE ROW LEVEL SECURITY;
ALTER TABLE forecasts DISABLE ROW LEVEL SECURITY;
\`\`\`

**To add public read policy (more secure):**
\`\`\`sql
-- Allow anyone to read base_stock
CREATE POLICY "Allow public read access" ON base_stock
FOR SELECT USING (true);

-- Repeat for other tables
CREATE POLICY "Allow public read access" ON stock_notifications
FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON base_data
FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON all_products
FOR SELECT USING (true);

CREATE POLICY "Allow public read access" ON forecasts
FOR SELECT USING (true);
\`\`\`

### Troubleshooting

**If you still see errors after restarting:**

1. Check the browser console for the Supabase connection messages
2. Verify the `.env.local` file exists in the project root (same folder as `package.json`)
3. Make sure you restarted the dev server (not just refreshed the browser)
4. Check Supabase RLS policies as described above

**Common mistakes:**
- Forgetting to restart the dev server after creating `.env.local`
- Creating `.env` instead of `.env.local` (must be `.env.local`)
- RLS blocking queries (most common issue)
