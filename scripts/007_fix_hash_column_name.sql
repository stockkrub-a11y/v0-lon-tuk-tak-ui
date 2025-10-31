-- Fix the '#' column name issue by creating a proper column
-- PostgreSQL doesn't handle '#' well as a column name

-- Add row_number column if it doesn't exist
ALTER TABLE base_stock 
ADD COLUMN IF NOT EXISTS row_number INTEGER;

-- If there's somehow a '#' column (quoted identifier), rename it
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'base_stock' 
        AND column_name = '#'
    ) THEN
        ALTER TABLE base_stock RENAME COLUMN "#" TO row_number;
    END IF;
END $$;

-- Add comment to explain the column
COMMENT ON COLUMN base_stock.row_number IS 'Row number from Excel file (originally # column)';
