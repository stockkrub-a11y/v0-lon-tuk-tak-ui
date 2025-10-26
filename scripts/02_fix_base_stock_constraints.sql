-- Fix base_stock table to allow NULL values in product_name column
-- This is needed because some products have emojis or special characters
-- that may not be properly handled during upload

-- Allow NULL in product_name column
ALTER TABLE base_stock 
ALTER COLUMN product_name DROP NOT NULL;

-- Allow NULL in product_sku column (in case of data issues)
ALTER TABLE base_stock 
ALTER COLUMN product_sku DROP NOT NULL;

-- Allow NULL in หมวดหมู่ (category) column
ALTER TABLE base_stock 
ALTER COLUMN "หมวดหมู่" DROP NOT NULL;

-- Add a check constraint to ensure at least product_name OR product_sku exists
-- This prevents completely empty rows
ALTER TABLE base_stock 
ADD CONSTRAINT base_stock_has_identifier 
CHECK (product_name IS NOT NULL OR product_sku IS NOT NULL);

-- Create an index on product_name for better query performance
CREATE INDEX IF NOT EXISTS idx_base_stock_product_name 
ON base_stock(product_name) 
WHERE product_name IS NOT NULL;

-- Create an index on product_sku for better query performance
CREATE INDEX IF NOT EXISTS idx_base_stock_product_sku 
ON base_stock(product_sku) 
WHERE product_sku IS NOT NULL;
