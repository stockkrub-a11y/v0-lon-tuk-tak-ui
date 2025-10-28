// API configuration and utility functions for backend integration

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  console.log("[v0] API Request:", url)

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    })

    console.log("[v0] API Response status:", response.status)

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("[v0] API Error response:", error)
      throw new Error(error.detail || `API Error: ${response.status}`)
    }

    const data = await response.json()
    console.log("[v0] API Success:", data)
    return data
  } catch (error) {
    console.error(`[v0] API Fetch Error for ${endpoint}:`, error)
    if (error instanceof TypeError && error.message === "Failed to fetch") {
      throw new Error("Cannot connect to backend. Make sure the backend server is running on " + API_BASE_URL)
    }
    throw error
  }
}

export async function trainModel(salesFile: File, productFile?: File) {
  const formData = new FormData()
  formData.append("sales_file", salesFile)
  if (productFile) {
    formData.append("product_file", productFile)
  }

  const response = await fetch(`${API_BASE_URL}/train`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Training failed" }))
    throw new Error(error.detail || "Training failed")
  }

  return await response.json()
}

export async function predictSales(nForecast = 3) {
  console.log("[v0] Calling predict API with n_forecast:", nForecast)
  return apiFetch<{
    status: string
    forecast_rows: number
    n_forecast: number
    forecast: Array<{
      product_sku: string
      forecast_date: string
      predicted_sales: number
      current_sales: number
      current_date_col: string
    }>
  }>(`/predict?n_forecast=${nForecast}`, { method: "POST" })
}

export async function getExistingForecasts() {
  console.log("[v0] Fetching existing forecasts")
  return apiFetch<{
    status: string
    forecast_rows: number
    forecast: Array<{
      product_sku: string
      forecast_date: string
      predicted_sales: number
      current_sales: number
      current_date_col: string
    }>
    message: string
  }>("/predict/existing")
}

export async function getHistoricalSales(baseSku: string) {
  return apiFetch<{
    chart: {
      months: string[]
      series: Array<{ size: string; values: number[] }>
    }
    table: Array<{
      date: string
      size: string
      quantity: number
      income: number
    }>
  }>(`/historical?base_sku=${baseSku}`)
}

export async function getPerformanceComparison(skuList: string[]) {
  const params = skuList.map((sku) => `sku_list=${encodeURIComponent(sku)}`).join("&")
  return apiFetch<{
    scatter: Array<{
      item: string
      quantity: number
    }>
  }>(`/performance?${params}`)
}

export async function getBestSellers(year: number, month: number, topN = 10) {
  return apiFetch<{
    table: Array<{
      base_sku: string
      best_size: string
      quantity: number
    }>
  }>(`/best_sellers?year=${year}&month=${month}&top_n=${topN}`)
}

export async function getNotifications() {
  console.log("[v0] ===== getNotifications() CALLED =====")
  console.log("[v0] API_BASE_URL:", API_BASE_URL)

  try {
    const result =
      await apiFetch<
        Array<{
          Product: string
          Stock: number
          Last_Stock: number
          "Decrease_Rate(%)": number
          Weeks_To_Empty: number
          MinStock: number
          Buffer: number
          Reorder_Qty: number
          Status: string
          Description: string
        }>
      >("/notifications")

    console.log("[v0] getNotifications() result:", result)
    return result
  } catch (error) {
    console.error("[v0] getNotifications() error:", error)
    // Return empty array if backend is not available
    return []
  }
}

export async function getNotificationDetail(productName: string) {
  return apiFetch<{
    Product: string
    Stock: number
    Last_Stock: number
    "Decrease_Rate(%)": number
    Weeks_To_Empty: number
    MinStock: number
    Buffer: number
    Reorder_Qty: number
    Status: string
    Description: string
  }>(`/notifications/${encodeURIComponent(productName)}`)
}

export async function getDashboardAnalytics() {
  try {
    return await apiFetch<{
      success: boolean
      data: {
        total_stock_items: number
        low_stock_alerts: number
        sales_this_month: number
        out_of_stock: number
      }
    }>("/analysis/dashboard")
  } catch (error) {
    console.error("[v0] Failed to fetch dashboard analytics:", error)
    // Return mock data if backend is not available
    return {
      success: false,
      data: {
        total_stock_items: 0,
        low_stock_alerts: 0,
        sales_this_month: 0,
        out_of_stock: 0,
      },
    }
  }
}

export async function getStockLevels(params?: {
  search?: string
  category?: string
  flag?: string
  sort_by?: string
}) {
  try {
    const queryParams = new URLSearchParams()
    if (params?.search) queryParams.append("search", params.search)
    if (params?.category) queryParams.append("category", params.category)
    if (params?.flag) queryParams.append("flag", params.flag)
    if (params?.sort_by) queryParams.append("sort_by", params.sort_by)

    const url = `/stock/levels${queryParams.toString() ? `?${queryParams}` : ""}`

    return await apiFetch<{
      success: boolean
      data: Array<{
        product_name: string
        product_sku: string
        stock_level: number
        category: string
        flag: string
        unchanged_counter: number
      }>
      total: number
    }>(url)
  } catch (error) {
    console.error("[v0] Failed to fetch stock levels:", error)
    return { success: false, data: [], total: 0 }
  }
}

