# 🚨 URGENT: Fix Database and Backend Issues

## Problem Summary
Your upload is failing due to two issues:
1. **Database constraint**: `product_name` column doesn't allow NULL values
2. **Backend parsing issue**: Excel metadata rows are being inserted as products

## Step 1: Fix Database Constraints (REQUIRED)

Run this SQL script in your Supabase SQL Editor:

1. Go to: https://julumxzweprvvcnealal.supabase.co (your Supabase dashboard)
2. Click **SQL Editor** in the left sidebar
3. Click **New Query**
4. Copy and paste the contents of `scripts/02_fix_base_stock_constraints.sql`
5. Click **Run** or press `Ctrl+Enter`

This will:
- Allow NULL values in `product_name`, `product_sku`, and `หมวดหมู่` columns
- Add a constraint to ensure at least one identifier exists
- Create indexes for better performance

## Step 2: Fix Backend Excel Parsing (REQUIRED)

Your backend is reading Excel metadata rows as product data. You need to filter these out.

### In your Backend.py file, find the upload function and add filtering:

\`\`\`python
# After reading the Excel file, filter out metadata rows
def clean_dataframe(df):
    """Remove metadata rows from Excel export"""
    # Remove rows where product_sku contains metadata keywords
    metadata_keywords = ['Exported by', 'Date Time', 'Generated', 'Report']
    df = df[~df['product_sku'].astype(str).str.contains('|'.join(metadata_keywords), na=False)]
    
    # Remove rows where product_name is NULL or empty
    df = df[df['product_name'].notna()]
    df = df[df['product_name'].astype(str).str.strip() != '']
    
    # Remove rows where product_sku is NULL or empty
    df = df[df['product_sku'].notna()]
    df = df[df['product_sku'].astype(str).str.strip() != '']
    
    return df

# Apply this function after reading your Excel files:
stock_df = pd.read_excel(stock_file)
stock_df = clean_dataframe(stock_df)
\`\`\`

## Step 3: Environment Variables (Already Set)

Your Supabase credentials are already configured in the v0 environment:
- ✅ NEXT_PUBLIC_SUPABASE_URL
- ✅ NEXT_PUBLIC_SUPABASE_ANON_KEY
- ✅ SUPABASE_URL
- ✅ SUPABASE_ANON_KEY

## Step 4: Test Upload

After completing Steps 1 and 2:
1. Restart your backend server
2. Refresh your frontend (localhost:3000)
3. Try uploading your files again

## Common Issues

### Issue: "null value in column violates not-null constraint"
**Solution**: Run the SQL script from Step 1

### Issue: Invalid data like "Exported by" or "Date Time" in products
**Solution**: Add the filtering function from Step 2 to your backend

### Issue: Emojis not displaying correctly
**Solution**: Ensure your database encoding is UTF-8 (should be default in Supabase)

## Need Help?

If you still have issues after these steps:
1. Check backend logs for specific error messages
2. Verify the SQL script ran successfully (no errors in Supabase SQL Editor)
3. Ensure your Excel files have the correct format (product_name, product_sku, stock_level columns)
