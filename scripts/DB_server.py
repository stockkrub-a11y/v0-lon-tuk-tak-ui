from supabase import create_client, Client
import pandas as pd
from dotenv import load_dotenv
import os

# ------------------------------------------------------
# ⚙️ Load environment variables
# ------------------------------------------------------
load_dotenv()

# ------------------------------------------------------
# 🔗 Create Supabase Client
# ------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = supabase.table('base_stock').select("count").limit(1).execute()
    if response.data is not None:
        print("✅ Connected to Supabase successfully")
    else:
        print("⚠️ Connected but no response")
except Exception as e:
    print("❌ Supabase connection failed:", e)
    supabase = None

def execute_query(query: str, params: dict = None) -> pd.DataFrame:
    """
    Execute a query using Supabase and return results as a DataFrame
    """
    try:
        # For SELECT queries
        if query.lower().strip().startswith('select'):
            table_name = query.lower().split('from')[1].split()[0].strip()
            result = supabase.table(table_name).select('*').execute()
            return pd.DataFrame(result.data)
            
        # For CREATE TABLE queries
        elif query.lower().strip().startswith('create table'):
            # Extract table name from CREATE TABLE query
            table_name = query.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
            print(f"[DB] Creating table {table_name}")
            
            result = supabase.rpc(
                'exec_sql',
                {'query': query}
            ).execute()
            
            print(f"[DB] ✅ Table {table_name} created successfully")
            return pd.DataFrame()
            
        else:
            print("[DB] Unsupported query type")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Query failed: {str(e)}")
        return pd.DataFrame()

def insert_data(table_name: str, data: dict | list):
    """
    Insert data into a table using Supabase
    """
    try:
        # Normalize and sanitize records to be JSON-safe (replace NaN with None, timestamps -> ISO)
        def sanitize_record(rec):
            import pandas as _pd
            from datetime import datetime as _dt
            sanitized = {}
            for k, v in rec.items():
                try:
                    if _pd.isna(v):
                        sanitized[k] = None
                    elif isinstance(v, _pd.Timestamp):
                        sanitized[k] = v.isoformat()
                    elif isinstance(v, _dt):
                        sanitized[k] = v.isoformat()
                    else:
                        # Convert numpy scalar types to native python types
                        try:
                            import numpy as _np
                            if isinstance(v, (_np.integer, _np.floating, _np.bool_)):
                                sanitized[k] = v.item()
                            else:
                                sanitized[k] = v
                        except Exception:
                            sanitized[k] = v
                except Exception:
                    # Fallback: set None for problematic values
                    sanitized[k] = None
            return sanitized

        total_records = len(data) if isinstance(data, list) else 1
        print(f"[DB] Inserting {total_records} records into {table_name}")

        # Apply sanitization
        if isinstance(data, list):
            clean_data = [sanitize_record(rec) for rec in data]
        else:
            clean_data = sanitize_record(data)

        # If it's a list of records, insert in batches of 1000
        if isinstance(clean_data, list) and len(clean_data) > 1000:
            batch_size = 1000
            for i in range(0, len(clean_data), batch_size):
                batch = clean_data[i : i + batch_size]
                print(f"[DB] Inserting batch {i//batch_size + 1}/{(len(clean_data) + batch_size - 1)//batch_size}")
                result = supabase.table(table_name).insert(batch).execute()
                print(f"[DB] ✅ Batch {i//batch_size + 1} inserted successfully")
        else:
            result = supabase.table(table_name).insert(clean_data).execute()

        print(f"[DB] ✅ Successfully inserted {total_records} records into {table_name}")
        return result.data
    except Exception as e:
        print(f"[DB] ❌ Insert failed: {str(e)}")
        # Print sample data for debugging
        if isinstance(data, list) and len(data) > 0:
            print(f"[DB] First record structure:")
            for key, value in data[0].items():
                print(f"   {key}: {type(value)} = {value}")
        elif isinstance(data, dict):
            print(f"[DB] Record structure:")
            for key, value in data.items():
                print(f"   {key}: {type(value)} = {value}")
        import traceback
        traceback.print_exc()
        return None

def update_data(table_name: str, data: dict, match_column: str, match_value: any):
    """
    Update data in a table using Supabase
    """
    try:
        result = supabase.table(table_name).update(data).eq(match_column, match_value).execute()
        return result.data
    except Exception as e:
        print(f"❌ Update failed: {str(e)}")
        return None

def delete_data(table_name: str, match_column: str, match_value: any):
    """
    Delete data from a table using Supabase
    """
    try:
        # Special case: if match_value == '*' or None, delete all rows from the table
        # PostgREST/Supabase rejects DELETE without a WHERE clause; use a safe predicate
        if match_value == '*' or match_value is None:
            # Assume table has integer primary key 'id' starting from 1; delete rows where id != 0
            result = supabase.table(table_name).delete().neq('id', 0).execute()
        else:
            result = supabase.table(table_name).delete().eq(match_column, match_value).execute()
        return result.data
    except Exception as e:
        print(f"❌ Delete failed: {str(e)}")
        return None
