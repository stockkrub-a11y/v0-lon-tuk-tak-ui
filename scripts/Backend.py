from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import pandas as pd
import io
import uvicorn
from sqlalchemy import text
import sys
import time
import joblib

# Import local modules
from Auto_cleaning import auto_cleaning
from DB_server import engine
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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

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
        "engine_available": engine is not None,
        "connection_test": False,
        "table_exists": False,
        "row_count": 0,
        "sample_data": None,
        "columns": [],
        "error": None
    }
    
    try:
        if not engine:
            result["error"] = "Database engine is None"
            print("ERROR: Database engine is None", flush=True)
            sys.stdout.flush()
            return result
        
        # Test 1: Simple connection test
        print("Test 1: Testing database connection...", flush=True)
        sys.stdout.flush()
        test_query = "SELECT 1 as test"
        test_df = pd.read_sql(test_query, engine)
        result["connection_test"] = True
        print("✅ Database connection successful", flush=True)
        sys.stdout.flush()
        
        # Test 2: Check if table exists
        print("Test 2: Checking if stock_notifications table exists...", flush=True)
        sys.stdout.flush()
        table_check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'stock_notifications'
            ) as table_exists
        """
        table_check_df = pd.read_sql(table_check_query, engine)
        result["table_exists"] = bool(table_check_df.iloc[0]['table_exists'])
        print(f"Table exists: {result['table_exists']}", flush=True)
        sys.stdout.flush()
        
        if not result["table_exists"]:
            result["error"] = "stock_notifications table does not exist"
            return result
        
        # Test 3: Count rows
        print("Test 3: Counting rows in stock_notifications...", flush=True)
        sys.stdout.flush()
        count_query = "SELECT COUNT(*) as count FROM stock_notifications"
        count_df = pd.read_sql(count_query, engine)
        result["row_count"] = int(count_df.iloc[0]['count'])
        print(f"✅ Row count: {result['row_count']}", flush=True)
        sys.stdout.flush()
        
        # Test 4: Get column names
        print("Test 4: Getting column names...", flush=True)
        sys.stdout.flush()
        columns_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stock_notifications'
            ORDER BY ordinal_position
        """
        columns_df = pd.read_sql(columns_query, engine)
        result["columns"] = columns_df['column_name'].tolist()
        print(f"✅ Columns: {result['columns']}", flush=True)
        sys.stdout.flush()
        
        # Test 5: Get sample data
        if result["row_count"] > 0:
            print("Test 5: Fetching sample data...", flush=True)
            sys.stdout.flush()
            sample_query = "SELECT * FROM stock_notifications LIMIT 3"
            sample_df = pd.read_sql(sample_query, engine)
            
            # Convert to dict and handle datetime
            sample_records = sample_df.to_dict('records')
            for record in sample_records:
                for key, value in record.items():
                    if pd.notna(value) and isinstance(value, (pd.Timestamp, datetime)):
                        record[key] = str(value)
            
            result["sample_data"] = sample_records
            print(f"✅ Sample data retrieved: {len(sample_records)} rows", flush=True)
            sys.stdout.flush()
        
        print("="*80 + "\n", flush=True)
        sys.stdout.flush()
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
    
    try:
        if not engine:
            print("ERROR: Database engine not available", flush=True)
            sys.stdout.flush()
            return []
        
        print("Database engine available, executing query...", flush=True)
        sys.stdout.flush()
        
        query = "SELECT * FROM stock_notifications ORDER BY created_at DESC"
        print(f"Query: {query}", flush=True)
        sys.stdout.flush()
        
        df = pd.read_sql(query, engine)
        
        print(f"Query executed. Rows returned: {len(df)}", flush=True)
        sys.stdout.flush()
        
        if df.empty:
            print("DataFrame is empty, returning empty array", flush=True)
            sys.stdout.flush()
            return []
        
        print(f"DataFrame columns: {df.columns.tolist()}", flush=True)
        print(f"First row sample: {df.iloc[0].to_dict()}", flush=True)
        sys.stdout.flush()
        
        # Convert to list of dicts
        notifications = df.to_dict('records')
        
        print(f"Converted to {len(notifications)} notification records", flush=True)
        sys.stdout.flush()
        
        # Convert datetime to string
        for notification in notifications:
            for key, value in notification.items():
                if pd.notna(value) and isinstance(value, (pd.Timestamp, datetime)):
                    notification[key] = str(value)
        
        print(f"Returning {len(notifications)} notifications", flush=True)
        print("="*80 + "\n", flush=True)
        sys.stdout.flush()
        
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
        
        if not engine:
            return {"exists": False, "count": 0}
        
        # Check if table exists and has data
        query = "SELECT COUNT(*) as count FROM base_stock"
        result = pd.read_sql(query, engine)
        count = int(result.iloc[0]['count'])
        
        print(f"[Backend] base_stock exists with {count} rows")
        return {"exists": count > 0, "count": count}
        
    except Exception as e:
        print(f"[Backend] base_stock table doesn't exist or error: {str(e)}")
        return {"exists": False, "count": 0}

