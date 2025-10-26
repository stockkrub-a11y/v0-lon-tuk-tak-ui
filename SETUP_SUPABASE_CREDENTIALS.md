# Setup Supabase Credentials

## Quick Fix - Add Environment Variables

Your Supabase client is configured correctly, but it needs the environment variables to be set.

### Step 1: Add Environment Variables in v0

1. Click on the **sidebar** (left side of the chat)
2. Click on **"Vars"** section
3. Add these two environment variables:

**Variable 1:**
- Name: `NEXT_PUBLIC_SUPABASE_URL`
- Value: `https://julumxzweprvvcnealal.supabase.co`

**Variable 2:**
- Name: `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Value: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1bHVteHp3ZXBydnZjbmVhbGFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE1MDU4OTksImV4cCI6MjA3NzA4MTg5OX0.AKluaTWZShPmCcsQZqKJNyz8jC7nwgZEqz0t3mTimBg`

### Step 2: Restart the Dev Server

After adding the environment variables:
1. Stop the dev server (Ctrl+C in terminal)
2. Run `npm run dev` again
3. The Supabase client will now work!

### Step 3: Fix Database Constraint

You also need to run this SQL in your Supabase dashboard to allow NULL values in product_name:

\`\`\`sql
-- Allow NULL values in product_name column
ALTER TABLE base_stock 
ALTER COLUMN product_name DROP NOT NULL;

-- Add a comment explaining why NULL is allowed
COMMENT ON COLUMN base_stock.product_name IS 'Product name - allows NULL to handle products with emojis or special characters';
\`\`\`

Go to: https://julumxzweprvvcnealal.supabase.co/project/julumxzweprvvcnealal/sql/new

Paste the SQL above and click "Run".

## Why This is Needed

- `NEXT_PUBLIC_` prefix makes variables accessible in the browser
- The Supabase client needs these to connect to your database
- Without them, the client cannot be created and uploads will fail

## After Setup

Once you've added the environment variables and restarted the server:
- File uploads will work
- Stock data will load from Supabase
- Notifications will display properly
- No more "@supabase/ssr" errors!
