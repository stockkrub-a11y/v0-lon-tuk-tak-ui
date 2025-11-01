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
            sanitized = {k.lower(): v for k, v in sanitized.items()}
            return sanitized        

        total_records = len(data) if isinstance(data, list) else 1
        print(f"[DB] Inserting {total_records} records into {table_name}")

        # Apply sanitization
        if isinstance(data, list):
            clean_data = [sanitize_record(rec) for rec in data]
        else:
            clean_data = sanitize_record(data)

        # If it's a list of records, handle batches efficiently
        if isinstance(clean_data, list):
            # Fetch table column names from the database to avoid inserting unknown columns
            try:
                rpc_query = (
                    "SELECT column_name FROM information_schema.columns "
                    f"WHERE table_name = '{table_name}'"
                )
                schema_res = supabase.rpc('exec_sql', {'query': rpc_query}).execute()
                schema_cols = []
                if schema_res and getattr(schema_res, 'data', None):
                    schema_cols = [r['column_name'] for r in schema_res.data if 'column_name' in r]
                # Build lookup maps (case-insensitive)
                cols_set = set(schema_cols)
                cols_lower_map = {c.lower(): c for c in schema_cols}
                if len(schema_cols) == 0:
                    print(f"[DB] Warning: could not fetch schema for table '{table_name}', proceeding without filtering")
                else:
                    # Filter each record to only include columns that exist in the table
                    filtered = []
                    dropped_count = 0
                    for rec in clean_data:
                        new_rec = {}
                        for k, v in rec.items():
                            if k in cols_set:
                                new_rec[k] = v
                            else:
                                mapped = cols_lower_map.get(k.lower())
                                if mapped:
                                    new_rec[mapped] = v
                                else:
                                    dropped_count += 1
                        filtered.append(new_rec)
                    clean_data = filtered
                    if dropped_count > 0:
                        print(f"[DB] Notice: dropped {dropped_count} fields that don't exist in '{table_name}' before insert")
            except Exception as e:
                print(f"[DB] Warning: failed to fetch/filter schema for table '{table_name}': {e}")
            # Increase batch size for better performance
            batch_size = 2000
            total_batches = (len(clean_data) + batch_size - 1) // batch_size
            
            # If this is base_data table, optimize the deletion process
            if table_name == 'base_data':
                try:
                    # Extract unique product SKUs
                    product_skus = list(set(
                        record['product_sku'] 
                        for record in clean_data 
                        if 'product_sku' in record
                    ))
                    
                    # Delete in chunks of 100 SKUs for better performance
                    sku_batch_size = 100
                    print(f"[DB] Clearing existing data for {len(product_skus)} products...")
                    for i in range(0, len(product_skus), sku_batch_size):
                        sku_batch = product_skus[i:i + sku_batch_size]
                        supabase.table(table_name)\
                            .delete()\
                            .in_('product_sku', sku_batch)\
                            .execute()
                    print("[DB] ✅ Existing data cleared")
                except Exception as e:
                    print(f"[DB] Warning: Failed to delete existing records: {str(e)}")
            
            # Insert in optimized batches with progress tracking
            print(f"[DB] Starting bulk insert of {len(clean_data)} records in {total_batches} batches")
            import time
            start_time = time.time()
            
            for i in range(0, len(clean_data), batch_size):
                batch = clean_data[i:i + batch_size]
                batch_num = i//batch_size + 1
                
                # Calculate progress and ETA
                progress = (batch_num / total_batches) * 100
                elapsed = time.time() - start_time
                eta = (elapsed / batch_num) * (total_batches - batch_num) if batch_num > 0 else 0
                
                print(f"[DB] Processing batch {batch_num}/{total_batches} ({progress:.1f}%) - ETA: {eta:.1f}s")
                result = supabase.table(table_name).insert(batch).execute()
                
                records_processed = min(i + batch_size, len(clean_data))
                rate = records_processed / (time.time() - start_time)
                print(f"[DB] ✅ Batch {batch_num} complete - {rate:.0f} records/sec")
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
        # Use key column check based on table name
        if match_value == '*' or match_value is None:
            if table_name == 'forecast_output':
                # For forecast_output, use forecast_date to match all rows
                # Setting a date far in the past ensures we match all records
                result = supabase.table(table_name).delete().gte('forecast_date', '1900-01-01').execute()
            else:
                # For other tables with 'id' primary key
                result = supabase.table(table_name).delete().neq('id', 0).execute()
        else:
            result = supabase.table(table_name).delete().eq(match_column, match_value).execute()
        return result.data
    except Exception as e:
        print(f"❌ Delete failed: {str(e)}")
        return None