@app.post("/notifications/upload")
async def upload_stock_files(
    previous_stock: Optional[UploadFile] = File(None),
    current_stock: UploadFile = File(...)
):
    """Upload stock files and generate notifications"""
    try:
        print("[Backend] Processing stock upload...")
        
        # Read current stock file
        current_content = await current_stock.read()
        df_curr = pd.read_excel(io.BytesIO(current_content))
        print(f"[Backend] Current stock loaded: {len(df_curr)} rows")
        
        # Check if base_stock exists
        base_stock_exists = False
        df_prev = None
        
        try:
            query = "SELECT * FROM base_stock ORDER BY updated_at DESC"
            df_prev = pd.read_sql(query, engine)
            if not df_prev.empty:
                base_stock_exists = True
                print(f"[Backend] Loaded previous stock from database: {len(df_prev)} rows")
        except Exception as e: # More specific exception handling
            print(f"[Backend] base_stock table doesn't exist or error during read: {str(e)}")
            # No need to explicitly set df_prev to None here as it's handled by scope
        
        # If base_stock doesn't exist, require previous stock file
        if not base_stock_exists:
            if not previous_stock:
                raise HTTPException(
                    status_code=400,
                    detail="Previous stock file is required for first upload"
                )
            prev_content = await previous_stock.read()
            # Use header=0 to correctly read Excel files without a skip row
            df_prev = pd.read_excel(io.BytesIO(prev_content), header=0)
            print(f"[Backend] Previous stock loaded from file: {len(df_prev)} rows")
        
        df_curr = df_curr.rename(columns={
            'ชื่อสินค้า': 'product_name',
            'รหัสสินค้า': 'product_sku',
            'จำนวนคงเหลือ': 'stock_level',
            'จำนวน': 'stock_level',
            'หมวดหมู่': 'category'
        })
        df_prev = df_prev.rename(columns={
            'ชื่อสินค้า': 'product_name',
            'รหัสสินค้า': 'product_sku',
            'จำนวนคงเหลือ': 'stock_level',
            'จำนวน': 'stock_level',
            'หมวดหมู่': 'category'
        })
        df_curr["stock_level"] = pd.to_numeric(df_curr["stock_level"], errors='coerce').fillna(0).astype(int)
        df_prev["stock_level"] = pd.to_numeric(df_prev["stock_level"], errors='coerce').fillna(0).astype(int)
        
        # Generate stock report
        print("[Backend] Generating stock report...")
        report_df = generate_stock_report(df_prev, df_curr)
        print(f"[Backend] Report generated: {len(report_df)} items")
        
        report_df['unchanged_counter'] = 0
        report_df['flag'] = 'stage'
        
        # Calculate flags based on stock changes
        print("[Backend] Calculating stock flags...")
        for idx, row in report_df.iterrows():
            product_sku = row.get('Product_SKU', '')
            current_stock_level = row.get('Stock', 0)
            last_stock_level = row.get('Last_Stock', 0)
            
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
        report_df.to_sql('stock_notifications', engine, if_exists='replace', index=False)
        
        print("[Backend] Updating base_stock table...")
        
        flag_map = dict(zip(report_df['Product_SKU'], report_df['flag']))
        counter_map = dict(zip(report_df['Product_SKU'], report_df['unchanged_counter']))
        
        # Build base_stock_df with proper alignment
        base_stock_data = []
        for idx, row in df_curr.iterrows():
            product_sku = row.get('product_sku', '')
            base_stock_data.append({
                'product_name': row.get('product_name', ''),
                'product_sku': product_sku,
                'stock_level': row.get('stock_level', 0),
                'หมวดหมู่': row.get('category', ''),
                'unchanged_counter': counter_map.get(product_sku, 0),
                'flag': flag_map.get(product_sku, 'stage'),
                'updated_at': datetime.now()
            })
        
        base_stock_df = pd.DataFrame(base_stock_data)
        
        # Clear and insert new data
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM base_stock"))
        base_stock_df.to_sql('base_stock', engine, if_exists='append', index=False)
        
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
        
        if not engine:
            raise HTTPException(status_code=500, detail="Database not available")
        
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM base_stock"))
            conn.execute(text("DELETE FROM stock_notifications"))
        
        print("[Backend] ✅ base_stock and stock_notifications cleared")
        return {"success": True, "message": "Stock data cleared successfully"}
        
    except Exception as e:
        print(f"[Backend] ❌ Error clearing stock data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notifications/update_manual_values")
