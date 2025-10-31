"""
Initialize the forecast_output table in Supabase
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize Supabase client
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    # Read the SQL file
    with open('create_forecast_output_table.sql', 'r') as f:
        sql = f.read()
    
    try:
        # Execute the SQL using RPC
        result = supabase.rpc(
            'exec_sql',
            {'query': sql}
        ).execute()
        
        print("✅ forecast_output table created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create forecast_output table: {str(e)}")
        return False

if __name__ == "__main__":
    main()
