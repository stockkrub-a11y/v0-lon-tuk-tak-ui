from DB_server import supabase, execute_query
import pandas as pd

def test_supabase_connection():
    print("\nTesting Supabase connection...")
    
    # Test direct table access
    print("\nTesting table access...")
    try:
        result = supabase.table('base_stock').select("*").limit(5).execute()
        df = pd.DataFrame(result.data)
        print(f"✅ Successfully fetched {len(df)} rows from base_stock")
        if not df.empty:
            print("\nSample data:")
            print(df.head())
    except Exception as e:
        print(f"❌ Table access failed: {str(e)}")
    
    # Test query execution wrapper
    print("\nTesting query execution...")
    try:
        df = execute_query("SELECT * FROM base_stock LIMIT 5")
        print(f"✅ Query execution returned {len(df)} rows")
    except Exception as e:
        print(f"❌ Query execution failed: {str(e)}")

if __name__ == "__main__":
    test_supabase_connection()
