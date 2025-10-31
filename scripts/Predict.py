import pandas as pd
import numpy as np
import os
import joblib
import xgboost as xgb
from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
import optuna
import time
import copy
from xgboost.callback import EarlyStopping

# -----------------------------
# Parameters
# -----------------------------
ROLLING_WINDOW = 12        # Last 12 months of data
TEST_MONTHS = 6            # Last 6 months for validation
N_FORECAST = 1             # Forecast next n months
MODEL_FILE = "xgb_sales_model.pkl"

# -----------------------------
# Feature Engineering Functions
# -----------------------------
def create_lags(data, lags=[1, 12]):
    for lag in lags:
        data[f'Total_quantity_lag_{lag}'] = data.groupby('product_sku')['total_quantity'].shift(lag)
    return data

def create_rolling(data, windows=[3,6]):
    for window in windows:
        data[f'Total_quantity_roll_mean_{window}'] = data.groupby('product_sku')['total_quantity'].shift(1).rolling(window).mean()
    return data

# -----------------------------
# Hyperparameter Tuning
# -----------------------------
def tune_xgboost(X, y, n_trials=1):
    def objective(trial):
        params = {
            "objective": "reg:squarederror",
            "eval_metric": "mae",
            "n_estimators": trial.suggest_int("n_estimators", 1200, 4000),
            "max_depth": trial.suggest_int("max_depth", 6, 18),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
            "subsample": trial.suggest_float("subsample", 0.8, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.8, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 0.1),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.5, 2.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 4),
            "gamma": trial.suggest_float("gamma", 0.0, 0.5),
            "max_leaves": trial.suggest_int("max_leaves", 0, 512),
            "tree_method": "hist",
            "random_state": 42,
        }

        tscv = TimeSeriesSplit(n_splits=3)
        scores = []

        for train_idx, valid_idx in tscv.split(X):
            X_train, X_valid = X.iloc[train_idx], X.iloc[valid_idx]
            y_train, y_valid = y.iloc[train_idx], y.iloc[valid_idx]

            model = XGBRegressor(**params)
            model.fit(
                X_train, y_train,
                eval_set=[(X_valid, y_valid)],
                verbose=False
            )

            preds = model.predict(X_valid)
            scores.append(mean_absolute_error(y_valid, preds))

        return np.mean(scores)

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    print("✅ Best params:", study.best_params)
    print("✅ Best MAE:", study.best_value)

    return study.best_params


# -----------------------------
# Model Training
# -----------------------------
def update_model_and_train(df):
    start_time = time.time()
    print("Starting model update and training...")

    df = df.drop(columns=["product_name"])
    # Ensure dates are datetime
    if df['sales_date'].dtype == 'object':
        print("Converting sales_date to datetime...")
        df['sales_date'] = pd.to_datetime(df['sales_date'])
    
    latest_date = df['sales_date'].max()
    print(f"Latest date in data: {latest_date}")
    df_window = df[df['sales_date'] > latest_date - pd.DateOffset(months=ROLLING_WINDOW)].copy()
    df_window = df_window.dropna(subset=['product_sku'])

    product_sku_last = df_window[df_window['sales_date'] == df_window['sales_date'].max()]['product_sku'].values

    # Feature engineering
    df_window = create_lags(df_window)
    df_window = create_rolling(df_window)
    df_window.fillna(0, inplace=True)

    df_window_raw = df_window.copy()
    df_window_encoded = pd.get_dummies(df_window, columns=['product_sku'], drop_first=True)

    train = df_window_encoded[df_window_encoded['sales_date'] < df_window_encoded['sales_date'].max() - pd.DateOffset(months=TEST_MONTHS)]
    test = df_window_encoded[df_window_encoded['sales_date'] >= df_window_encoded['sales_date'].max() - pd.DateOffset(months=TEST_MONTHS)]

    X_train = train.drop(['total_quantity','sales_year','sales_month','sales_date'], axis=1)
    y_train = train['total_quantity']
    X_test = test.drop(['total_quantity','sales_year','sales_month','sales_date'], axis=1)
    y_test = test['total_quantity']

    # Load or tune model
    if os.path.exists(MODEL_FILE):
        print("Loading existing model...")
        base_model = joblib.load(MODEL_FILE)
    else:
        print("Tuning XGBoost model with Optuna...")
        best_params = tune_xgboost(X_train, y_train, n_trials=1)

        base_model = XGBRegressor(
            **best_params,
            objective="reg:squarederror",
            eval_metric="mae",
            tree_method="hist",
            random_state=42
        )

        base_model.fit(X_train, y_train, verbose=10)
        joblib.dump(base_model, MODEL_FILE)
        print(f"✅ Model saved to {MODEL_FILE}")

    # Validation
    y_pred = base_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    print("Validation MAE:", mae)

    print(f"Process completed in {time.time() - start_time:.2f} seconds.")
    return df_window_raw, df_window, base_model, X_train, y_train, X_test, y_test, product_sku_last

