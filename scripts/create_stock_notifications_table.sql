-- Create stock_notifications table to store notification results
CREATE TABLE IF NOT EXISTS stock_notifications (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    product_sku VARCHAR(255) NOT NULL,
    category VARCHAR(255),
    stock_level INTEGER NOT NULL,
    last_stock INTEGER NOT NULL,
    decrease_rate NUMERIC(10, 2),
    weeks_to_empty NUMERIC(10, 2),
    min_stock INTEGER,
    reorder_qty INTEGER,
    status VARCHAR(50),
    description TEXT,
    unchanged_counter NUMERIC(10, 2) DEFAULT 0,
    flag VARCHAR(50) DEFAULT 'stage',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_stock_notifications_created_at 
ON stock_notifications(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_stock_notifications_product_sku
ON stock_notifications(product_sku);

CREATE INDEX IF NOT EXISTS idx_stock_notifications_flag 
ON stock_notifications(flag);
