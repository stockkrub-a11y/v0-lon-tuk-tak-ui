CREATE TABLE IF NOT EXISTS forecast_output (
    id SERIAL PRIMARY KEY,
    product_sku VARCHAR(255) NOT NULL,
    forecast_date DATE NOT NULL,
    predicted_sales INTEGER NOT NULL,
    current_sales INTEGER NOT NULL,
    current_date_col DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);