# -----------------------------
# Forecasting
# -----------------------------
def forcast_loop(X_train, y_train, df_window_raw, product_sku_last, base_model, n_forecast=N_FORECAST, retrain_each_step=True):
    start_time = time.time()
    print("Starting forecasting loop...")

    # Ensure dates are datetime
    if df_window_raw['sales_date'].dtype == 'object':
        df_window_raw['sales_date'] = pd.to_datetime(df_window_raw['sales_date'])

    future = df_window_raw[df_window_raw['sales_date'] == df_window_raw['sales_date'].max()].copy()
    future['product_sku'] = product_sku_last
    long_forecast_rows = []
    current_model = copy.deepcopy(base_model)

    for i in range(n_forecast):
        future['sales_date'] = future['sales_date'] + pd.DateOffset(months=1)
        forecast_date = future['sales_date'].iloc[0]
        future['sales_year'] = future['sales_date'].dt.year
        future['sales_month'] = future['sales_date'].dt.month
        future['Total_quantity_lag_1'] = future['total_quantity']

        future['Total_quantity_lag_12'] = future.groupby('product_sku')['total_quantity'].shift(12).fillna(0)
        future['Total_quantity_roll_mean_3'] = future.groupby('product_sku')['total_quantity'].shift(1).rolling(3).mean().fillna(0)

        X_future = future.drop(['total_quantity','sales_year','sales_month','product_sku'], axis=1)
        X_future = pd.get_dummies(X_future)
        for col in X_train.columns:
            if col not in X_future.columns:
                X_future[col] = 0
        X_future = X_future[X_train.columns]

        y_pred_future = current_model.predict(X_future)
        y_pred_future = np.maximum(np.round(y_pred_future).astype(int), 0)
        future['total_quantity'] = y_pred_future

        for sku, pred in zip(product_sku_last, y_pred_future):
            # get last known actuals for this SKU
            last_row = df_window_raw[df_window_raw['product_sku'] == sku].sort_values('sales_date').iloc[-1]
            current_sales = int(last_row['total_quantity'])
            current_date_col = last_row['sales_date']

            long_forecast_rows.append({
                "product_sku": sku,
                "forecast_date": forecast_date,
                "predicted_sales": int(pred),
                "current_sales": current_sales,
                "current_date_col": current_date_col
            })

        print(f"✅ {i+1} month prediction ({forecast_date.date()}): {y_pred_future}")

        if retrain_each_step:
            X_train = pd.concat([X_train, X_future], axis=0)
            y_train = pd.concat([y_train, pd.Series(y_pred_future)], axis=0)
            current_model.fit(X_train, y_train, xgb_model=current_model.get_booster())

    long_forecast = pd.DataFrame(long_forecast_rows)
    long_forecast.sort_values(['product_sku','forecast_date'], inplace=True)
    end_time = time.time()
    long_forecast.to_csv('forecast_output.csv', index=False)
    print(f"Forecasting completed in {end_time - start_time:.2f} seconds")
    return long_forecast, long_forecast_rows

# -----------------------------
# Evaluation
# -----------------------------
def Evaluate(X_train, y_train, X_test, y_test, model_file=MODEL_FILE):
    model = joblib.load(model_file)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    print(f"MAE: {mae}\nMAPE: {mape}\nRMSE: {rmse}\nR2: {r2}")

import matplotlib.pyplot as plt

# -----------------------------
# Plot Validation Results
# -----------------------------
def plot_validation(X_test, y_test, model_file=MODEL_FILE):
    # Load model and predict
    model = joblib.load(model_file)
    y_pred_test = model.predict(X_test)

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(y_test.values, label='Actual', marker='o')
    plt.plot(y_pred_test, label='Predicted', marker='x')
    plt.title("Actual vs Predicted total_quantity (Validation)")
    plt.xlabel("Index")
    plt.ylabel("total_quantity")
    plt.legend()
    plt.grid(True)
    plt.show()
