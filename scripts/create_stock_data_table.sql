-- Create stock_data table for tracking inventory levels over time
CREATE TABLE IF NOT EXISTS stock_data (
    id SERIAL PRIMARY KEY,
    week_date DATE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    product_sku VARCHAR(100),
    stock_level INTEGER NOT NULL,
    min_stock INTEGER DEFAULT 0,
    buffer INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(week_date, product_name)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_stock_data_week_date ON stock_data(week_date DESC);
CREATE INDEX IF NOT EXISTS idx_stock_data_product ON stock_data(product_name);

-- Insert sample data if table is empty (for testing)
INSERT INTO stock_data (week_date, product_name, product_sku, stock_level, min_stock, buffer)
SELECT 
    CURRENT_DATE - INTERVAL '14 days' as week_date,
    product_name,
    product_sku,
    FLOOR(RANDOM() * 100 + 50)::INTEGER as stock_level,
    FLOOR(RANDOM() * 20 + 10)::INTEGER as min_stock,
    FLOOR(RANDOM() * 10 + 5)::INTEGER as buffer
FROM all_products
WHERE NOT EXISTS (SELECT 1 FROM stock_data LIMIT 1);

-- Insert more recent data (7 days ago)
INSERT INTO stock_data (week_date, product_name, product_sku, stock_level, min_stock, buffer)
SELECT 
    CURRENT_DATE - INTERVAL '7 days' as week_date,
    product_name,
    product_sku,
    FLOOR(RANDOM() * 80 + 30)::INTEGER as stock_level,
    min_stock,
    buffer
FROM all_products ap
LEFT JOIN stock_data sd ON sd.product_name = ap.product_name AND sd.week_date = CURRENT_DATE - INTERVAL '14 days'
WHERE NOT EXISTS (
    SELECT 1 FROM stock_data 
    WHERE week_date = CURRENT_DATE - INTERVAL '7 days'
    LIMIT 1
);

-- Insert current data (today)
INSERT INTO stock_data (week_date, product_name, product_sku, stock_level, min_stock, buffer)
SELECT 
    CURRENT_DATE as week_date,
    product_name,
    product_sku,
    FLOOR(RANDOM() * 60 + 10)::INTEGER as stock_level,
    min_stock,
    buffer
FROM all_products ap
LEFT JOIN stock_data sd ON sd.product_name = ap.product_name AND sd.week_date = CURRENT_DATE - INTERVAL '7 days'
WHERE NOT EXISTS (
    SELECT 1 FROM stock_data 
    WHERE week_date = CURRENT_DATE
    LIMIT 1
);