export async function getStockCategories() {
  try {
    return await apiFetch<{
      success: boolean
      data: string[]
    }>("/stock/categories")
  } catch (error) {
    console.error("[v0] Failed to fetch stock categories:", error)
    return { success: false, data: [] }
  }
}

export async function getAnalysisHistoricalSales(sku: string) {
  try {
    return await apiFetch<{
      success: boolean
      message: string
      chart_data: Array<Record<string, any>>
      table_data: Array<Record<string, any>>
      sizes: string[]
    }>(`/analysis/historical?sku=${encodeURIComponent(sku)}`)
  } catch (error) {
    console.error("[v0] Failed to fetch historical sales:", error)
    return { success: false, message: "Failed to fetch data", chart_data: [], table_data: [], sizes: [] }
  }
}

export async function getAnalysisPerformance(skuList: string[]) {
  try {
    return await apiFetch<{
      success: boolean
      message: string
      table_data: Array<{
        Item: string
        Product_name: string
        Quantity: number
      }>
      chart_data: Record<string, Array<{ month: number; value: number }>>
    }>("/analysis/performance", {
      method: "POST",
      body: JSON.stringify({ sku_list: skuList }),
    })
  } catch (error) {
    console.error("[v0] Failed to fetch performance comparison:", error)
    return { success: false, message: "Failed to fetch data", table_data: [], chart_data: {} }
  }
}

export async function getAnalysisBestSellers(year: number, month: number, topN = 10) {
  try {
    return await apiFetch<{
      success: boolean
      message: string
      data: Array<{
        rank: number
        base_sku: string
        name: string
        size: string
        quantity: number
      }>
    }>(`/analysis/best_sellers?year=${year}&month=${month}&top_n=${topN}`)
  } catch (error) {
    console.error("[v0] Failed to fetch best sellers:", error)
    return { success: false, message: "Failed to fetch data", data: [] }
  }
}

export async function getAnalysisTotalIncome(product_sku = "", category = "") {
  try {
    const params = new URLSearchParams()
    if (product_sku) params.append("product_sku", product_sku)
    if (category) params.append("category", category)

    const url = `/analysis/total_income${params.toString() ? `?${params}` : ""}`

    return await apiFetch<{
      success: boolean
      message?: string
      table_data: Array<{
        Product_name: string
        Product_sku: string
        Avg_Monthly_Revenue_Baht: number
        Total_Quantity: number
      }>
      chart_data: Array<{
        month: string
        total_income: number
      }>
      grand_total: number
    }>(url)
  } catch (error) {
    console.error("[v0] Failed to fetch total income:", error)
    return { success: false, message: "Failed to fetch data", table_data: [], chart_data: [], grand_total: 0 }
  }
}

export async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      return {
        connected: false,
        error: `Backend returned status ${response.status}`,
        url: API_BASE_URL,
      }
    }

    const data = await response.json()
    return {
      connected: true,
      data,
      url: API_BASE_URL,
    }
  } catch (error) {
    console.error("[v0] Backend health check failed:", error)
    return {
      connected: false,
      error: error instanceof Error ? error.message : "Unknown error",
      url: API_BASE_URL,
    }
  }
}

export async function clearForecasts() {
  try {
    return await apiFetch<{
      success: boolean
      message: string
    }>("/predict/clear", { method: "DELETE" })
  } catch (error) {
    console.error("[v0] Failed to clear forecasts:", error)
    throw error
  }
}

export async function getAnalysisBaseSKUs(search = "") {
  try {
    return await apiFetch<{
      success: boolean
      base_skus: string[]
      total: number
    }>(`/analysis/base_skus?search=${encodeURIComponent(search)}`)
  } catch (error) {
    console.error("[v0] Failed to fetch base SKUs:", error)
    return { success: false, base_skus: [], total: 0 }
  }
}

export async function getAnalysisPerformanceProducts(search = "") {
  try {
    return await apiFetch<{
      success: boolean
      categories: Record<string, Array<{ product_sku: string; product_name: string }>>
      all_products: Array<{ product_sku: string; product_name: string; category: string }>
    }>(`/analysis/performance-products?search=${encodeURIComponent(search)}`)
  } catch (error) {
    console.error("[v0] Failed to fetch performance products:", error)
    return { success: false, categories: {}, all_products: [] }
  }
}

export async function checkBaseStock() {
  try {
    return await apiFetch<{
      exists: boolean
      has_data: boolean
      row_count?: number
    }>("/notifications/check_base_stock")
  } catch (error) {
    console.error("[v0] Failed to check base_stock:", error)
    return { exists: false, has_data: false }
  }
}

export async function getSearchSuggestions(search: string) {
  try {
    return await apiFetch<{
      success: boolean
      suggestions: Array<{
        value: string
        type: string
        label: string
      }>
    }>(`/analysis/search-suggestions?search=${encodeURIComponent(search)}`)
  } catch (error) {
    console.error("[v0] Failed to fetch search suggestions:", error)
    return { success: false, suggestions: [] }
  }
}
