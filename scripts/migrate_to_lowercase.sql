-- Drop old columns from stock_notifications
ALTER TABLE stock_notifications
DROP COLUMN IF EXISTS "Product",
DROP COLUMN IF EXISTS "Stock",
DROP COLUMN IF EXISTS "Last_Stock",
DROP COLUMN IF EXISTS "Decrease_Rate(%)",
DROP COLUMN IF EXISTS "Weeks_To_Empty",
DROP COLUMN IF EXISTS "MinStock",
DROP COLUMN IF EXISTS "Buffer",
DROP COLUMN IF EXISTS "Reorder_Qty",
DROP COLUMN IF EXISTS "Status",
DROP COLUMN IF EXISTS "Description";

-- Add new lowercase columns to stock_notifications
ALTER TABLE stock_notifications
ADD COLUMN IF NOT EXISTS product_name VARCHAR(255) NOT NULL DEFAULT '',
ADD COLUMN IF NOT EXISTS product_sku VARCHAR(255) NOT NULL DEFAULT '',
ADD COLUMN IF NOT EXISTS category VARCHAR(255),
ADD COLUMN IF NOT EXISTS stock_level INTEGER NOT NULL DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_stock INTEGER NOT NULL DEFAULT 0,
ADD COLUMN IF NOT EXISTS decrease_rate NUMERIC(10, 2),
ADD COLUMN IF NOT EXISTS weeks_to_empty NUMERIC(10, 2),
ADD COLUMN IF NOT EXISTS min_stock INTEGER,
ADD COLUMN IF NOT EXISTS reorder_qty INTEGER,
ADD COLUMN IF NOT EXISTS status VARCHAR(50),
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Update base_stock table
ALTER TABLE base_stock
DROP COLUMN IF EXISTS "หมวดหมู่";

ALTER TABLE base_stock
ADD COLUMN IF NOT EXISTS category VARCHAR(255);

-- Add constraints
ALTER TABLE base_stock
ALTER COLUMN product_sku SET NOT NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_stock_notifications_product_sku
ON stock_notifications(product_sku);

CREATE INDEX IF NOT EXISTS idx_base_stock_product_sku
ON base_stock(product_sku);