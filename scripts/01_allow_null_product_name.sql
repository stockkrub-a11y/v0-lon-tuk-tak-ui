-- Allow NULL values in product_name column to handle emojis and special characters
-- This fixes the NotNullViolation error when uploading products with emojis

-- Alter base_stock table to allow NULL in product_name
ALTER TABLE base_stock 
ALTER COLUMN product_name DROP NOT NULL;

-- Add a comment explaining why NULL is allowed
COMMENT ON COLUMN base_stock.product_name IS 'Product name - allows NULL to handle special characters and emojis';

-- Optional: Update any existing NULL values to empty string if needed
-- UPDATE base_stock SET product_name = '' WHERE product_name IS NULL;
