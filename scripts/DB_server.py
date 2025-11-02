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

supabase = None
SUPABASE_AVAILABLE = False

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Don't test connection on import - let it fail gracefully when actually used
        print("✅ Supabase client initialized")
        SUPABASE_AVAILABLE = True
    except Exception as e:
        print(f"⚠️ Supabase client initialization failed: {e}")
        supabase = None
        SUPABASE_AVAILABLE = False
else:
    print("⚠️ Supabase credentials not found (SUPABASE_URL or SUPABASE_KEY missing)")
    print("   Database features will be disabled until credentials are added.")
    supabase = None
    SUPABASE_AVAILABLE = False

def execute_query(query: str, params: dict = None) -> pd.DataFrame:
    """
    Execute a query using Supabase and return results as a DataFrame
    """
    if not SUPABASE_AVAILABLE or supabase is None:
        print("⚠️ Supabase not available - cannot execute query")
        return pd.DataFrame()
    
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
    if not SUPABASE_AVAILABLE or supabase is None:
        print("⚠️ Supabase not available - cannot insert data")
        return None
    
    try:
        # Import required libraries inside function for reliability
        import pandas as _pd
        import numpy as _np
        from datetime import datetime as _dt
        
        def sanitize_value(v):
            """Helper function to sanitize a single value"""
            if v is None:
                return None
            elif _pd.isna(v):
                return None
            elif isinstance(v, (_pd.Timestamp, _dt)):
                return v.isoformat()
            elif isinstance(v, (_np.integer, _np.int64, _np.int32)):
                return int(v)
            elif isinstance(v, (_np.floating, _np.float64, _np.float32)):
                return float(v)
            elif isinstance(v, _np.bool_):
                return bool(v)
            elif isinstance(v, (str, int, float, bool)):
                return v
            elif isinstance(v, bytes):
                return v.decode('utf-8')
            else:
                try:
                    # Try converting to string as last resort
                    return str(v)
                except:
                    return None

        def sanitize_record(rec):
            """Helper function to sanitize a single record"""
            if not isinstance(rec, dict):
                return rec
            
            # Define integer fields that should be converted from float
            integer_fields = {'stock_level', 'last_stock', 'min_stock', 'reorder_qty', 'unchanged_counter'}
            
            sanitized = {}
            for k, v in rec.items():
                try:
                    # Handle float to int conversion for specific fields
                    if k in integer_fields and v is not None and not _pd.isna(v):
                        try:
                            sanitized[k] = int(float(v))
                        except (ValueError, TypeError):
                            print(f"[DB] Warning: Could not convert {k}={v} to integer")
                            sanitized[k] = None
                    else:
                        sanitized[k] = sanitize_value(v)
                except Exception as e:
                    print(f"[DB] Warning: Failed to sanitize value for key {k}: {str(e)}")
                    sanitized[k] = None
            return sanitized

        # Get record count for logging
        total_records = len(data) if isinstance(data, list) else 1
        print(f"[DB] Inserting {total_records} records into {table_name}")

        # Apply sanitization
        if isinstance(data, list):
            clean_data = []
            for idx, record in enumerate(data):
                try:
                    clean_record = sanitize_record(record)
                    clean_data.append(clean_record)
                except Exception as e:
                    print(f"[DB] Warning: Failed to sanitize record {idx}: {str(e)}")
                    continue
        else:
            clean_data = sanitize_record(data)

        if not clean_data or (isinstance(clean_data, list) and not clean_data):
            raise ValueError("No valid records to insert after sanitization")

        # Insert in batches if needed
        if isinstance(clean_data, list) and len(clean_data) > 1000:
            batch_size = 1000
            results = []
            
            for i in range(0, len(clean_data), batch_size):
                batch = clean_data[i:i + batch_size]
                if not batch:
                    continue
                    
                print(f"[DB] Inserting batch {i//batch_size + 1}/{(len(clean_data) + batch_size - 1)//batch_size}")
                
                try:
                    result = supabase.table(table_name).insert(batch).execute()
                    print(f"[DB] ✅ Batch {i//batch_size + 1} inserted successfully")
                    if result and result.data:
                        results.extend(result.data)
                except Exception as e:
                    print(f"[DB] ❌ Batch {i//batch_size + 1} insert failed: {str(e)}")
                    continue
            
            if not results:
                raise Exception("All batch inserts failed")
                
            return results
            
        else:
            result = supabase.table(table_name).insert(clean_data).execute()
            print(f"[DB] ✅ Successfully inserted {total_records} records into {table_name}")
            return result.data

    except Exception as e:
        print(f"[DB] ❌ Insert failed: {str(e)}")
        
        # Enhanced error debugging
        print("\n[DB] Debug Information:")
        print("-" * 50)
        
        if isinstance(data, list) and data:
            print("Sample record before sanitization:")
            sample = data[0]
            if isinstance(sample, dict):
                for k, v in sample.items():
                    print(f"  {k}: {type(v)} = {v}")
        elif isinstance(data, dict):
            print("Record before sanitization:")
            for k, v in data.items():
                print(f"  {k}: {type(v)} = {v}")
                
        print("-" * 50)
        import traceback
        traceback.print_exc()
        print("-" * 50)
        return None

def update_data(table_name: str, data: dict, match_column: str, match_value: any):
    """
    Update data in a table using Supabase
    """
    if not SUPABASE_AVAILABLE or supabase is None:
        print("⚠️ Supabase not available - cannot update data")
        return None
    
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
    if not SUPABASE_AVAILABLE or supabase is None:
        print("⚠️ Supabase not available - cannot delete data")
        return None
    
    try:
        # Special case: if match_value == '*' or None, delete all rows from the table
        if match_value == '*' or match_value is None:
            # Use table-specific logic for deleting all rows
            if table_name == 'base_data':
                # For base_data, use sales_year >= 0 which matches all rows
                result = supabase.table(table_name).delete().gte('sales_year', 0).execute()
            elif table_name == 'base_stock':
                # For base_stock, use stock_level >= 0 which matches all rows
                result = supabase.table(table_name).delete().gte('stock_level', 0).execute()
            elif table_name == 'stock_notifications':
                # For stock_notifications, use a condition that matches all rows
                result = supabase.table(table_name).delete().neq('product_sku', None).execute()
            elif table_name in ['forecasts', 'forecast_output']:
                # For forecast tables, use a condition that matches all rows
                result = supabase.table(table_name).delete().neq('product_sku', None).execute()
            else:
                # For other tables with 'id' column, use id >= 0
                result = supabase.table(table_name).delete().gte('id', 0).execute()
        else:
            result = supabase.table(table_name).delete().eq(match_column, match_value).execute()
        
        print(f"[DB] ✅ Successfully deleted from {table_name}")
        return result.data
    except Exception as e:
        print(f"❌ Delete failed: {e}")
        return None
