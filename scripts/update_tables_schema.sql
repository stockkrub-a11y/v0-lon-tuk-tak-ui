-- Add missing columns to stock_notifications table
ALTER TABLE stock_notifications
ADD COLUMN IF NOT EXISTS product_sku VARCHAR(255),
ADD COLUMN IF NOT EXISTS category VARCHAR(255),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_stock_notifications_product_sku
ON stock_notifications(product_sku);

CREATE INDEX IF NOT EXISTS idx_stock_notifications_category
ON stock_notifications(category);

-- Update category column name in base_stock if it exists as หมวดหมู่
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'base_stock'
        AND column_name = 'หมวดหมู่'
    ) THEN
        ALTER TABLE base_stock RENAME COLUMN "หมวดหมู่" TO category;
    END IF;
END $$;