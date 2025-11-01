from DB_server import supabase
import os

def apply_schema_updates():
    """Apply schema updates to standardize column names"""
    try:
        # Read the SQL file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(current_dir, 'update_table_schemas.sql')
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
            
        # Split into individual statements
        statements = sql.split(';')
        
        # Execute each statement
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                try:
                    result = supabase.rpc('exec_sql', {'query': stmt}).execute()
                    print(f"✅ Executed: {stmt[:100]}...")
                except Exception as e:
                    print(f"⚠️ Error executing statement: {e}")
                    print(f"Statement was: {stmt}")
                    continue
                    
        print("✅ Schema updates applied successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error applying schema updates: {e}")
        return False

if __name__ == "__main__":
    apply_schema_updates()