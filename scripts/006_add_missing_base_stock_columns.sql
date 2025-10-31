-- Add missing columns to base_stock table to match backend data structure

-- Add row number column (# from Excel)
ALTER TABLE base_stock 
ADD COLUMN IF NOT EXISTS row_number INTEGER;

-- Add category column (already exists as หมวดหมู่, but backend sends 'category')
ALTER TABLE base_stock 
ADD COLUMN IF NOT EXISTS category VARCHAR;

-- Add subcategory column
ALTER TABLE base_stock 
ADD COLUMN IF NOT EXISTS subcategory VARCHAR;

-- Add week_date column
ALTER TABLE base_stock 
ADD COLUMN IF NOT EXISTS week_date DATE;

-- Add uploaded_at column
ALTER TABLE base_stock 
ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP;

-- Create index on product_sku for faster lookups
CREATE INDEX IF NOT EXISTS idx_base_stock_product_sku ON base_stock(product_sku);

-- Create index on week_date for time-based queries
CREATE INDEX IF NOT EXISTS idx_base_stock_week_date ON base_stock(week_date);