async def update_manual_values_endpoint(
    product_sku: str = Query(..., description="Product SKU"),
    minstock: Optional[int] = Query(None, description="Manual MinStock value"),
    buffer: Optional[int] = Query(None, description="Manual Buffer value")
):
    """Update manual MinStock and Buffer values and recalculate that product"""
    try:
        print(f"[Backend] Updating manual values for {product_sku}: MinStock={minstock}, Buffer={buffer}")
        
        if not engine:
            raise HTTPException(status_code=500, detail="Database not available")
        
        query = text("SELECT * FROM stock_notifications WHERE Product_SKU = :sku")
        df_notification = pd.read_sql(query, engine, params={"sku": product_sku})
        
        if df_notification.empty:
            raise HTTPException(status_code=404, detail=f"Product {product_sku} not found in notifications")
        
        row = df_notification.iloc[0]
        
        # Get values from the row
        stock = row['Stock']
        last_stock = row['Last_Stock']
        weekly_sale = max((last_stock - stock), 1)
        decrease_rate = ((last_stock - stock) / last_stock * 100) if last_stock > 0 else 0
        weeks_to_empty = stock / weekly_sale if weekly_sale > 0 else 0
        
        # Apply manual values or use defaults
        if minstock is not None:
            new_minstock = minstock
        else:
            new_minstock = int(weekly_sale * 2 * 1.5)  # WEEKS_TO_COVER = 2, SAFETY_FACTOR = 1.5
        
        if buffer is not None:
            new_buffer = buffer
        else:
            if decrease_rate > 50:
                new_buffer = 20
            elif decrease_rate > 20:
                new_buffer = 10
            else:
                new_buffer = 5
            new_buffer = min(new_buffer, 50)  # MAX_BUFFER = 50
        
        # Calculate new reorder quantity
        default_reorder = int(weekly_sale * 1.5)
        new_reorder_qty = max(new_minstock + new_buffer - stock, default_reorder)
        
        # Determine status
        is_red = (stock < new_minstock) or (decrease_rate > 50)
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
        
        update_query = text("""
            UPDATE stock_notifications
            SET "MinStock" = :minstock,
                "Buffer" = :buffer,
                "Reorder_Qty" = :reorder_qty,
                "Status" = :status,
                "Description" = :description
            WHERE "Product_SKU" = :sku
        """)
        
        with engine.begin() as conn:
            conn.execute(update_query, {
                "minstock": new_minstock,
                "buffer": new_buffer,
                "reorder_qty": new_reorder_qty,
                "status": new_status,
                "description": new_description,
                "sku": product_sku
            })
        
        print(f"[Backend] ✅ Updated manual values for {product_sku}")
        return {
            "success": True,
            "message": "Manual values updated successfully",
            "product_sku": product_sku,
            "minstock": new_minstock,
            "buffer": new_buffer,
            "reorder_qty": new_reorder_qty,
            "status": new_status
        }
        
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
        
        if not engine:
            return {"success": False, "data": []}
        
        query = text("""
            SELECT 
                product_name,
                product_sku,
                stock_level as quantity,
                "หมวดหมู่" as category,
                flag as status,
                unchanged_counter,
                updated_at
            FROM base_stock
            WHERE 1=1
        """)
        
        # Build conditions
        conditions = []
        params = {}
        
        if category:
            conditions.append('"หมวดหมู่" = :category')
            params['category'] = category
        if status:
            conditions.append('flag = :status')
            params['status'] = status
        
        # Add conditions to query
        if conditions:
            query = text(str(query) + " AND " + " AND ".join(conditions))
        
        # Add sorting
        if sort_by == "quantity_asc":
            query = text(str(query) + " ORDER BY stock_level ASC")
        elif sort_by == "quantity_desc":
            query = text(str(query) + " ORDER BY stock_level DESC")
        else:
            query = text(str(query) + " ORDER BY product_name ASC")
        
        df = pd.read_sql(query, engine, params=params if params else None)
        
        if not df.empty:
            print(f"[Backend] ✅ Retrieved {len(df)} stock items")
            # Convert datetime to string
            for idx, row in df.iterrows():
                if 'updated_at' in df.columns and pd.notna(row['updated_at']):
                    df.at[idx, 'updated_at'] = str(row['updated_at'])
            return {"success": True, "data": df.to_dict('records')}
        else:
            print("[Backend] No stock data found")
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
        
        if not engine:
            return {"success": False, "data": []}
        
        try:
            query = text('SELECT DISTINCT "หมวดหมู่" as category FROM base_stock WHERE "หมวดหมู่" IS NOT NULL')
            df = pd.read_sql(query, engine)
            
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
        
        if not engine:
            return {
                "success": False,
                "data": {
                    "total_stock_items": 0,
                    "low_stock_alerts": 0,
                    "sales_this_month": 0,
                    "out_of_stock": 0
                }
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
    try:
        print(f"[Backend] Fetching base SKUs with search: '{search}'")
        
        if not engine:
            return {"success": False, "base_skus": [], "results": [], "total": 0}
        
        try:
            query = """
                SELECT DISTINCT product_sku, "หมวดหมู่" as category
                FROM base_stock
                WHERE product_sku IS NOT NULL
            """
            
            if search:
                # Search in both SKU and category
                query += f" AND (product_sku ILIKE '%{search}%' OR \"หมวดหมู่\" ILIKE '%{search}%')"
            
            query += " ORDER BY product_sku ASC LIMIT 100"
            
            df = pd.read_sql(query, engine)
            
            if not df.empty:
                # Return both SKU and category for display
                results = df.to_dict('records')
                print(f"[Backend] ✅ Found {len(results)} items matching search")
                return {"success": True, "base_skus": [item['product_sku'] for item in results], "results": results, "total": len(results)}
            else:
                print("[Backend] No items found")
                return {"success": True, "base_skus": [], "results": [], "total": 0}
                
        except Exception as db_error:
            print(f"[Backend] Database query failed: {str(db_error)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "base_skus": [], "results": [], "total": 0}
        
    except Exception as e:
        print(f"[Backend] ❌ Error fetching base SKUs: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "base_skus": [], "results": [], "total": 0}

@app.get("/analysis/historical")
async def get_analysis_historical_sales(sku: str = Query(..., description="Product SKU or category to analyze")):
    """Get historical stock data from base_stock table"""
    try:
        print(f"[Backend] Fetching historical stock data for: {sku}")
        
        if not engine:
            return {"success": False, "message": "Database not available", "chart_data": [], "table_data": [], "search_type": "unknown"}
        
        try:
            # Check if it's a specific SKU
            sku_check_query = text("""
                SELECT COUNT(*) as count
                FROM base_stock
                WHERE product_sku = :sku
            """)
            
            with engine.connect() as conn:
                sku_result = conn.execute(sku_check_query, {"sku": sku})
                is_sku = sku_result.fetchone()[0] > 0
            
            if is_sku:
                print(f"[Backend] Detected SKU search for: {sku}")
                
                sales_query = text("""
                    SELECT 
                        product_sku,
                        product_name,
                        sales_month as month,
                        sales_year as year,
                        SUM(total_quantity) as quantity
                    FROM base_data
                    WHERE product_sku = :sku
                    GROUP BY product_sku, product_name, sales_month, sales_year
                    ORDER BY sales_year, sales_month
                """)
                
                df = pd.read_sql(sales_query, engine, params={"sku": sku})
                
                if df.empty:
                    return {
                        "success": True,
                        "message": "No sales data found for this SKU",
                        "chart_data": [],
                        "table_data": [],
                        "search_type": "sku"
                    }
                
                # Format chart data for line chart (month on X-axis)
                chart_data = []
                for _, row in df.iterrows():
                    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                    month_label = f"{month_names[int(row['month'])-1]} {int(row['year'])}"
                    chart_data.append({
                        "month": month_label,
                        "quantity": int(row['quantity'])
                    })
                
                # Table data
                table_data = [{
                    "product_sku": sku,
                    "product_name": df.iloc[0]['product_name'],
                    "total_quantity": int(df['quantity'].sum())
                }]
                
                return {
                    "success": True,
                    "message": "Sales data retrieved successfully",
                    "chart_data": chart_data,
                    "table_data": table_data,
                    "search_type": "sku"
                }
            
            else:
                print(f"[Backend] Detected category search for: {sku}")
                
                category_query = text("""
                    SELECT 
                        product_sku,
                        product_name,
                        stock_level,
                        "หมวดหมู่" as category,
                        flag
                    FROM base_stock
                    WHERE "หมวดหมู่" ILIKE :category_pattern
                    ORDER BY product_name ASC
                """)
                
                df = pd.read_sql(category_query, engine, params={"category_pattern": f"%{sku}%"})
                
                if df.empty:
                    return {
                        "success": True,
                        "message": "No products found in this category",
                        "chart_data": [],
                        "table_data": [],
                        "search_type": "category"
                    }
                
                chart_data = []
                for _, row in df.iterrows():
                    full_name = row['product_name']
                    display_name = full_name[:30] + "..." if len(full_name) > 30 else full_name
                    chart_data.append({
                        "product_name": full_name,  # Full name for tooltip
                        "display_name": display_name,  # Truncated name for X-axis
                        "stock_level": int(row['stock_level'])
                    })
                
                # Table data
                table_data = df[['product_sku', 'product_name', 'stock_level', 'category', 'flag']].to_dict('records')
                
                return {
                    "success": True,
                    "message": f"Found {len(df)} products in category",
                    "chart_data": chart_data,
                    "table_data": table_data,
                    "search_type": "category"
                }
            
        except Exception as db_error:
            print(f"[Backend] Database query failed: {str(db_error)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Database error: {str(db_error)}",
                "chart_data": [],
                "table_data": [],
                "search_type": "unknown"
            }
        
    except Exception as e:
        print(f"[Backend] ❌ Error fetching historical stock: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "chart_data": [],
            "table_data": [],
            "search_type": "unknown"
        }

@app.post("/analysis/performance")
async def get_analysis_performance(request: dict):
    """Get performance comparison data from base_data table"""
    try:
        sku_list = request.get('sku_list', [])
        print(f"[Backend] Fetching performance comparison for SKUs: {sku_list}")
        
        if not engine:
            return {"success": False, "message": "Database not available", "chart_data": {}, "table_data": []}
        
        if not sku_list or len(sku_list) == 0:
            return {"success": False, "message": "No SKUs provided", "chart_data": {}, "table_data": []}
        
        try:
            placeholders = ', '.join([f':sku{i}' for i in range(len(sku_list))])
            query = text(f"""
                SELECT 
                    product_sku as "Item",
                    product_name as "Product_name",
                    EXTRACT(MONTH FROM sales_date) as month,
                    SUM(total_quantity) as "Quantity"
                FROM base_data
                WHERE product_sku IN ({placeholders})
                GROUP BY product_sku, product_name, EXTRACT(MONTH FROM sales_date)
                ORDER BY product_sku, month
            """)
            
            # Create params dict
            params = {f'sku{i}': sku for i, sku in enumerate(sku_list)}
            
            df = pd.read_sql(query, engine, params=params)
            
            if df.empty:
                print(f"[Backend] No performance data found for SKUs: {sku_list}")
                return {
                    "success": True,
                    "message": "No data found for selected SKUs",
                    "chart_data": {},
                    "table_data": []
                }
            
            print(f"[Backend] ✅ Retrieved {len(df)} performance records")
            
            # Prepare chart data (scatter plot format)
            chart_data = {}
            for sku in sku_list:
                sku_data = df[df['Item'] == sku]
                if not sku_data.empty:
                    chart_data[sku] = [
                        {"month": int(row['month']), "value": int(row['Quantity'])}
                        for _, row in sku_data.iterrows()
                    ]
            
            # Prepare table data (aggregated totals)
            table_data = df.groupby(['Item', 'Product_name']).agg({
                'Quantity': 'sum'
            }).reset_index()
            
            return {
                "success": True,
                "message": "Performance data retrieved successfully",
                "chart_data": chart_data,
                "table_data": table_data.to_dict('records')
            }
            
        except Exception as db_error:
            print(f"[Backend] Database query failed: {str(db_error)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Database error: {str(db_error)}",
                "chart_data": {},
                "table_data": []
            }
        
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
        
        if not engine:
            return {"success": False, "message": "Database not available", "data": []}
        
        try:
            query = text("""
                SELECT 
                    product_sku,
                    product_name,
                    SUM(total_quantity) as total_quantity_sold
                FROM base_data
                WHERE sales_year = :year
                AND sales_month = :month
                GROUP BY product_sku, product_name
                ORDER BY total_quantity_sold DESC
                LIMIT :limit
            """)
            
            df = pd.read_sql(query, engine, params={"year": year, "month": month, "limit": limit})
            
            if not df.empty:
                result = []
                for idx, row in df.iterrows():
                    result.append({
                        "rank": idx + 1,
                        "name": row['product_name'],
                        "base_sku": row['product_sku'],
                        "size": 'N/A',  # base_data doesn't have size column
                        "quantity": int(row['total_quantity_sold'])
                    })
                
                print(f"[Backend] ✅ Retrieved {len(result)} best sellers")
                return {"success": True, "message": "Best sellers retrieved successfully", "data": result}
            else:
                print(f"[Backend] No best sellers found for {year}-{month:02d}")
                return {"success": True, "message": "No best sellers found for the specified period", "data": []}
                
        except Exception as db_error:
            print(f"[Backend] Database query failed: {str(db_error)}")
            return {"success": False, "message": f"Database error: {str(db_error)}", "data": []}
            
    except Exception as e:
        print(f"[Backend] Error in best_sellers endpoint: {str(e)}")
        return {"success": False, "message": f"Server error: {str(e)}", "data": []}

@app.get("/analysis/performance-products")
async def get_performance_products(search: str = Query("", description="Search term for products")):
    """Get products grouped by category from base_stock table"""
    try:
        print(f"[Backend] Fetching performance products from base_stock with search: '{search}'")
        
        if not engine:
            return {"success": False, "categories": {}, "all_products": []}
        
        try:
            # Get products from base_stock table with category information
            query = text("""
                SELECT DISTINCT 
                    product_sku,
                    product_name,
                    COALESCE("หมวดหมู่", 'Uncategorized') as category
                FROM base_stock
                WHERE product_sku IS NOT NULL AND product_name IS NOT NULL
                ORDER BY category, product_name
            """)
            
            df = pd.read_sql(query, engine)
            
            if df.empty:
                print("[Backend] No products found in base_stock table")
                return {"success": True, "categories": {}, "all_products": []}
            
            # Apply search filter if provided (only on SKU for search box)
            if search:
                mask = df['product_sku'].str.contains(search, case=False, na=False)
                df = df[mask]
            
            # Group products by category
            categories = {}
            for category in sorted(df['category'].unique()):
                if pd.notna(category):
                    category_products = df[df['category'] == category][['product_sku', 'product_name']].to_dict('records')
                    categories[category] = category_products
            
            # Also return flat list of all products
            all_products = df[['product_sku', 'product_name', 'category']].to_dict('records')
            
            print(f"[Backend] ✅ Found {len(categories)} categories with {len(all_products)} total products from base_stock")
            return {
                "success": True,
                "categories": categories,
                "all_products": all_products
            }
            
        except Exception as db_error:
            print(f"[Backend] Database query failed: {str(db_error)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "categories": {}, "all_products": []}
            
    except Exception as e:
        print(f"[Backend] ❌ Error fetching performance products: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "categories": {}, "all_products": []}

@app.get("/analysis/total_income")
async def get_total_income(product_sku: str = "", category: str = ""):
    """Get total income analysis from base_data table with optional filters"""
    try:
        if not engine:
            return {"success": False, "message": "Database not available"}
        
        print(f"[Backend] Fetching total income data (product_sku={product_sku}, category={category})...")
        
        # Build WHERE clause based on filters
        where_conditions = ["bd.total_quantity IS NOT NULL"]
        joins = ""
        
        if product_sku:
            where_conditions.append(f"bd.product_sku = '{product_sku}'")
        
        if category:
            # Join with base_stock to filter by category
            joins = 'INNER JOIN base_stock bs ON bd.product_sku = bs.product_sku'
            where_conditions.append(f"bs.\"หมวดหมู่\" = '{category}'")
        
        where_clause = " AND ".join(where_conditions)
        
        # Query to get monthly sales totals
        query = text(f"""
            SELECT 
                bd.sales_year,
                bd.sales_month,
                SUM(bd.total_quantity) as total_quantity
            FROM base_data bd
            {joins}
            WHERE {where_clause}
            GROUP BY bd.sales_year, bd.sales_month
            ORDER BY bd.sales_year, bd.sales_month
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query)
            monthly_data = result.fetchall()
        
        if not monthly_data:
            return {
                "success": True,
                "chart_data": [],
                "table_data": [],
                "grand_total": 0,
                "message": "No data found for selected filters"
            }
        
        # Format chart data
        chart_data = []
        for row in monthly_data:
            chart_data.append({
                "month": f"{row[0]}-{row[1]:02d}",
                "total_income": float(row[2]) if row[2] else 0
            })
        
        # Query to get product-level sales data
        product_query = text(f"""
            SELECT 
                bd.product_name,
                bd.product_sku,
                AVG(bd.total_quantity) as avg_monthly_quantity,
                SUM(bd.total_quantity) as total_quantity
            FROM base_data bd
            {joins}
            WHERE {where_clause} AND bd.product_name IS NOT NULL
            GROUP BY bd.product_name, bd.product_sku
            ORDER BY total_quantity DESC
        """)
        
        with engine.connect() as conn:
            result = conn.execute(product_query)
            product_data = result.fetchall()
        
        # Format table data
        table_data = []
        for row in product_data:
            table_data.append({
                "Product_name": row[0],
                "Product_sku": row[1],
                "Avg_Monthly_Revenue_Baht": float(row[2]) if row[2] else 0,
                "Total_Quantity": int(row[3]) if row[3] else 0
            })
        
        # Calculate grand total
        grand_total = sum(item["total_income"] for item in chart_data)
        
        print(f"[Backend] ✅ Total quantity sold: {grand_total:,.0f} units (filters: product_sku={product_sku}, category={category})")
        
        return {
            "success": True,
            "chart_data": chart_data,
            "table_data": table_data,
            "grand_total": grand_total
        }
        
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
        
        if not engine:
            return {"success": False, "suggestions": []}
        
        if not search or len(search) < 1:
            return {"success": True, "suggestions": []}
        
        try:
            query = text("""
                SELECT DISTINCT 
                    product_sku as value,
                    'SKU' as type,
                    product_name as label
                FROM base_stock
                WHERE product_sku ILIKE :search_pattern
                
                UNION
                
                SELECT DISTINCT 
                    "หมวดหมู่" as value,
                    'Category' as type,
                    "หมวดหมู่" as label
                FROM base_stock
                WHERE "หมวดหมู่" ILIKE :search_pattern
                AND "หมวดหมู่" IS NOT NULL
                
                ORDER BY type DESC, value ASC
                LIMIT 10
            """)
            
            df = pd.read_sql(query, engine, params={"search_pattern": f"%{search}%"})
            
            if not df.empty:
                suggestions = df.to_dict('records')
                print(f"[Backend] ✅ Found {len(suggestions)} suggestions")
                return {"success": True, "suggestions": suggestions}
            else:
                return {"success": True, "suggestions": []}
                
        except Exception as db_error:
            print(f"[Backend] Database query failed: {str(db_error)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "suggestions": []}
        
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
        
        if not engine:
            raise HTTPException(status_code=500, detail="Database not available")
        
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
            print(f"[Backend] Calling auto_cleaning with sales_path={sales_temp_path}, product_path={product_temp_path}, engine={engine}")
            df_cleaned = auto_cleaning(sales_temp_path, product_temp_path, engine)
            
            rows_uploaded = len(df_cleaned)
            print(f"[Backend] Cleaned data: {rows_uploaded} rows")
            
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
            
            # Train the model
            print("[Backend] Training forecasting model...")
            try:
                df_window_raw, df_window, base_model, X_train, y_train, X_test, y_test, product_sku_last = update_model_and_train(df_cleaned)
                
                print("[Backend] ✅ Model training completed successfully")
                
                response["ml_training"] = {
                    "status": "completed",
                    "message": "Model trained successfully"
                }
                
                try:
                    print("[Backend] Attempting to generate forecasts...")
                    long_forecast, forecast_results = forcast_loop(X_train, y_train, df_window_raw, product_sku_last, base_model)
                    
                    if forecast_results and len(forecast_results) > 0:
                        # Save forecasts to database
                        forecast_df = pd.DataFrame(forecast_results)
                        forecast_df['created_at'] = datetime.now()
                        
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("DELETE FROM forecasts"))
                        except:
                            # Table might not exist, create it
                            print("[Backend] Creating forecasts table...")
                            create_forecasts_table = """
                                CREATE TABLE IF NOT EXISTS forecasts (
                                    id SERIAL PRIMARY KEY,
                                    product_sku VARCHAR(255),
                                    forecast_date DATE,
                                    predicted_sales INTEGER,
                                    current_sales INTEGER,
                                    current_date_col DATE,
                                    created_at TIMESTAMP
                                )
                            """
                            with engine.begin() as conn:
                                conn.execute(text(create_forecasts_table))
                        
                        forecast_df.to_sql('forecasts', engine, if_exists='append', index=False)
                        
                        print(f"[Backend] ✅ Generated {len(forecast_results)} forecasts")
                        
                        response["ml_training"]["forecast_rows"] = len(forecast_results)
                        response["ml_training"]["message"] = f"Model trained and {len(forecast_results)} forecasts generated"
                    else:
                        response["ml_training"]["message"] = "Model trained but no forecasts generated"
                        
                except Exception as forecast_error:
                    print(f"[Backend] ⚠️ Forecast generation failed: {str(forecast_error)}")
                    import traceback
                    traceback.print_exc()
                    response["ml_training"]["message"] = f"Model trained but forecast generation failed: {str(forecast_error)}"
                
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
        
        if not engine:
            return {"success": False, "forecast": []}
        
        try:
            query = """
                SELECT 
                    product_sku,
                    forecast_date,
                    predicted_sales,
                    current_sales,
                    current_date_col,
                    created_at
                FROM forecasts
                ORDER BY product_sku ASC, forecast_date ASC
            """
            df = pd.read_sql(query, engine)
            
            if not df.empty:
                print(f"[Backend] ✅ Retrieved {len(df)} forecasts")
                for idx, row in df.iterrows():
                    if 'forecast_date' in df.columns and pd.notna(row['forecast_date']):
                        df.at[idx, 'forecast_date'] = str(row['forecast_date'])
                    if 'current_date_col' in df.columns and pd.notna(row['current_date_col']):
                        df.at[idx, 'current_date_col'] = str(row['current_date_col'])
                    if 'created_at' in df.columns and pd.notna(row['created_at']):
                        df.at[idx, 'created_at'] = str(row['created_at'])
                
                return {"success": True, "forecast": df.to_dict('records')}
            else:
                print("[Backend] No forecasts found")
                return {"success": True, "forecast": []}
                
        except Exception as db_error:
            print(f"[Backend] Forecasts table doesn't exist or query failed: {str(db_error)}")
            return {"success": True, "forecast": []}
        
    except Exception as e:
        print(f"[Backend] ❌ Error fetching forecasts: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "forecast": [], "error": str(e)}

@app.post("/predict")
async def predict_sales(n_forecast: int = Query(3, description="Number of months to forecast")):
    """Generate sales forecasts for n months"""
    try:
        print(f"[Backend] Generating {n_forecast} month forecast...")
        
        if not engine:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Check if model is trained (base_data exists)
        try:
            check_query = "SELECT COUNT(*) as count FROM base_data"
            result = pd.read_sql(check_query, engine)
            if result.iloc[0]['count'] == 0:
                raise HTTPException(
                    status_code=400,
                    detail="No training data available. Please train the model first."
                )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail="Model not trained. Please upload and train with data first."
            )
        
        print("[Backend] Loading trained model and data...")
        
        if not os.path.exists("xgb_sales_model.pkl"):
            raise HTTPException(
                status_code=400,
                detail="Model file not found. Please train the model first."
            )
        
        # Load model
        base_model = joblib.load("xgb_sales_model.pkl")
        
        # Get the latest training data from base_data
        query = "SELECT * FROM base_data ORDER BY sales_date DESC"
        df_cleaned = pd.read_sql(query, engine)
        
        # Recreate the training data
        print("[Backend] Preparing training data...")
        df_window_raw, df_window, _, X_train, y_train, X_test, y_test, product_sku_last = update_model_and_train(df_cleaned)
        
        # Run forecast loop with n_forecast parameter
        print(f"[Backend] Running forecast loop for {n_forecast} months...")
        long_forecast, forecast_results = forcast_loop(X_train, y_train, df_window_raw, product_sku_last, base_model, n_forecast=n_forecast)
        
        # Save forecasts to database
        print("[Backend] Saving forecasts to database...")
        forecast_df = pd.DataFrame(forecast_results)
        forecast_df['created_at'] = datetime.now()
        
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM forecasts"))
        except:
            # Table might not exist, create it
            print("[Backend] Creating forecasts table...")
            create_forecasts_table = """
                CREATE TABLE IF NOT EXISTS forecasts (
                    id SERIAL PRIMARY KEY,
                    product_sku VARCHAR(255),
                    forecast_date DATE,
                    predicted_sales INTEGER,
                    current_sales INTEGER,
                    current_date_col DATE,
                    created_at TIMESTAMP
                )
            """
            with engine.begin() as conn:
                conn.execute(text(create_forecasts_table))
        
        forecast_df.to_sql('forecasts', engine, if_exists='append', index=False)
        
        print(f"[Backend] ✅ Generated {len(forecast_results)} forecasts for {n_forecast} months")
        
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
        
        if not engine:
            raise HTTPException(status_code=500, detail="Database not available")
        
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM forecasts"))
        
        print("[Backend] ✅ Forecasts cleared")
        return {"success": True, "message": "Forecasts cleared successfully"}
        
    except Exception as e:
        print(f"[Backend] ❌ Error clearing forecasts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Starting Lon TukTak Backend Server")
    print("=" * 80)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
