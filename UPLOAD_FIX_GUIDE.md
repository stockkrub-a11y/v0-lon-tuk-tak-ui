# Upload Fix Guide

## Issues Identified

1. **Supabase Client Error**: Environment variables not accessible
2. **Database Constraint Error**: `product_name` column doesn't allow NULL values
3. **Backend Upload Failing**: Excel metadata rows being inserted as products

## Step-by-Step Fix

### 1. Restart Dev Server (CRITICAL)

Environment variables are only loaded when the dev server starts. You MUST restart:

\`\`\`bash
# Stop the server (Ctrl+C)
# Then restart:
npm run dev
\`\`\`

After restarting, check the browser console. You should see:
\`\`\`
[v0] Supabase URL: ✓ Set
[v0] Supabase Key: ✓ Set
[v0] Supabase client created successfully
\`\`\`

If you still see "✗ Missing", the environment variables aren't set correctly.

### 2. Fix Database Constraints

Run this SQL script in your Supabase SQL Editor:

\`\`\`sql
ALTER TABLE base_stock ALTER COLUMN product_name DROP NOT NULL;
ALTER TABLE all_products ALTER COLUMN product_name DROP NOT NULL;
ALTER TABLE stock_notifications ALTER COLUMN "Product" DROP NOT NULL;
\`\`\`

Or use the script file: `scripts/03_fix_product_name_constraint.sql`

### 3. Verify Environment Variables

Make sure these are set in the v0 Vars section:

- `NEXT_PUBLIC_SUPABASE_URL` = `https://julumxzweprvvcnealal.supabase.co`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1bHVteHp3ZXBydnZjbmVhbGFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE1MDU4OTksImV4cCI6MjA3NzA4MTg5OX0.AKluaTWZShPmCcsQZqKJNyz8jC7nwgZEqz0t3mTimBg`

### 4. Fix Backend Excel Parsing (If Using Backend)

Your backend is reading Excel metadata rows as product data. Add this filter to your backend code:

\`\`\`python
def is_metadata_row(row):
    """Filter out Excel metadata rows"""
    metadata_keywords = [
        'exported by',
        'date time',
        'pajaralive@gmail.com',
        'generated on',
        'report date'
    ]
    
    # Check if any column contains metadata keywords
    for value in row.values():
        if isinstance(value, str):
            if any(keyword in value.lower() for keyword in metadata_keywords):
                return True
    return False

# When processing Excel data:
df = pd.read_excel(file)
df = df[~df.apply(is_metadata_row, axis=1)]  # Filter out metadata rows
\`\`\`

## Testing the Fix

### Test 1: Stocks Page Upload
1. Go to `/dashboard/stocks`
2. Click "Upload Product List" or "Upload Sale Stock"
3. Select your Excel files
4. Click "Upload"
5. Check console for success message

### Test 2: Notifications Page Upload
1. Go to `/dashboard/notifications`
2. Click "Upload Current Stock"
3. Select your stock file
4. Click "Upload & Generate Report"
5. Check for success message

## Common Errors and Solutions

### Error: "@supabase/ssr: Your project's URL and API key are required"
**Solution**: Restart dev server (Step 1)

### Error: "null value in column 'product_name' violates not-null constraint"
**Solution**: Run the SQL script (Step 2)

### Error: "Exported by pajaralive@gmail.com" appears as a product
**Solution**: Fix backend Excel parsing (Step 4)

### Error: Backend not responding
**Solution**: Make sure your FastAPI backend is running:
\`\`\`bash
python scripts/Backend.py
\`\`\`

## Upload Flow

### Using Backend (Recommended for ML Training):
1. Upload files on Stocks page
2. Backend processes files, trains ML model
3. Generates forecasts and updates database
4. Redirects to Predict page

### Using Supabase Direct (No ML Training):
1. Upload files on Notifications page
2. Frontend parses Excel files
3. Inserts data directly into Supabase
4. No ML training, just data storage

## Need Help?

If uploads still fail after following these steps:
1. Check browser console for detailed error messages
2. Check backend logs if using backend
3. Verify database schema in Supabase dashboard
4. Ensure all environment variables are set correctly
