# Local Setup Guide - Lon TukTak Stock Management

This guide will help you clone and run the application on your local machine.

## Prerequisites

- Node.js 18+ installed
- Git installed
- A code editor (VS Code recommended)

## Quick Start (Frontend Only - Recommended)

### Step 1: Clone the Repository

\`\`\`bash
git clone <your-repo-url>
cd lon-tuk-tak-ui
\`\`\`

### Step 2: Install Dependencies

\`\`\`bash
npm install
\`\`\`

### Step 3: Set Up Environment Variables

Create a `.env.local` file in the root directory:

\`\`\`bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://julumxzweprvvcnealal.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1bHVteHp3ZXBydnZjbmVhbGFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE1MDU4OTksImV4cCI6MjA3NzA4MTg5OX0.AKluaTWZShPmCcsQZqKJNyz8jC7nwgZEqz0t3mTimBg
\`\`\`

**Important:** These are your Supabase credentials. The app needs these to connect to your database.

### Step 4: Run the Development Server

\`\`\`bash
npm run dev
\`\`\`

The app will start at `http://localhost:3000`

### Step 5: Open in Browser

Navigate to `http://localhost:3000/dashboard` to see your app.

## What Works Without Backend?

**✅ Fully Functional:**
- View all stock items (3040+ products)
- Search and filter stocks
- View dashboard analytics
- View notifications
- View analysis charts and reports
- View existing predictions
- Clear predictions

**⚠️ Requires Backend (Optional):**
- Upload new stock files
- Generate new predictions

## Understanding Supabase (No Setup Needed!)

**Good news:** You don't need to set up Supabase yourself! Here's why:

1. **Already Configured**: Your Supabase database is already set up and running in the cloud
2. **Just Connect**: You only need to add the environment variables (Step 3 above)
3. **No Installation**: Supabase is a cloud service - nothing to install locally
4. **Data Already There**: Your database already has 3040 stock items and all the data

**What is Supabase?**
- It's like a cloud database (similar to Firebase)
- Your app connects to it over the internet
- All your data is stored there safely
- You can view/edit data at: https://supabase.com/dashboard

## Troubleshooting

### Error: "Supabase client creation failed"

**Solution:** Make sure your `.env.local` file exists and has the correct variables:
\`\`\`bash
NEXT_PUBLIC_SUPABASE_URL=https://julumxzweprvvcnealal.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
\`\`\`

Then restart the dev server:
\`\`\`bash
# Stop the server (Ctrl+C)
npm run dev
\`\`\`

### Error: "Module not found"

**Solution:** Reinstall dependencies:
\`\`\`bash
rm -rf node_modules
npm install
\`\`\`

### Page shows "No data"

**Solution:** Check the browser console (F12) for errors. Make sure:
1. Environment variables are set correctly
2. Dev server was restarted after adding `.env.local`
3. You're connected to the internet (Supabase is cloud-based)

## Optional: Running the Backend (For ML Features)

If you want to upload files and generate predictions, you need the Python backend:

### Backend Setup

1. **Install Python 3.8+**

2. **Navigate to backend directory** (if you have it):
\`\`\`bash
cd backend
\`\`\`

3. **Install Python dependencies**:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

4. **Create backend `.env` file**:
\`\`\`bash
SUPABASE_URL=https://julumxzweprvvcnealal.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
\`\`\`

5. **Run the backend**:
\`\`\`bash
python main.py
\`\`\`

Backend will start at `http://localhost:8000`

## Project Structure

\`\`\`
lon-tuk-tak-ui/
├── app/                    # Next.js pages
│   ├── dashboard/         # Dashboard pages
│   │   ├── page.tsx      # Main dashboard
│   │   ├── stocks/       # Stock management
│   │   ├── notifications/ # Notifications
│   │   ├── predict/      # Predictions
│   │   └── analysis/     # Analysis
├── components/            # React components
├── lib/                   # Utilities
│   ├── api.ts            # API functions (uses Supabase)
│   └── supabase/         # Supabase client
├── .env.local            # Environment variables (create this!)
└── package.json          # Dependencies
\`\`\`

## VS Code Tips

1. **Install Extensions:**
   - ESLint
   - Prettier
   - Tailwind CSS IntelliSense

2. **Open Integrated Terminal:**
   - Press `` Ctrl+` `` (backtick)
   - Run `npm run dev` here

3. **View Console Logs:**
   - Open browser DevTools (F12)
   - Go to Console tab
   - See `[v0]` logs for debugging

## Next Steps

1. **Test the app**: Browse through all pages to see your data
2. **View Supabase Dashboard**: Go to https://supabase.com/dashboard to see your database
3. **Deploy to Vercel**: When ready, push to GitHub and deploy on Vercel

## Need Help?

- Check browser console (F12) for error messages
- Make sure `.env.local` file exists with correct values
- Restart dev server after changing environment variables
- Verify you're connected to the internet (Supabase is cloud-based)
