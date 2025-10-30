import os
import pandas as pd
from math import ceil
from sqlalchemy import text, Integer, inspect

def check_db_status(engine):
    """
    Quick sanity check for base_data and all_products tables.
    Shows row counts and sales_date range (if available).
    """
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print("\n🔎 Database Status Check:")

        if "base_data" in tables:
            with engine.connect() as conn:
                row_count = conn.execute(text("SELECT COUNT(*) FROM base_data")).scalar()
                min_date = conn.execute(text("SELECT MIN(sales_date) FROM base_data")).scalar()
                max_date = conn.execute(text("SELECT MAX(sales_date) FROM base_data")).scalar()
            print(f"   ✅ base_data exists with {row_count:,} rows")
            print(f"      → sales_date range: {min_date} → {max_date}")
        else:
            print("   ⚠️ base_data does not exist")

        if "all_products" in tables:
            with engine.connect() as conn:
                row_count = conn.execute(text("SELECT COUNT(*) FROM all_products")).scalar()
            print(f"   ✅ all_products exists with {row_count:,} rows")
        else:
            print("   ⚠️ all_products does not exist")

    except Exception as e:
        print(f"❌ check_db_status failed: {e}")

def auto_cleaning(sales_path, product_path, engine):
    """
    PostgreSQL-safe auto-cleaning: loads sales/product files, aggregates, fills missing,
    deletes overlapping rows, and appends to PostgreSQL table base_data.
    """

    # --- Load base_data from DB (if exists) ---
    df_base = None
    try:
        df_base = pd.read_sql("SELECT * FROM base_data", engine)
        df_base["sales_date"] = pd.to_datetime(df_base["sales_date"], errors="coerce")
        df_base = df_base.copy()
    except Exception:
        pass  # first run

    # --- Helper to load CSV/Excel with fallback headers ---
    def load_excel_with_fallback(path, possible_headers=[0,1,2,3]):
        sku_candidates = ["รหัสสินค้า", "เลขอ้างอิง SKU (SKU Reference No.)", "Product_SKU"]
        for h in possible_headers:
            df = pd.read_csv(path, header=h).copy()
            df.columns = df.columns.str.strip()
            for candidate in sku_candidates:
                if candidate in df.columns:
                    df = df.rename(columns={candidate: "Product_SKU"}).copy()
                    return df, h
        raise ValueError("❌ Could not find SKU column (รหัสสินค้า or เลขอ้างอิง SKU)")

    # --- Load sales ---
    ext_new = os.path.splitext(sales_path)[1].lower()
    if ext_new == ".csv":
        df_new, used_header = load_excel_with_fallback(sales_path)
    else:
        df_new = pd.read_excel(sales_path).copy()
        sales_path = sales_path.replace(ext_new, ".csv")
        df_new.to_csv(sales_path, index=False, encoding="utf-8-sig")
        df_new, used_header = load_excel_with_fallback(sales_path)

    # --- Load products ---
    ext_products = os.path.splitext(product_path)[1].lower()
    if ext_products == ".csv":
        df_products, pro_header = load_excel_with_fallback(product_path)
    else:
        df_products = pd.read_excel(product_path).copy()
        product_path = product_path.replace(ext_products, ".csv")
        df_products.to_csv(product_path, index=False, encoding="utf-8-sig")
        df_products, pro_header = load_excel_with_fallback(product_path)

    # --- Clean and rename columns ---
    df_new = df_new.dropna(subset=["Product_SKU"]).copy()
    df_products = df_products.dropna(subset=["Product_SKU"]).copy()
    print(df_new.columns.to_list())
    df_new = df_new.rename(columns={
        "ชื่อสินค้า": "product_name",
        "เลขอ้างอิง SKU (SKU Reference No.)": "Product_SKU",
        "รหัสสินค้า": "Product_SKU",
        "วันที่ทำรายการ": "sales_date",
        "จำนวน": "Quantity",
        "ราคาตั้งต้น": "Original_price",
        "ราคาต่อหน่วย": "Original_price",
        "ราคาขายสุทธิ": "Net_sale_price",
        "ราคารวม": "Net_sale_price",
        "โค้ดส่วนลดชำระโดยผู้ขาย": "Discount_code_paid_by_seller_Baht",
        "ส่วนลดต่อหน่วย": "Discount_code_paid_by_seller_Baht",
        "วันที่ทำการสั่งซื้อ": "sales_date"
    }).copy()

    df_new["Product_SKU"] = df_new["Product_SKU"].astype(str).str.strip()
    df_new["sales_date"] = pd.to_datetime(
        df_new["sales_date"], dayfirst=True, errors="coerce"
    ).dt.to_period("M").dt.to_timestamp()
    df_new["sales_year"] = df_new["sales_date"].dt.year
    df_new["sales_month"] = df_new["sales_date"].dt.month

    if "sales_date" not in df_new.columns:
        # Try to find any date-like column
        date_candidates = [col for col in df_new.columns if any(keyword in col.lower() for keyword in ['date', 'วันที่', 'เวลา', 'time'])]
        if date_candidates:
            print(f"⚠️ 'sales_date' column not found. Using '{date_candidates[0]}' as sales_date")
            df_new = df_new.rename(columns={date_candidates[0]: "sales_date"}).copy()
        else:
            available_cols = df_new.columns.tolist()
            raise ValueError(f"❌ Could not find sales date column. Available columns: {available_cols}")

    # --- Aggregate sales ---
    summary = (
        df_new.groupby(["Product_SKU","sales_date","sales_year","sales_month"], as_index=False)
              .agg({"Quantity": "sum"})
              .rename(columns={"Quantity": "Total_quantity"})
              .copy()
    )

    # --- Clean and rename columns for products ---
    df_products.columns = df_products.columns.str.strip()
    df_products = df_products.rename(columns={
        "ชื่อสินค้า": "product_name",
        "Product_name": "product_name",
        "รหัสสินค้า": "Product_SKU",
        "เลขอ้างอิง SKU (SKU Reference No.)": "Product_SKU"
    }).copy()

    df_products["Product_SKU"] = df_products["Product_SKU"].astype(str).str.strip()

    # --- Merge with products list ---
    df_merged = pd.merge(
        df_products[["Product_SKU", "product_name"]],
        summary,
        on="Product_SKU",
        how="left"
    ).copy()
    df_merged["Total_quantity"] = df_merged["Total_quantity"].fillna(0)

    # --- Fill missing months ONLY within CSV range ---
    min_date, max_date = summary["sales_date"].min(), summary["sales_date"].max()
    all_months = pd.date_range(min_date, max_date, freq="MS")
    products = df_products[["Product_SKU", "product_name"]].drop_duplicates().copy()

    full_index = pd.MultiIndex.from_product(
        [products["Product_SKU"], all_months],
        names=["Product_SKU", "sales_date"]
    )

    # --- Ensure uniqueness before reindex ---
    df_merged = (
        df_merged.groupby(["Product_SKU", "sales_date"], as_index=False)
                 .agg({"product_name": "first", "Total_quantity": "sum"})
    )

    # --- Now safe to reindex ---
    df_merged = (
        df_merged.set_index(["Product_SKU", "sales_date"])
                 .reindex(full_index, fill_value=0)
                 .reset_index()
                 .copy()
    )


    # ✅ Re-attach product_name properly and collapse duplicates
    df_merged = pd.merge(
        df_merged,
        products,
        on="Product_SKU",
        how="left"
    ).copy()

    if "product_name_x" in df_merged.columns and "product_name_y" in df_merged.columns:
        df_merged["product_name"] = df_merged["product_name_y"].combine_first(df_merged["product_name_x"])
        df_merged = df_merged.drop(columns=["product_name_x", "product_name_y"])
    elif "product_name_y" in df_merged.columns:
        df_merged = df_merged.rename(columns={"product_name_y": "product_name"})
    elif "product_name_x" in df_merged.columns:
        df_merged = df_merged.rename(columns={"product_name_x": "product_name"})

    df_merged["sales_year"] = df_merged["sales_date"].dt.year
    df_merged["sales_month"] = df_merged["sales_date"].dt.month
    df_merged = df_merged.sort_values(["Product_SKU","sales_date"]).reset_index(drop=True).copy()

    # --- Combine with base_data ---
    if df_base is None or df_base.empty:
        df_merged.columns = [col.lower() for col in df_merged.columns]
        df_base = df_merged.copy()
    else:
        df_merged.columns = [col.lower() for col in df_merged.columns]
        df_base = pd.concat([df_base, df_merged], ignore_index=True).copy()
        if "product_name" not in df_base.columns:
            df_base["product_name"] = None
        df_base["sales_date"] = pd.to_datetime(df_base["sales_date"], errors="coerce")
        df_base = (
            df_base.groupby(["product_sku","sales_date","sales_year","sales_month"], as_index=False)
                   .agg({"total_quantity": "first", "product_name": "first"})
                   .copy()
        )

    # --- Save cleaned CSV ---
    #clean_csv_path = r"D:\test\clean_sales_data.csv"
    df_base.to_csv("clean_sales_data.csv", index=False, encoding="utf-8-sig")

    # --- Final schema enforcement ---
    df_base = df_base[[
        "product_sku","product_name","sales_date","sales_year","sales_month","total_quantity"
    ]].copy()

    df_base["sales_date"]     = pd.to_datetime(df_base["sales_date"], errors="coerce")
    df_base["total_quantity"] = pd.to_numeric(df_base["total_quantity"], errors="coerce").fillna(0).astype("int64")
    df_base["sales_year"]     = pd.to_numeric(df_base["sales_year"], errors="coerce").fillna(0).astype("int64")
    df_base["sales_month"]    = pd.to_numeric(df_base["sales_month"], errors="coerce").fillna(0).astype("int64")

    df_base.columns = [col.lower() for col in df_base.columns]

    dtype_mapping = {
        "total_quantity": Integer,
        "sales_year": Integer,
        "sales_month": Integer
    }

    # --- Delete overlapping rows ---
    if df_base.shape[0] > 0:
        min_date = df_base["sales_date"].min().strftime("%Y-%m-%d")
        max_date = df_base["sales_date"].max().strftime("%Y-%m-%d")
        skus_list = df_base["product_sku"].unique().tolist()
        batch_size = 1000
        n_batches = ceil(len(skus_list) / batch_size)

        with engine.begin() as conn:
            for i in range(n_batches):
                batch_skus = skus_list[i*batch_size : (i+1)*batch_size]
                skus_str = "','".join(batch_skus)
                delete_sql = text(f"""
                    DELETE FROM base_data
                    WHERE product_sku IN ('{skus_str}')
                      AND sales_date BETWEEN '{min_date}' AND '{max_date}'
                """)
                conn.execute(delete_sql)

    print(df_base.dtypes)  # ✅ check column types
    print(df_base.columns.to_list())
    # --- Remove garbage rows like 'Exported by' and 'Date Time'
    bad_values = ["Exported by", "Date Time"]
    #df_products = df_products[~df_products["Product_SKU"].isin(bad_values)].copy()
    df_base = df_base[~df_base["product_sku"].isin(bad_values)].copy()
    # --- Save cleaned CSV ---
    clean_csv_path = r"clean_sales_data.csv"
    df_base.to_csv(clean_csv_path, index=False, encoding="utf-8-sig")
    # ✅ Insert cleaned data into base_data
    df_base.to_sql("base_data", engine, if_exists="append", index=False)

    # --- Replace all_products table ---
    df_base.to_sql("base_data", engine, if_exists="replace", index=False)

    df_products.to_sql("all_products", engine, if_exists="replace", index=False)

    check_db_status(engine)
    return df_base
