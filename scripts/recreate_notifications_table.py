import os
from DB_server import supabase

def drop_and_recreate_notifications_table():
    try:
        print("Dropping stock_notifications table...")
        supabase.table('stock_notifications').delete().neq('id', 0).execute()
        
        print("Reading SQL file...")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(current_dir, 'create_stock_notifications_table.sql')
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
            
        # Replace table creation with DROP and CREATE
        sql = """
        DROP TABLE IF EXISTS stock_notifications;
        """ + sql
            
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
                    
        print("\n✅ Table recreated successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Error recreating table: {e}")
        return False

if __name__ == "__main__":
    drop_and_recreate_notifications_table()