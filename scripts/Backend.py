from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import pandas as pd
import io
import uvicorn
from DB_server import supabase, execute_query, insert_data, update_data, delete_data
import sys
import time
import joblib
from dotenv import load_dotenv
from supabase import create_client, Client
import os

# Load environment variables
load_dotenv()

try:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client initialized successfully")
        SUPABASE_AVAILABLE = True
    else:
        supabase = None
        print("⚠️  Supabase credentials not found. Database features will be disabled.")
        print("   Set SUPABASE_URL and SUPABASE_KEY environment variables to enable database.")
        SUPABASE_AVAILABLE = False
except Exception as e:
    supabase = None
    SUPABASE_AVAILABLE = False
    print(f"⚠️  Failed to initialize Supabase client: {str(e)}")
    print("   Database features will be disabled.")

# Import local modules
from Auto_cleaning import auto_cleaning
engine = None  # Deprecated: use Supabase client functions instead
from Predict import update_model_and_train, forcast_loop, Evaluate
from Notification import generate_stock_report, update_manual_values

# Initialize FastAPI app
app = FastAPI(title="Lon TukTak Stock Management API")

@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    print(f"\n{'='*80}", flush=True)
    print(f"🌐 REQUEST: {request.method} {request.url.path}", flush=True)
    print(f"{'='*80}", flush=True)
    sys.stdout.flush()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    print(f"✅ RESPONSE: {response.status_code} (took {process_time:.2f}s)", flush=True)
    print(f"{'='*80}\n", flush=True)
    sys.stdout.flush()
    
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "https://v0-lontuktak.final.vercel.app",
        "https://v0-lontuktak-final.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*80, flush=True)
    print("🚀 LON TUKTAK BACKEND STARTED", flush=True)
    print("="*80, flush=True)
    print(f"✅ Backend loaded from: {__file__}", flush=True)
    print(f"✅ Database engine available: {engine is not None}", flush=True)
    print("="*80 + "\n", flush=True)
    sys.stdout.flush()

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint - works even without database"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if SUPABASE_AVAILABLE else "not configured",
        "supabase_url_set": bool(os.getenv("SUPABASE_URL")),
        "supabase_key_set": bool(os.getenv("SUPABASE_KEY"))
    }
    return health_status

