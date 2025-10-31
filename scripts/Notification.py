# ================= Backend: Postgres Version =================
import pandas as pd
import numpy as np  # Added numpy import for vectorized operations
# from DB_server import engine  # Removed: SQLAlchemy engine no longer used

# Manual overrides
manual_minstock = {}  # {'Product_SKU': value}
manual_buffer = {}    # {'Product_SKU': value}

SAFETY_FACTOR = 1.5
WEEKS_TO_COVER = 2
MAX_BUFFER = 50

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
    
    curr.rename(columns={
        'product_sku': 'Product_SKU', 
        'product_name': 'Product',
        'stock_level': 'Stock',
        'category': 'Category'
    }, inplace=True)

    # Last_Stock = previous snapshot if available, else fall back to current stock
    curr['Last_Stock'] = curr['Product_SKU'].map(prev_lookup).fillna(curr['Stock'])

    # Weekly sales and decrease rate
    curr['Weekly_Sale'] = (curr['Last_Stock'] - curr['Stock']).clip(lower=1)
    curr['Decrease_Rate(%)'] = np.where(
        curr['Last_Stock'] > 0,
        (curr['Last_Stock'] - curr['Stock']) / curr['Last_Stock'] * 100,
        0
    ).round(1)

    # Weeks to empty
    curr['Weeks_To_Empty'] = (curr['Stock'] / curr['Weekly_Sale']).round(2)

    # MinStock: manual override, else formula
    default_min = (curr['Weekly_Sale'] * WEEKS_TO_COVER * SAFETY_FACTOR).astype(int)
    manual_min = curr['Product_SKU'].map(manual_minstock)
    curr['MinStock'] = np.where(manual_min.notna(), manual_min, default_min).astype(int)

    # Buffer: dynamic by decrease rate, capped; manual override if present
    dyn_buf = np.select(
        [curr['Decrease_Rate(%)'] > 50, curr['Decrease_Rate(%)'] > 20],
        [20, 10],
        default=5
    )
    dyn_buf = np.minimum(dyn_buf, MAX_BUFFER)
    manual_buf = curr['Product_SKU'].map(manual_buffer)
    curr['Buffer'] = np.where(manual_buf.notna(), manual_buf, dyn_buf).astype(int)

    # Reorder quantity (at least SAFETY_FACTOR * weekly sale)
    default_reorder = (curr['Weekly_Sale'] * SAFETY_FACTOR).astype(int)
    curr['Reorder_Qty'] = np.maximum(curr['MinStock'] + curr['Buffer'] - curr['Stock'], default_reorder).astype(int)

    # Status + Description
    is_red = (curr['Stock'] < curr['MinStock']) | (curr['Decrease_Rate(%)'] > 50)
    is_yellow = (~is_red) & (curr['Decrease_Rate(%)'] > 20)

    curr['Status'] = np.where(is_red, 'Red', np.where(is_yellow, 'Yellow', 'Green'))
    curr['Description'] = np.where(
        is_red,
        'Decreasing rapidly and nearly out of stock! Recommend restocking ' + curr['Reorder_Qty'].astype(str) + ' units',
        np.where(
            is_yellow,
            'Decreasing rapidly, should prepare to restock. Recommend restocking ' + curr['Reorder_Qty'].astype(str) + ' units',
            'Stock is sufficient'
        )
    )

    return curr[['Product', 'Product_SKU', 'Category', 'Stock', 'Last_Stock', 'Decrease_Rate(%)', 'Weeks_To_Empty',
                 'MinStock', 'Buffer', 'Reorder_Qty', 'Status', 'Description']].reset_index(drop=True)

def update_manual_values(product_sku: str, minstock: int = None, buffer: int = None):
    """Update manual MinStock and Buffer values for a product"""
    if minstock is not None:
        manual_minstock[product_sku] = minstock
    if buffer is not None:
        manual_buffer[product_sku] = buffer

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
