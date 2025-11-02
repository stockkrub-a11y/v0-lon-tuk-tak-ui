-- Update base_stock table schema
ALTER TABLE base_stock
RENAME COLUMN "หมวดหมู่" TO category;

-- Update base_stock table to have proper constraints
ALTER TABLE base_stock
ADD CONSTRAINT base_stock_required_fields
CHECK (
    product_name IS NOT NULL AND
    product_sku IS NOT NULL AND
    stock_level IS NOT NULL
);

-- Update stock_notifications table schema to use consistent column names
ALTER TABLE stock_notifications
RENAME COLUMN "Product" TO product_name;

ALTER TABLE stock_notifications
RENAME COLUMN "Stock" TO stock_level;

ALTER TABLE stock_notifications
RENAME COLUMN "Last_Stock" TO last_stock;

ALTER TABLE stock_notifications
RENAME COLUMN "Decrease_Rate(%)" TO decrease_rate;

ALTER TABLE stock_notifications
RENAME COLUMN "Weeks_To_Empty" TO weeks_to_empty;

ALTER TABLE stock_notifications
RENAME COLUMN "MinStock" TO min_stock;

ALTER TABLE stock_notifications
RENAME COLUMN "Reorder_Qty" TO reorder_qty;

ALTER TABLE stock_notifications
RENAME COLUMN "Status" TO status;

ALTER TABLE stock_notifications
RENAME COLUMN "Description" TO description;

-- Drop Buffer column since we'll handle it in application logic
ALTER TABLE stock_notifications
DROP COLUMN IF EXISTS "Buffer";

-- Add product_sku and category columns that were missing
ALTER TABLE stock_notifications
ADD COLUMN IF NOT EXISTS product_sku VARCHAR(255) NOT NULL DEFAULT '',
ADD COLUMN IF NOT EXISTS category VARCHAR(255);

-- Add index on product_sku
CREATE INDEX IF NOT EXISTS idx_stock_notifications_product_sku 
ON stock_notifications(product_sku);
