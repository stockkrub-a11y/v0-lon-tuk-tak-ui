# Fix Database Schema for Product Names with Emojis

## Problem
The `base_stock` table has a NOT NULL constraint on the `product_name` column, which causes errors when uploading products with emojis or special characters.

## Solution
Run the SQL script to allow NULL values in the `product_name` column.

## Steps

### Option 1: Run SQL Script in Supabase Dashboard

1. Go to your Supabase dashboard: https://supabase.com/dashboard/project/oscypcfrridgqwgqvdsl
2. Click on "SQL Editor" in the left sidebar
3. Click "New Query"
4. Copy and paste the contents of `scripts/01_allow_null_product_name.sql`
5. Click "Run" to execute the script

### Option 2: Run from v0 (if you have the script execution feature)

The SQL script is already in your project at `scripts/01_allow_null_product_name.sql`. If v0 supports running SQL scripts, it will execute automatically.

## What This Does

- Removes the NOT NULL constraint from `base_stock.product_name`
- Allows products with emojis and special characters to be uploaded
- Adds a comment explaining why NULL is allowed

## After Running the Script

1. Try uploading your files again
2. Products with emojis should now upload successfully
3. The notifications page should display correctly

## Verification

Run this query to verify the change:

\`\`\`sql
SELECT column_name, is_nullable, data_type
FROM information_schema.columns
WHERE table_name = 'base_stock' AND column_name = 'product_name';
\`\`\`

You should see `is_nullable = 'YES'`.
