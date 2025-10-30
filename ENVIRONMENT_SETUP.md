# Environment Variables Setup

## The Problem

You're seeing errors like:
- `[v0] Failed to fetch stock levels: {}`
- `Error: Failed to fetch`
- `Supabase credentials missing`

This happens because the Supabase credentials are not loaded.

## The Solution

### Step 1: Create `.env.local` File

In your project root (same folder as `package.json`), create a file named `.env.local`:

\`\`\`env
NEXT_PUBLIC_SUPABASE_URL=https://julumxzweprvvcnealal.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1bHVteHp3ZXBydnZjbmVhbGFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE1MDU4OTksImV4cCI6MjA3NzA4MTg5OX0.AKluaTWZShPmCcsQZqKJNyz8jC7nwgZEqz0t3mTimBg
\`\`\`

### Step 2: Restart Dev Server

**THIS IS CRITICAL** - Environment variables are only loaded when the server starts.

\`\`\`bash
# Stop your current server (press Ctrl+C in the terminal)
# Then start it again:
npm run dev
\`\`\`

### Step 3: Verify It's Working

Open your browser console (F12) and look for:
\`\`\`
[v0] Initializing Supabase client
[v0] Supabase URL: ✓ Configured
[v0] Supabase Key: ✓ Configured
[v0] ✓ Supabase client created successfully
\`\`\`

If you see `✗ Missing`, the `.env.local` file is not being read. Make sure:
1. The file is named exactly `.env.local` (not `.env.local.txt`)
2. The file is in the project root folder
3. You restarted the dev server

### Step 4: Disable Row Level Security (RLS)

Even with credentials configured, Supabase might block queries due to RLS:

1. Go to: https://supabase.com/dashboard/project/julumxzweprvvcnealal
2. Click "Authentication" → "Policies"
3. For each table, click "Disable RLS" (for development)

OR create a policy that allows public read access:
- Policy name: "Enable read access for all users"
- Policy command: SELECT
- Target roles: public
- USING expression: `true`

## Why This Happens

- **In v0**: Environment variables are automatically injected
- **Locally**: You need to create `.env.local` file manually
- **Next.js**: Only reads `.env.local` when the server starts

## Quick Test

Run this in your browser console:
\`\`\`javascript
console.log('URL:', process.env.NEXT_PUBLIC_SUPABASE_URL)
console.log('Key:', process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? 'Set' : 'Missing')
\`\`\`

If both show values, your environment is configured correctly.
