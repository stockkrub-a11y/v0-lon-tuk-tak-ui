# ================= Backend: Postgres Version =================
import pandas as pd
import numpy as np  # Added numpy import for vectorized operations
# from DB_server import engine  # Removed: SQLAlchemy engine no longer used

# Configuration constants
SAFETY_FACTOR = 1.5
WEEKS_TO_COVER = 2
MAX_BUFFER = 50

from DB_server import execute_query

def get_manual_values(product_sku: str):
    """Get manual MinStock and Buffer values from database"""
    try:
        df = execute_query(f"SELECT min_stock, buffer FROM stock_notifications WHERE product_sku = '{product_sku}'")
        if df is not None and not df.empty:
            return {
                'min_stock': df.iloc[0]['min_stock'] if pd.notna(df.iloc[0]['min_stock']) else None,
                'buffer': df.iloc[0]['buffer'] if pd.notna(df.iloc[0]['buffer']) else None
            }
    except Exception as e:
        print(f"Warning: Failed to get manual values from DB: {e}")
    return {'min_stock': None, 'buffer': None}

# ================= Get latest stock per product =================
def get_data(week_date):
    # Not implemented: Needs migration to Supabase
    raise NotImplementedError("get_data() needs to be migrated to use Supabase client.")

# ================= Generate Stock Report =================
def generate_stock_report(df_prev, df_curr):
    """
    df_curr: columns ['product_name', 'product_sku', 'stock_level', 'category']
    df_prev: columns ['product_name', 'product_sku', 'stock_level', 'category']
    """
    df_prev_unique = df_prev.drop_duplicates(subset='product_sku', keep='last')
    prev_lookup = df_prev_unique.set_index('product_sku')['stock_level']
    
    name_lookup = df_curr.drop_duplicates(subset='product_sku', keep='last').set_index('product_sku')['product_name']
    category_lookup = df_curr.drop_duplicates(subset='product_sku', keep='last').set_index('product_sku')['category']

    curr = df_curr.drop_duplicates(subset='product_sku', keep='last').copy()

    # Ensure all column names are lowercase
    curr.columns = curr.columns.str.lower()
    
    # No need to rename since we're using lowercase everywhere now
    # Map last_stock from previous data
    curr['last_stock'] = curr['product_sku'].map(prev_lookup).fillna(curr['stock_level'])

    # Weekly sales and decrease rate
    curr['weekly_sale'] = (curr['last_stock'] - curr['stock_level']).clip(lower=1)
    curr['decrease_rate'] = np.where(
        curr['last_stock'] > 0,
        (curr['last_stock'] - curr['stock_level']) / curr['last_stock'] * 100,
        0
    ).round(1)

    # Weeks to empty
    curr['weeks_to_empty'] = (curr['stock_level'] / curr['weekly_sale']).round(2)

    # Get manual values from database for all products
    manual_values_df = execute_query("SELECT product_sku, min_stock, buffer FROM stock_notifications")
    manual_min_map = {}
    manual_buf_map = {}
    
    if manual_values_df is not None and not manual_values_df.empty:
        manual_min_map = manual_values_df.set_index('product_sku')['min_stock'].to_dict()
        manual_buf_map = manual_values_df.set_index('product_sku')['buffer'].to_dict()
    
    # min_stock: manual override, else formula
    default_min = (curr['weekly_sale'] * WEEKS_TO_COVER * SAFETY_FACTOR).astype(int)
    manual_min = curr['product_sku'].map(manual_min_map)
    curr['min_stock'] = np.where(manual_min.notna(), manual_min, default_min).astype(int)

    # Calculate buffer using manual values from DB
    dyn_buf = np.select(
        [curr['decrease_rate'] > 50, curr['decrease_rate'] > 20],
        [20, 10],
        default=5
    )
    dyn_buf = np.minimum(dyn_buf, MAX_BUFFER)
    manual_buf = curr['product_sku'].map(manual_buf_map)
    buffer_values = np.where(manual_buf.notna(), manual_buf, dyn_buf).astype(int)

    # Reorder quantity (at least SAFETY_FACTOR * weekly sale)
    default_reorder = (curr['weekly_sale'] * SAFETY_FACTOR).astype(int)
    curr['reorder_qty'] = np.maximum(curr['min_stock'] + buffer_values - curr['stock_level'], default_reorder).astype(int)

    # status + description
    is_red = (curr['stock_level'] < curr['min_stock']) | (curr['decrease_rate'] > 50)
    is_yellow = (~is_red) & (curr['decrease_rate'] > 20)

    curr['status'] = np.where(is_red, 'Red', np.where(is_yellow, 'Yellow', 'Green'))
    curr['description'] = np.where(
        is_red,
        'Decreasing rapidly and nearly out of stock! Recommend restocking ' + curr['reorder_qty'].astype(str) + ' units',
        np.where(
            is_yellow,
            'Decreasing rapidly, should prepare to restock. Recommend restocking ' + curr['reorder_qty'].astype(str) + ' units',
            'Stock is sufficient'
        )
    )

    # Return only the columns that match our DB schema
    return curr[[
        'product_name', 'product_sku', 'category', 'stock_level', 'last_stock',
        'decrease_rate', 'weeks_to_empty', 'min_stock', 'reorder_qty',
        'status', 'description'
    ]].reset_index(drop=True)

from DB_server import update_data

def update_manual_values(product_sku: str, minstock: int = None, buffer: int = None):
    """Update manual MinStock and Buffer values in the database"""
    update_payload = {}
    if minstock is not None:
        update_payload['min_stock'] = minstock
    if buffer is not None:
        update_payload['reorder_qty'] = buffer
        
    if update_payload:
        try:
            result = update_data('stock_notifications', update_payload, 'product_sku', product_sku)
            if result is None:
                print(f"Warning: Failed to update manual values for {product_sku}")
                return False
            return True
        except Exception as e:
            print(f"Error updating manual values: {e}")
            return False
    return True

# ================= Get Notifications =================
def get_notifications():
    """
    Returns notification list (summary view).
    """
    print("[Notification] get_notifications() called")
    
    # Not implemented: Needs migration to Supabase
    raise NotImplementedError("get_notifications() needs to be migrated to use Supabase client.")


def get_notification_detail(product_name: str):
    """
    Returns detailed metrics for one product.
    """
    # Not implemented: Needs migration to Supabase
    raise NotImplementedError("get_notification_detail() needs to be migrated to use Supabase client.")
