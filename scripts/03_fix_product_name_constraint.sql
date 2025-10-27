-- Fix the NOT NULL constraint on product_name in base_stock table
-- This allows products with emojis or missing names to be inserted

ALTER TABLE base_stock 
ALTER COLUMN product_name DROP NOT NULL;

-- Also fix it in other tables that might have the same issue
ALTER TABLE all_products 
ALTER COLUMN product_name DROP NOT NULL;

ALTER TABLE stock_notifications 
ALTER COLUMN "Product" DROP NOT NULL;

-- Add a comment to document this change
COMMENT ON COLUMN base_stock.product_name IS 'Product name - can be NULL for products with special characters or missing names';