@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint"""
    print("\n" + "="*80, flush=True)
    print("🧪 TEST ENDPOINT CALLED", flush=True)
    print("="*80 + "\n", flush=True)
    sys.stdout.flush()
    return {"message": "Backend is working!", "timestamp": datetime.now().isoformat()}

@app.get("/api/db-test")
async def test_database():
    """Test database connection and query stock_notifications table"""
    print("\n" + "="*80, flush=True)
    print("DATABASE TEST ENDPOINT CALLED", flush=True)
    print("="*80, flush=True)
    sys.stdout.flush()
    
    result = {
        "engine_available": True,
        "connection_test": False,
        "table_exists": False,
        "row_count": 0,
        "sample_data": None,
        "columns": [],
        "error": None
    }
    try:
        # Test 1: Simple connection test
        print("Test 1: Testing Supabase connection...", flush=True)
        test_df = execute_query("SELECT * FROM stock_notifications LIMIT 1")
        result["connection_test"] = not test_df.empty
        print("✅ Supabase connection successful", flush=True)
        # Test 2: Check if table exists (if query returned data or not)
        result["table_exists"] = True
        # Test 3: Count rows
        count_df = execute_query("SELECT * FROM stock_notifications")
        result["row_count"] = len(count_df)
        # Test 4: Get column names
        result["columns"] = list(count_df.columns)
        # Test 5: Get sample data
        if not count_df.empty:
            sample_records = count_df.head(3).to_dict('records')
            for record in sample_records:
                for key, value in record.items():
                    if pd.notna(value) and isinstance(value, (pd.Timestamp, datetime)):
                        record[key] = str(value)
            result["sample_data"] = sample_records
        print("="*80 + "\n", flush=True)
        return result
    except Exception as e:
        result["error"] = str(e)
        print(f"ERROR in database test: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        return result

# ============================================================================
# NOTIFICATIONS ENDPOINTS
# ============================================================================

@app.get("/api/notifications")
async def get_notifications():
    """Get inventory notifications from stock_notifications table"""
    print("\n" + "="*80, flush=True)
    print("NOTIFICATIONS ENDPOINT CALLED", flush=True)
    print("="*80, flush=True)
    sys.stdout.flush()
    
    if not SUPABASE_AVAILABLE:
        print("⚠️  Supabase not available, returning empty notifications", flush=True)
        return []
    
    try:
        print("Supabase client: fetching notifications...", flush=True)
        df = execute_query("SELECT * FROM stock_notifications")
        if df.empty:
            return []
        notifications = df.to_dict('records')
        for notification in notifications:
            for key, value in notification.items():
                if pd.notna(value) and isinstance(value, (pd.Timestamp, datetime)):
                    notification[key] = str(value)
        return notifications
    except Exception as e:
        print(f"ERROR in get_notifications: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        return []

@app.get("/notifications/check_base_stock")
async def check_base_stock():
    """Check if base_stock table exists and has data"""
    try:
        print("[Backend] Checking base_stock table...")
        df = execute_query("SELECT * FROM base_stock")
        count = len(df)
        print(f"[Backend] base_stock exists with {count} rows")
        return {"exists": count > 0, "count": count}
    except Exception as e:
        print(f"[Backend] base_stock table doesn't exist or error: {str(e)}")
        return {"exists": False, "count": 0}

# --- Helper to load files with fallback headers ---
def load_file_with_fallback(file_content, possible_headers=[0,1,2,3]):
    """
    Try to load Excel/CSV file with multiple header row attempts.
    Returns (DataFrame, header_row_used)
    """
    column_mapping = {
        # SKU columns
        "รหัสสินค้า": "Product_SKU",
        "เลขอ้างอิง SKU (SKU Reference No.)": "Product_SKU",
        "Product_SKU": "Product_SKU",
        "SKU": "Product_SKU",
        "รหัส": "Product_SKU",
        "Code": "Product_SKU",
        
        # Product name columns
        "ชื่อสินค้า": "product_name",
        "สินค้า": "product_name",
        "Product Name": "product_name",
        "Name": "product_name",
        
        # Stock level columns
        "จำนวนคงเหลือ": "stock_level",
        "จำนวน": "stock_level",
        "Stock": "stock_level",
        "Quantity": "stock_level",
        
        # Category columns
        "หมวดหมู่": "category",
        "Category": "category",
        "ประเภท": "category"
    }
    
    errors = []
    
    def clean_and_map_columns(df):
        # Drop the index column if it exists
        if '#' in df.columns:
            df = df.drop('#', axis=1)
        if 'Unnamed: 0' in df.columns:
            df = df.drop('Unnamed: 0', axis=1)
            
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Map columns using our mapping dictionary
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
                
        # Convert stock_level to numeric
        if 'stock_level' in df.columns:
            df['stock_level'] = pd.to_numeric(df['stock_level'], errors='coerce').fillna(0).astype(int)
            
        return df
    
    # Try Excel format first
    for h in possible_headers:
        try:
            df = pd.read_excel(file_content, header=h)
            df = clean_and_map_columns(df)
            
            # Verify required columns exist
            if 'Product_SKU' in df.columns:
                print(f"✓ Found Excel with header row {h}")
                return df, h
                
            errors.append(f"Excel header={h}: No SKU column found")
        except Exception as e:
            errors.append(f"Excel header={h}: {str(e)}")
    
    # Try CSV with different encodings
    encodings = ['utf-8', 'utf-8-sig', 'cp874', 'tis-620']
    for encoding in encodings:
        for h in possible_headers:
            try:
                if isinstance(file_content, bytes):
                    content = file_content.decode(encoding)
                else:
                    content = file_content
                
                df = pd.read_csv(io.StringIO(content), header=h)
                df = clean_and_map_columns(df)
                
                if 'Product_SKU' in df.columns:
                    print(f"✓ Found CSV with encoding {encoding}, header row {h}")
                    return df, h
                    
                errors.append(f"CSV {encoding} header={h}: No SKU column found")
            except Exception as e:
                errors.append(f"CSV {encoding} header={h}: {str(e)}")
    
    error_msg = "❌ Could not load file as Excel or CSV. Tried:\n" + "\n".join(errors)
    raise ValueError(error_msg)

@app.post("/notifications/upload")
async def upload_stock_files(
    previous_stock: Optional[UploadFile] = File(None),
    current_stock: UploadFile = File(...)
):
    """Upload stock files and generate notifications"""
    try:
        print("[Backend] Processing stock upload...")
        
        if not SUPABASE_AVAILABLE:
            print("[Backend] ⚠️ Supabase not available")
            raise HTTPException(
                status_code=503,
                detail="Database not available. Please check Supabase configuration."
            )
        
        # Read current stock file with fallback headers
        current_content = await current_stock.read()
        try:
            df_curr, header_row = load_file_with_fallback(io.BytesIO(current_content))
            print(f"[Backend] Current stock loaded (header={header_row}): {len(df_curr)} rows")
            
            # Validate required columns exist
            required_columns = ['Product_SKU', 'product_name', 'stock_level', 'category']
            missing_columns = [col for col in required_columns if col not in df_curr.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in current stock file: {', '.join(missing_columns)}")
                
            # Remove any unnecessary columns
            keep_columns = ['Product_SKU', 'product_name', 'stock_level', 'category', 'created_at', 'updated_at', 'week_date', 'uploaded_at', 'flag', 'unchanged_counter']
            all_columns = df_curr.columns.tolist()
            drop_columns = [col for col in all_columns if col not in keep_columns and col != '#']
            if drop_columns:
                print(f"[Backend] Removing unnecessary columns: {', '.join(drop_columns)}")
                df_curr = df_curr.drop(drop_columns, axis=1, errors='ignore')
                
        except Exception as e:
            print(f"[Backend] Failed to load current stock file: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # Check if base_stock exists
        base_stock_exists = False
        df_prev = None
        
        try:
            df_prev = execute_query("SELECT * FROM base_stock")
            if not df_prev.empty:
                base_stock_exists = True
                print(f"[Backend] Loaded previous stock from database: {len(df_prev)} rows")
        except Exception as e:
            print(f"[Backend] base_stock table doesn't exist or error during read: {str(e)}")
        
        # If base_stock doesn't exist, require previous stock file
        if not base_stock_exists:
            if not previous_stock:
                raise HTTPException(
                    status_code=400,
                    detail="Previous stock file is required for first upload"
                )
            prev_content = await previous_stock.read()
            try:
                df_prev, header_row = load_file_with_fallback(io.BytesIO(prev_content))
                print(f"[Backend] Previous stock loaded (header={header_row}): {len(df_prev)} rows")
            except Exception as e:
                print(f"[Backend] Failed to load previous stock file: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
        
        # Rename columns in current stock data
        df_curr = df_curr.rename(columns={
            'ชื่อสินค้า': 'product_name',
            'รหัสสินค้า': 'product_sku',
            'จำนวนคงเหลือ': 'stock_level',
            'จำนวน': 'stock_level',
            'หมวดหมู่': 'category',
            "หมวดหมู่ย่อย" : 'category'
        })
        
        # Rename columns in previous stock data
        if df_prev is not None:
            df_prev = df_prev.rename(columns={
                'ชื่อสินค้า': 'product_name',
                'รหัสสินค้า': 'product_sku',
                'จำนวนคงเหลือ': 'stock_level',
                'จำนวน': 'stock_level',
                'หมวดหมู่': 'category',
                "หมวดหมู่ย่อย" : 'category' 
            })
        df_curr["stock_level"] = pd.to_numeric(df_curr["stock_level"], errors='coerce').fillna(0).astype(int)
        df_prev["stock_level"] = pd.to_numeric(df_prev["stock_level"], errors='coerce').fillna(0).astype(int)
        # Normalize column names (handle upper/lowercase automatically)
        df_curr.columns = df_curr.columns.str.strip().str.lower()
        df_prev.columns = df_prev.columns.str.strip().str.lower()
        print("[Debug] df_curr columns:", df_curr.columns.tolist())
        df_curr = df_curr.dropna(subset=['product_sku','category'])
        df_prev = df_prev.dropna(subset=['product_sku','category'])
        try:
            # Save current stock data to Supabase
            print("[Backend] Saving current stock data to Supabase...")
            
            # Ensure required columns exist and have correct names
            required_columns = {
                'product_sku': 'product_sku',
                'product_name': 'product_name',
                'stock_level': 'stock_level',
                'category': 'category'
            }
            
            # Validate required columns
            missing_columns = [col for col in required_columns.keys() if col not in df_curr.columns]
            if missing_columns:
                print(f"[Backend] Columns found in df_curr: {df_curr.columns.tolist()}")
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
                
            # Rename columns to match database schema
            df_curr = df_curr.rename(columns=required_columns)
            
            # Convert stock_level to integer
            df_curr['stock_level'] = pd.to_numeric(df_curr['stock_level'], errors='coerce').fillna(0).astype(int)
            
            # Keep only the columns we need
            keep_columns = ['product_sku', 'product_name', 'stock_level', 'category']
            df_curr = df_curr[keep_columns]
            
            # Add metadata columns that exist in the schema
            now = pd.Timestamp.now()
            df_curr['created_at'] = now
            df_curr['updated_at'] = now
            df_curr['unchanged_counter'] = 0
            df_curr['flag'] = 'stage'
            
            print(f"[Backend] Columns being saved: {df_curr.columns.tolist()}")
            df_curr_dict = df_curr.to_dict(orient='records')
            # Clear and insert into base_stock (raw current stock)
            delete_data('base_stock', 'product_sku', '*')  # '*' means all
            res_base = insert_data('base_stock', df_curr_dict)
            if res_base is None:
                print("[Backend] ❌ insert_data returned None for base_stock")
                raise HTTPException(status_code=500, detail="Failed to insert base_stock records")
            print(f"[Backend] ✓ Saved {len(df_curr_dict)} records to base_stock (raw upload)")

            # Generate stock report (notifications)
            print("[Backend] Generating stock report...")

            # Normalize column names to expected keys so generate_stock_report doesn't KeyError
            def ensure_sku_column(df):
                # make a copy to avoid modifying original
                df = df.copy()
                cols = {str(c): c for c in df.columns}
                # find SKU-like column (case-insensitive)
                sku_col = None
                for c in cols:
                    if 'sku' in c.lower():
                        sku_col = cols[c]
                        break
                if sku_col is not None and str(sku_col) != 'product_sku':
                    df = df.rename(columns={sku_col: 'product_sku'})
                # product name
                name_col = None
                for c in cols:
                    if 'product' in c.lower() and 'name' in c.lower():
                        name_col = cols[c]
                        break
                if name_col is not None and str(name_col) != 'product_name':
                    df = df.rename(columns={name_col: 'product_name'})
                # stock level
                stock_col = None
                for c in cols:
                    if 'stock' in c.lower() or c.lower() == 'จำนวน' or 'quantity' in c.lower():
                        stock_col = cols[c]
                        break
                if stock_col is not None and str(stock_col) != 'stock_level':
                    df = df.rename(columns={stock_col: 'stock_level'})
                # category
                cat_col = None
                for c in cols:
                    if 'หมวด' in c or 'category' in c.lower():
                        cat_col = cols[c]
                        break
                if cat_col is not None and str(cat_col) != 'category':
                    df = df.rename(columns={cat_col: 'category'})
                return df

            # Log columns for debugging
            try:
                prev_cols = list(df_prev.columns) if (df_prev is not None and hasattr(df_prev, 'columns')) else None
            except Exception:
                prev_cols = None
            try:
                curr_cols = list(df_curr.columns) if (df_curr is not None and hasattr(df_curr, 'columns')) else None
            except Exception:
                curr_cols = None
            print(f"[Backend] df_prev columns: {prev_cols}")
            print(f"[Backend] df_curr columns: {curr_cols}")

            try:
                df_prev = ensure_sku_column(df_prev) if df_prev is not None else df_prev
                df_curr = ensure_sku_column(df_curr)
            except Exception as e:
                print(f"[Backend] Warning: failed to normalize columns: {e}")

            # Show a small sample for debugging
            try:
                print("[Backend] df_curr sample:")
                print(df_curr.head(3).to_dict(orient='records'))
            except Exception:
                pass

            try:
                print("[Backend] df_prev sample:")
                if df_prev is not None:
                    print(df_prev.head(3).to_dict(orient='records'))
            except Exception:
                pass

            report_df = generate_stock_report(df_prev, df_curr)
            print(f"[Backend] Report generated: {len(report_df)} items")

            # Convert report columns to lowercase to match database
            column_mapping = {
                'Product_SKU': 'product_sku',
                'Stock': 'stock_level',
                'Last_Stock': 'last_stock',
                'Status': 'status',
                'Description': 'description',
                'Min_Stock': 'min_stock',
                'Buffer': 'reorder_qty',
                'WeeksToEmpty': 'weeks_to_empty',
                'DecreaseRate': 'decrease_rate'
            }

            # Rename columns to match the database schema
            report_df = report_df.rename(columns=column_mapping)

            # Save report to stock_notifications
            report_df['unchanged_counter'] = 0
            report_df['flag'] = 'stage'
            report_df['created_at'] = now
            report_df['updated_at'] = now
            report_dict = report_df.to_dict(orient='records')
            delete_data('stock_notifications', 'product_sku', '*')

            # Log sample record before insertion
            if report_dict:
                print("[Backend] Sample record before insertion:")
                for k, v in report_dict[0].items():
                    print(f"  {k}: {type(v)} = {v}")

            res_notif = insert_data('stock_notifications', report_dict)
            if res_notif is None:
                print("[Backend] ❌ insert_data returned None for stock_notifications")
                raise HTTPException(status_code=500, detail="Failed to insert stock_notifications records")
            print(f"[Backend] ✓ Saved {len(report_dict)} notifications to stock_notifications")

            # Note: base_stock will be updated later after flags/counters are calculated

        except Exception as e:
            print(f"[Backend] ❌ Failed to save to Supabase: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save data to Supabase: {str(e)}"
            )
        
        # Calculate flags based on stock changes
        print("[Backend] Calculating stock flags...")
        for idx, row in report_df.iterrows():
            product_sku = row.get('product_sku', '')  # Using lowercase column names
            current_stock_level = row.get('stock_level', 0)
            last_stock_level = row.get('last_stock', 0)
            
            # Get previous counter and flag from base_stock if exists
            prev_counter = 0
            prev_flag = 'stage'
            
            if base_stock_exists and not df_prev.empty:
                prev_row = df_prev[df_prev['product_sku'] == product_sku]
                if not prev_row.empty:
                    prev_counter = prev_row.iloc[0].get('unchanged_counter', 0)
                    prev_flag = prev_row.iloc[0].get('flag', 'stage')
            
            # Apply flag logic
            if current_stock_level == last_stock_level:
                new_counter = prev_counter + 1
                new_flag = 'inactive' if new_counter >= 4 else prev_flag
            elif current_stock_level < last_stock_level:
                new_counter = 0
                new_flag = 'active'
            else:  # current_stock_level > last_stock_level
                new_counter = 0
                new_flag = 'just added stock'
            
            report_df.at[idx, 'unchanged_counter'] = new_counter
            report_df.at[idx, 'flag'] = new_flag
        
        # Save report to stock_notifications table
        print("[Backend] Saving to stock_notifications table...")
        report_df['created_at'] = datetime.now()
    # Save to Supabase (already done above)
        
        print("[Backend] Updating base_stock table...")
        
        flag_map = dict(zip(report_df['product_sku'], report_df['flag']))
        counter_map = dict(zip(report_df['product_sku'], report_df['unchanged_counter']))
        
        # Build base_stock_df with proper alignment
        base_stock_data = []
        for idx, row in df_curr.iterrows():
            product_sku = row.get('product_sku', '')
            base_stock_data.append({
                'product_name': row.get('product_name', ''),
                'product_sku': product_sku,
                'stock_level': row.get('stock_level', 0),
                'category': row.get('category', ''),  # Changed from 'หมวดหมู่' to match schema
                'unchanged_counter': counter_map.get(product_sku, 0),
                'flag': flag_map.get(product_sku, 'stage'),
                'updated_at': datetime.now()
            })
        
        base_stock_df = pd.DataFrame(base_stock_data)
        
        # Clear and insert new data into base_stock
        delete_data('base_stock', 'product_sku', '*')
        insert_data('base_stock', base_stock_df.to_dict(orient='records'))
        
        print("[Backend] ✅ Upload completed successfully")
        return {
            "success": True,
            "message": "Stock files processed successfully",
            "notifications_count": len(report_df)
        }
        
    except Exception as e:
        print(f"[Backend] ❌ Error in upload: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/notifications/clear_base_stock")
async def clear_base_stock():
    """Clear both base_stock and stock_notifications tables"""
    try:
        print("[Backend] Clearing base_stock and stock_notifications tables...")
        
        # Clear both tables using Supabase
        delete_data('base_stock', 'product_sku', '*')
        delete_data('stock_notifications', 'product_sku', '*')
        
        print("[Backend] ✅ base_stock and stock_notifications cleared")
        return {"success": True, "message": "Stock data cleared successfully"}
        
    except Exception as e:
        print(f"[Backend] ❌ Error clearing stock data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear_stock")
async def clear_stock_compat():
    """Compatibility endpoint for frontend: clears base_stock and stock_notifications"""
    try:
        print("[Backend] Compatibility: clearing base_stock and stock_notifications via /clear_stock")
        delete_data('base_stock', 'product_sku', '*')
        delete_data('stock_notifications', 'product_sku', '*')
        print("[Backend] ✅ /clear_stock completed")
        return {"success": True, "message": "Stock data cleared successfully"}
    except Exception as e:
        print(f"[Backend] ❌ Error in /clear_stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notifications/update_manual_values")
async def update_manual_values_endpoint(
    product_sku: str = Query(..., description="Product SKU"),
    minstock: Optional[int] = Query(None, description="Manual MinStock value"),
    buffer: Optional[int] = Query(None, description="Buffer value (for calculation only, not stored)")
):
    """Update manual MinStock value and recalculate that product
    Note: Buffer is used for calculation but not stored in the database"""
    try:
        print(f"[Backend] Updating manual values for {product_sku}: MinStock={minstock}, Buffer={buffer}")
        
        df_notification = execute_query(f"SELECT * FROM stock_notifications WHERE product_sku = '{product_sku}'")
        
        if df_notification.empty:
            raise HTTPException(status_code=404, detail=f"Product {product_sku} not found in notifications")
        
        row = df_notification.iloc[0]

        # Robustly read numeric columns
        def _get_col_value(series, df_cols, candidates, default=0):
            norm_map = {str(c).strip().lower(): c for c in df_cols}
            for cand in candidates:
                key = norm_map.get(str(cand).strip().lower())
                if key is not None:
                    val = series.get(key, None)
                    try:
                        if pd.notna(val):
                            return val
                    except Exception:
                        return val
            return default

        stock = _get_col_value(row, df_notification.columns, ['stock', 'stock_level', 'Stock', 'Stock_Level'])
        last_stock = _get_col_value(row, df_notification.columns, ['last_stock', 'Last_Stock', 'LastStock'])

        try:
            stock = int(stock)
        except Exception:
            stock = 0
        try:
            last_stock = int(last_stock)
        except Exception:
            last_stock = 0

        weekly_sale = max((last_stock - stock), 1)
        decrease_rate = ((last_stock - stock) / last_stock * 100) if last_stock > 0 else 0
        weeks_to_empty = stock / weekly_sale if weekly_sale > 0 else 0
        
        stored_minstock = minstock if minstock is not None else 0
        
        # Calculate buffer dynamically based on decrease_rate (same logic as generate_stock_report)
        if decrease_rate > 50:
            calculated_buffer = 20
        elif decrease_rate > 20:
            calculated_buffer = 10
        else:
            calculated_buffer = 5
        calculated_buffer = min(calculated_buffer, 50)  # MAX_BUFFER = 50
        
        # If user provided a buffer value, use it for this calculation
        buffer_to_use = buffer if buffer is not None else calculated_buffer
        
        print("[Backend] Calculation values:")
        print(f"  Stock: {stock}")
        print(f"  Last Stock: {last_stock}")
        print(f"  Weekly Sale: {weekly_sale}")
        print(f"  Decrease Rate: {decrease_rate}%")
        print(f"  MinStock: {stored_minstock}")
        print(f"  Buffer (calculated): {calculated_buffer}")
        print(f"  Buffer (to use): {buffer_to_use}")
        
        # Calculate new reorder quantity
        default_reorder = int(weekly_sale * 1.5)
        new_reorder_qty = max(stored_minstock + buffer_to_use - stock, default_reorder)
        
        # Determine status
        is_red = (stock < stored_minstock) or (decrease_rate > 50)
        is_yellow = (not is_red) and (decrease_rate > 20)
        
        if is_red:
            new_status = 'Red'
            new_description = f'Decreasing rapidly and nearly out of stock! Recommend restocking {new_reorder_qty} units'
        elif is_yellow:
            new_status = 'Yellow'
            new_description = f'Decreasing rapidly, should prepare to restock. Recommend restocking {new_reorder_qty} units'
        else:
            new_status = 'Green'
            new_description = 'Stock is sufficient'
        
        # Find actual column names
        cols = [str(c) for c in df_notification.columns]
        norm_map = {c.strip().lower(): c for c in cols}
        match_col = norm_map.get('product_sku', 'product_sku')

        def find_col(*candidates):
            for cand in candidates:
                key = str(cand).strip().lower()
                if key in norm_map:
                    return norm_map[key]
            return None

        update_payload = {}
        min_col = find_col('minstock', 'min_stock', 'min stock', 'MinStock')
        if min_col and minstock is not None:
            update_payload[min_col] = int(stored_minstock)
        
        # Always update reorder_qty, status, and description
        update_payload['reorder_qty'] = int(new_reorder_qty)
        update_payload['status'] = new_status
        update_payload['description'] = new_description
        update_payload['updated_at'] = datetime.now().isoformat()

        print(f"[Backend] Updating {product_sku} with: {update_payload}")
        result = update_data('stock_notifications', update_payload, match_col, product_sku)
        print(f"[Backend] Update result: {result}")
        
        # Get the final updated record
        final_df = execute_query(f"SELECT * FROM stock_notifications WHERE {match_col} = '{product_sku}'")
        final_row = None
        if final_df is not None and not final_df.empty:
            final_row = final_df.iloc[0].to_dict()
            for k, v in list(final_row.items()):
                if pd.notna(v) and isinstance(v, (pd.Timestamp, datetime)):
                    final_row[k] = str(v)

        print(f"[Backend] ✅ Updated manual values for {product_sku}")
        response_data = {
            "success": True,
            "message": "Manual values updated successfully",
            "product_sku": product_sku,
            "minstock": stored_minstock,
            "buffer": buffer_to_use,
            "calculated_buffer": calculated_buffer,
            "reorder_qty": new_reorder_qty,
            "status": new_status,
            "updated_row": {
                "product_sku": product_sku,
                "min_stock": stored_minstock,
                "buffer": buffer_to_use,
                "reorder_qty": new_reorder_qty,
                "status": new_status,
                "description": new_description
            }
        }
        if final_row is not None:
            response_data["updated_row"].update(final_row)
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Backend] ❌ Error updating manual values: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# STOCK ENDPOINTS
# ============================================================================

@app.get("/stock/levels")
async def get_stock_levels(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None)
):
    """Get stock levels from base_stock table"""
    try:
        print("[Backend] Fetching stock levels from base_stock...")
        df = execute_query("SELECT * FROM base_stock")
        if category:
            df = df[df['หมวดหมู่'] == category]
        if status:
            df = df[df['flag'] == status]
        if sort_by == "quantity_asc":
            df = df.sort_values(by="stock_level", ascending=True)
        elif sort_by == "quantity_desc":
            df = df.sort_values(by="stock_level", ascending=False)
        else:
            df = df.sort_values(by="product_name", ascending=True)
        if not df.empty:
            for idx, row in df.iterrows():
                if 'updated_at' in df.columns and pd.notna(row['updated_at']):
                    df.at[idx, 'updated_at'] = str(row['updated_at'])
            return {"success": True, "data": df.to_dict('records')}
        else:
            return {"success": True, "data": []}
    except Exception as e:
        print(f"[Backend] ❌ Error fetching stock levels: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "data": [], "error": str(e)}

@app.get("/stock/categories")
async def get_stock_categories():
    """Get unique stock categories from base_stock"""
    try:
        print("[Backend] Fetching stock categories...")
        
        try:
            df = execute_query("SELECT DISTINCT \"หมวดหมู่\" as category FROM base_stock")
            df = df[df['category'].notnull()]
            if not df.empty:
                categories = df['category'].tolist()
                print(f"[Backend] ✅ Found {len(categories)} categories")
                return {"success": True, "data": categories}
            else:
                return {"success": True, "data": []}
        except Exception as db_error:
            print(f"[Backend] Error fetching categories: {str(db_error)}")
            return {"success": True, "data": []}
    except Exception as e:
        print(f"[Backend] ❌ Error in get_stock_categories: {str(e)}")
        return {"success": False, "data": []}

# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@app.get("/analysis/dashboard")
async def get_dashboard_analytics():
    """Get dashboard analytics data"""
    try:
        print("[Backend] Fetching dashboard analytics...")
        
        # Note: This endpoint uses 'engine' which is deprecated. It should be migrated to use Supabase client.
        # For now, it will likely fail if engine is None.
        if not engine: 
            print("[Backend] ⚠️ Deprecated 'engine' not available. Dashboard analytics will not work.")
            return {
                "success": False,
                "data": {
                    "total_stock_items": 0,
                    "low_stock_alerts": 0,
                    "sales_this_month": 0,
                    "out_of_stock": 0
                },
                "error": "'engine' not initialized. Migration to Supabase client required."
            }
        
        # Get metrics from base_data and base_stock
        current_date = datetime.now()
        current_month = current_date.month
        current_year = current_date.year
        
        # Total stock items
        total_query = "SELECT COUNT(*) as count FROM base_stock"
        total_result = pd.read_sql(total_query, engine)
        total_items = int(total_result.iloc[0]['count']) if not total_result.empty else 0
        
        # Low stock (using flag)
        low_stock_query = "SELECT COUNT(*) as count FROM base_stock WHERE flag = 'active'"
        low_stock_result = pd.read_sql(low_stock_query, engine)
        low_stock = int(low_stock_result.iloc[0]['count']) if not low_stock_result.empty else 0
        
        # Out of stock
        out_stock_query = "SELECT COUNT(*) as count FROM base_stock WHERE stock_level = 0"
        out_stock_result = pd.read_sql(out_stock_query, engine)
        out_of_stock = int(out_stock_result.iloc[0]['count']) if not out_stock_result.empty else 0
        
        # Sales this month
        try:
            sales_query = f"""
                SELECT COALESCE(SUM(total_amount_baht), 0) as monthly_sales
                FROM base_data
                WHERE EXTRACT(MONTH FROM sales_date) = {current_month}
                AND EXTRACT(YEAR FROM sales_date) = {current_year}
            """
            sales_result = pd.read_sql(sales_query, engine)
            monthly_sales = float(sales_result.iloc[0]['monthly_sales']) if not sales_result.empty else 0
        except:
            monthly_sales = 0
        
        return {
            "success": True,
            "data": {
                "total_stock_items": total_items,
                "low_stock_alerts": low_stock,
                "sales_this_month": monthly_sales,
                "out_of_stock": out_of_stock
            }
        }
        
    except Exception as e:
        print(f"[Backend] ❌ Error in dashboard analytics: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "data": {
                "total_stock_items": 0,
                "low_stock_alerts": 0,
                "sales_this_month": 0,
                "out_of_stock": 0
            },
            "error": str(e)
        }

@app.get("/analysis/base_skus")
async def get_analysis_base_skus(search: str = Query("", description="Search term for base SKUs or categories")):
    """Get unique base SKUs from base_stock for analysis, searchable by SKU or category"""
    print(f"[Backend] Fetching base SKUs with search: '{search}'")
    # Not implemented: SQLAlchemy removed, needs Supabase migration
    return {"success": False, "message": "Not implemented: endpoint needs Supabase migration", "base_skus": [], "results": [], "total": 0}

@app.get("/analysis/historical")
async def get_analysis_historical_sales(sku: str = Query(..., description="Product SKU or category to analyze")):
    """Get historical stock data from base_stock table"""
    print(f"[Backend] Fetching historical stock data for: {sku}")
    # Not implemented: SQLAlchemy removed, needs Supabase migration
    return {"success": False, "message": "Not implemented: endpoint needs Supabase migration", "chart_data": [], "table_data": [], "search_type": "unknown"}

@app.post("/analysis/performance")
async def get_analysis_performance(request: dict):
    """Get performance comparison data from base_data table"""
    try:
        sku_list = request.get('sku_list', [])
        print(f"[Backend] Fetching performance comparison for SKUs: {sku_list}")
        
        # Note: This endpoint uses 'engine' which is deprecated. It should be migrated to use Supabase client.
        # For now, it will likely fail if engine is None.
        if not engine:
            return {"success": False, "message": "Database not available. 'engine' not initialized.", "chart_data": {}, "table_data": []}
        
        if not sku_list or len(sku_list) == 0:
            return {"success": False, "message": "No SKUs provided", "chart_data": {}, "table_data": []}
        
        # Disabled: SQLAlchemy text() not available. Needs Supabase migration.
        return {"success": False, "message": "Not implemented: endpoint needs Supabase migration", "chart_data": {}, "table_data": []}
    except Exception as e:
        print(f"[Backend] ❌ Error fetching performance comparison: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "chart_data": {},
            "table_data": []
        }

@app.get("/analysis/best_sellers")
async def get_analysis_best_sellers(
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month"),
    limit: int = Query(10, description="Number of top sellers")
):
    """Get best selling products from base_data table"""
    try:
        print(f"[Backend] Fetching best sellers for {year}-{month:02d} (limit {limit})...")
        
        # Note: This endpoint uses 'engine' which is deprecated. It should be migrated to use Supabase client.
        # For now, it will likely fail if engine is None.
        if not engine:
            return {"success": False, "message": "Database not available. 'engine' not initialized.", "data": []}
        
        # Disabled: SQLAlchemy text() not available. Needs Supabase migration.
        return {"success": False, "message": "Not implemented: endpoint needs Supabase migration", "data": []}
    except Exception as e:
        print(f"[Backend] Error in best_sellers endpoint: {str(e)}")
        return {"success": False, "message": f"Server error: {str(e)}", "data": []}

@app.get("/analysis/performance-products")
async def get_performance_products(search: str = Query("", description="Search term for products")):
    """Get products grouped by category from base_stock table"""
    try:
        print(f"[Backend] Fetching performance products from base_stock with search: '{search}'")
        
        # Note: This endpoint uses 'engine' which is deprecated. It should be migrated to use Supabase client.
        # For now, it will likely fail if engine is None.
        if not engine:
            return {"success": False, "categories": {}, "all_products": [], "message": "Database not available. 'engine' not initialized."}
        
        # Disabled: SQLAlchemy text() not available. Needs Supabase migration.
        return {"success": False, "categories": {}, "all_products": [], "message": "Not implemented: endpoint needs Supabase migration"}
    except Exception as e:
        print(f"[Backend] ❌ Error fetching performance products: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "categories": {}, "all_products": []}

@app.get("/analysis/total_income")
async def get_total_income(product_sku: str = "", category: str = ""):
    """Get total income analysis from base_data table with optional filters"""
    try:
        # Note: This endpoint uses 'engine' which is deprecated. It should be migrated to use Supabase client.
        # For now, it will likely fail if engine is None.
        if not engine:
            return {"success": False, "message": "Database not available. 'engine' not initialized."}
        
        print(f"[Backend] Fetching total income data (product_sku={product_sku}, category={category})...")
        
        # Disabled: SQLAlchemy text() not available. Needs Supabase migration.
        return {"success": False, "chart_data": [], "table_data": [], "grand_total": 0, "message": "Not implemented: endpoint needs Supabase migration"}
    except Exception as e:
        print(f"[Backend] ❌ Error fetching total income: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "chart_data": [],
            "table_data": [],
            "grand_total": 0
        }

@app.get("/analysis/search-suggestions")
async def get_search_suggestions(search: str = Query("", description="Search term for SKUs or categories")):
    """Get search suggestions for both SKUs and categories"""
    try:
        print(f"[Backend] Fetching search suggestions for: '{search}'")
        
        # Note: This endpoint uses 'engine' which is deprecated. It should be migrated to use Supabase client.
        # For now, it will likely fail if engine is None.
        if not engine:
            return {"success": False, "suggestions": [], "message": "Database not available. 'engine' not initialized."}
        
        if not search or len(search) < 1:
            return {"success": True, "suggestions": []}
        
        # Disabled: SQLAlchemy text() not available. Needs Supabase migration.
        return {"success": False, "suggestions": [], "message": "Not implemented: endpoint needs Supabase migration"}
    except Exception as e:
        print(f"[Backend] ❌ Error fetching search suggestions: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "suggestions": []}

# ============================================================================
# TRAIN AND PREDICT ENDPOINTS
# ============================================================================

@app.post("/train")
async def train_model(
    product_file: UploadFile = File(...),
    sales_file: UploadFile = File(...)
):
    """Train the forecasting model with product and sales data"""
    try:
        print("[Backend] Starting model training...")
        # Read uploaded files
        product_content = await product_file.read()
        sales_content = await sales_file.read()
        print(f"[Backend] Product file: {product_file.filename}")
        print(f"[Backend] Sales file: {sales_file.filename}")
        import tempfile
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.xlsx') as product_temp:
            product_temp.write(product_content)
            product_temp_path = product_temp.name
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.xlsx') as sales_temp:
            sales_temp.write(sales_content)
            sales_temp_path = sales_temp.name
        try:
            print(f"[Backend] Calling auto_cleaning with sales_path={sales_temp_path}, product_path={product_temp_path}")
            df_cleaned = auto_cleaning(sales_temp_path, product_temp_path)
            rows_uploaded = len(df_cleaned)
            print(f"[Backend] Cleaned data: {rows_uploaded} rows")
            # Insert cleaned data into Supabase
            import pandas as pd
            records = df_cleaned.to_dict(orient='records')
            print(f"[Backend] Preparing to insert {len(records)} records into base_data")
            print(f"[Backend] Columns in cleaned data: {df_cleaned.columns.tolist()}")
            # Handle datetime columns and NaN values
            for record in records:
                for key, value in list(record.items()):  # Use list() to avoid modifying during iteration
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, pd.Timestamp):
                        record[key] = value.isoformat()
                    elif isinstance(value, float) and pd.isna(value):
                        record[key] = None
            print("[Backend] Data cleaned and ready for insertion")
            result = insert_data('base_data', records)
            if result is None:
                print("[Backend] ⚠️ Failed to insert data into base_data")
                raise HTTPException(status_code=500, detail="Failed to insert data into Supabase")
            response = {
                "success": True,
                "data_cleaning": {
                    "status": "completed",
                    "rows_uploaded": rows_uploaded,
                    "message": f"Successfully cleaned and uploaded {rows_uploaded} rows"
                },
                "ml_training": {
                    "status": "pending",
                    "message": "Training not started"
                }
            }
            # Train the model (if you want to keep this logic, adapt to use Supabase for all DB access)
            try:
                df_window_raw, df_window, base_model, X_train, y_train, X_test, y_test, product_sku_last = update_model_and_train(df_cleaned)
                print("[Backend] ✅ Model training completed successfully")
                response["ml_training"] = {
                    "status": "completed",
                    "message": "Model trained successfully"
                }
                # Forecast generation and saving to Supabase
                try:
                    print("[Backend] Generating forecasts...")
                    long_forecast, forecast_results = forcast_loop(X_train, y_train, df_window_raw, product_sku_last, base_model)
                    if forecast_results and len(forecast_results) > 0:
                        import pandas as pd
                        from datetime import datetime
                        from DB_server import insert_data, delete_data
                        
                        # Convert forecast results to DataFrame
                        print("[Backend] Processing forecast results...")
                        forecast_df = pd.DataFrame(forecast_results)
                        print(f"[Backend] Forecast columns: {forecast_df.columns.tolist()}")
                        
                        # Add timestamp
                        now = datetime.now()
                        forecast_df['created_at'] = now
                        
                        # Clean up data for Supabase
                        records = forecast_df.to_dict(orient='records')
                        print(f"[Backend] Cleaning {len(records)} forecast records...")
                        for record in records:
                            for key, value in list(record.items()):
                                if pd.isna(value):
                                    record[key] = None
                                elif isinstance(value, pd.Timestamp):
                                    record[key] = value.isoformat()
                                elif isinstance(value, datetime):
                                    record[key] = value.isoformat()
                        
                        # Clear old forecasts and insert new ones
                        print("[Backend] Clearing old forecasts...")
                        delete_data('forecast_output', 'product_sku', '*')
                        
                        print("[Backend] Inserting new forecasts...")
                        result = insert_data('forecast_output', records)
                        if result is not None:
                            print(f"[Backend] ✅ Successfully saved {len(records)} forecasts to forecast_output")
                            response["ml_training"]["forecast_rows"] = len(records)
                            response["ml_training"]["message"] = f"Model trained and {len(records)} forecasts generated and saved to forecast_output"
                        else:
                            print("[Backend] ⚠️ Failed to save forecasts to forecast_output")
                            response["ml_training"]["message"] = "Model trained but failed to save forecasts"
                    else:
                        response["ml_training"]["message"] = "Model trained but no forecasts generated"
                except Exception as forecast_error:
                    print(f"[Backend] ⚠️ Forecast generation or saving failed: {str(forecast_error)}")
                    import traceback
                    traceback.print_exc()
                    response["ml_training"]["message"] = f"Model trained but forecast generation/saving failed: {str(forecast_error)}"
            except Exception as train_error:
                print(f"[Backend] ❌ Model training failed: {str(train_error)}")
                import traceback
                traceback.print_exc()
                response["ml_training"] = {
                    "status": "failed",
                    "message": f"Training failed: {str(train_error)}"
                }
            return response
        finally:
            # Clean up temporary files
            import os
            try:
                os.unlink(product_temp_path)
                os.unlink(sales_temp_path)
            except:
                pass
    except Exception as e:
        print(f"[Backend] ❌ Error in train_model: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict/existing")
async def get_existing_forecasts():
    """Get existing forecast data from the forecasts table"""
    try:
        print("[Backend] Fetching existing forecasts...")
        
        try:
            print("[Backend] Querying Supabase...")
            df = execute_query("""
                SELECT 
                    product_sku,
                    forecast_date,
                    predicted_sales,
                    current_sales,
                    current_date_col,
                    created_at
                FROM forecasts
                ORDER BY product_sku ASC, forecast_date ASC
            """)
            
            if df is not None and not df.empty:
                print(f"[Backend] ✅ Retrieved {len(df)} forecasts")
                # Convert timestamps to strings
                for idx, row in df.iterrows():
                    for col in ['forecast_date', 'current_date_col', 'created_at']:
                        if col in df.columns and pd.notna(row[col]):
                            df.at[idx, col] = str(row[col])
                
                return {"success": True, "forecast": df.to_dict('records')}
            else:
                print("[Backend] No forecasts found")
                return {"success": True, "forecast": []}
                
        except Exception as db_error:
            print(f"[Backend] Error querying forecasts: {str(db_error)}")
            import traceback
            traceback.print_exc()
            return {"success": True, "forecast": []}
        
    except Exception as e:
        print(f"[Backend] ❌ Error fetching forecasts: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "forecast": [], "error": str(e)}

@app.post("/predict")
async def predict_sales(n_forecast: int = Query(3, description="Number of months to forecast")):
    """Generate sales forecasts for n months"""
    print(f"\n{'='*80}", flush=True)
    print(f"🎯 PREDICT ENDPOINT CALLED - n_forecast={n_forecast}", flush=True)
    print(f"{'='*80}\n", flush=True)
    sys.stdout.flush()
    
    try:
        print(f"[Backend] Generating {n_forecast} month forecast...")
        
        if not SUPABASE_AVAILABLE:
            print("[Backend] ⚠️ Supabase not available")
            raise HTTPException(
                status_code=503,
                detail="Database not available. Please check Supabase configuration."
            )
        
        # Check if model is trained (base_data exists)
        try:
            print("[Backend] Checking base_data table...")
            df = execute_query("SELECT * FROM base_data LIMIT 1")
            if df is None or len(df) == 0:
                print("[Backend] No training data found in base_data")
                raise HTTPException(
                    status_code=400,
                    detail="No training data available. Please train the model first by uploading product and sales data."
                )
            print(f"[Backend] Found training data: {len(df)} rows")
        except HTTPException:
            raise
        except Exception as e:
            print(f"[Backend] Error checking base_data: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=400,
                detail=f"Failed to check training data: {str(e)}"
            )
        
        print("[Backend] Loading trained model and data...")
        
        if not os.path.exists("xgb_sales_model.pkl"):
            print("[Backend] Model file not found")
            raise HTTPException(
                status_code=400,
                detail="Model file not found. Please train the model first by uploading product and sales data."
            )

        # Load model
        base_model = joblib.load("xgb_sales_model.pkl")
        
        # Get the latest training data from base_data
        print("[Backend] Fetching training data from Supabase...")
        df_cleaned = execute_query("SELECT * FROM base_data ORDER BY sales_date DESC")
        if df_cleaned is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve training data from Supabase"
            )
        
        # Convert date columns to datetime
        print("[Backend] Converting date columns...")
        try:
            df_cleaned['sales_date'] = pd.to_datetime(df_cleaned['sales_date'])
            if 'week_date' in df_cleaned.columns:
                df_cleaned['week_date'] = pd.to_datetime(df_cleaned['week_date'])
        except Exception as e:
            print(f"[Backend] Error converting dates: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process dates in training data: {str(e)}"
            )
        
        # Recreate the training data
        print("[Backend] Preparing training data...")
        df_window_raw, df_window, _, X_train, y_train, X_test, y_test, product_sku_last = update_model_and_train(df_cleaned)
        
        # Run forecast loop with n_forecast parameter
        print(f"[Backend] Running forecast loop for {n_forecast} months...")
        long_forecast, forecast_results = forcast_loop(X_train, y_train, df_window_raw, product_sku_last, base_model, n_forecast=n_forecast)
        
        if not forecast_results or len(forecast_results) == 0:
            print("[Backend] No forecast results generated")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate forecasts"
            )
        
        # Save forecasts to database
        print("[Backend] Saving forecasts to Supabase...")
        forecast_df = pd.DataFrame(forecast_results)
        forecast_df['created_at'] = datetime.now()
        
        # Clean up data for Supabase
        records = forecast_df.to_dict(orient='records')
        for record in records:
            for key, value in list(record.items()):
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, pd.Timestamp):
                    record[key] = value.isoformat()
                elif isinstance(value, datetime):
                    record[key] = value.isoformat()
        
        # Clear old forecasts and insert new ones
        delete_data('forecasts', 'product_sku', '*')
        result = insert_data('forecasts', records)
        if result is None:
            print("[Backend] Failed to save forecasts to Supabase")
            raise HTTPException(
                status_code=500,
                detail="Failed to save forecasts to database"
            )
        
        print(f"[Backend] ✅ Generated and saved {len(forecast_results)} forecasts for {n_forecast} months")
        
        # Convert dates to strings for JSON serialization
        for item in forecast_results:
            if 'forecast_date' in item:
                item['forecast_date'] = str(item['forecast_date'])
            if 'current_date_col' in item:
                item['current_date_col'] = str(item['current_date_col'])
        
        return {
            "status": "success",
            "forecast_rows": len(forecast_results),
            "n_forecast": n_forecast,
            "forecast": forecast_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Backend] ❌ Error generating forecasts: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/predict/clear")
async def clear_forecasts():
    """Clear all forecast data"""
    try:
        print("[Backend] Clearing forecasts...")
        result = delete_data('forecasts', 'product_sku', '*')
        if result is None:
            raise HTTPException(
                status_code=500, 
                detail="Failed to clear forecasts from database"
            )
        print("[Backend] ✅ Forecasts cleared")
        return {"success": True, "message": "Forecasts cleared successfully"}
        
    except Exception as e:
        print(f"[Backend] ❌ Error clearing forecasts: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Starting Lon TukTak Backend Server")
    print("=" * 80)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
 Backend Server")
    print("=" * 80)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
