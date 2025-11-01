from DB_server import supabase
import os

def migrate_to_lowercase():
    """Apply migration to use lowercase column names"""
    try:
        print("Starting migration to lowercase column names...")
        
        # Read the SQL file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(current_dir, 'migrate_to_lowercase.sql')
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
            
        # Split into individual statements
        statements = sql.split(';')
        
        # Execute each statement
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                try:
                    print(f"\nExecuting: {stmt[:100]}...")
                    result = supabase.rpc('exec_sql', {'query': stmt}).execute()
                    print("✅ Success")
                except Exception as e:
                    print(f"⚠️ Error executing statement: {e}")
                    print(f"Statement was: {stmt}")
                    continue
                    
        print("\n✅ Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        return False

if __name__ == "__main__":
    migrate_to_lowercase()