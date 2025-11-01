-- Create stock_notifications table to store notification results
CREATE TABLE IF NOT EXISTS stock_notifications (
    id SERIAL PRIMARY KEY,
    "Product" VARCHAR(255) NOT NULL,
    "Stock" INTEGER NOT NULL,
    "Last_Stock" INTEGER NOT NULL,
    "Decrease_Rate(%)" NUMERIC(10, 2),
    "Weeks_To_Empty" NUMERIC(10, 2),
    "MinStock" INTEGER,
    "Buffer" INTEGER,
    "Reorder_Qty" INTEGER,
    "Status" VARCHAR(50),
    "Description" TEXT,
    unchanged_counter NUMERIC(10, 2) DEFAULT 0,
    flag VARCHAR(50) DEFAULT 'stage',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_stock_notifications_created_at 
ON stock_notifications(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_stock_notifications_product 
ON stock_notifications("Product");

CREATE INDEX IF NOT EXISTS idx_stock_notifications_flag 
ON stock_notifications(flag);
