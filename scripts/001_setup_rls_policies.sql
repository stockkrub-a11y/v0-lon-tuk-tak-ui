-- Disable RLS temporarily for stock management tables
-- Since there's no authentication system yet, we'll allow public access

-- Disable RLS on base_stock table
ALTER TABLE public.base_stock DISABLE ROW LEVEL SECURITY;

-- Disable RLS on base_data table  
ALTER TABLE public.base_data DISABLE ROW LEVEL SECURITY;

-- Disable RLS on stock_notifications table
ALTER TABLE public.stock_notifications DISABLE ROW LEVEL SECURITY;

-- Disable RLS on forecasts table
ALTER TABLE public.forecasts DISABLE ROW LEVEL SECURITY;

-- Disable RLS on all_products table
ALTER TABLE public.all_products DISABLE ROW LEVEL SECURITY;

-- Disable RLS on stock_data table
ALTER TABLE public.stock_data DISABLE ROW LEVEL SECURITY;

-- Disable RLS on forecast_output table
ALTER TABLE public.forecast_output DISABLE ROW LEVEL SECURITY;

-- Note: When you add authentication later, you should:
-- 1. Re-enable RLS: ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;
-- 2. Create policies: CREATE POLICY "policy_name" ON table_name FOR SELECT USING (true);
