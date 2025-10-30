import { getSupabaseClient } from "./supabase/client"

const supabase = getSupabaseClient()

// Stock Management Functions
export async function getStockLevels(params?: {
  search?: string
  category?: string
  flag?: string
  sort_by?: string
}) {
  try {
    let query = supabase
      .from("base_stock")
      .select("product_name, product_sku, stock_level, หมวดหมู่, flag, unchanged_counter")

    // Apply filters
    if (params?.search) {
      query = query.or(`product_name.ilike.%${params.search}%,product_sku.ilike.%${params.search}%`)
    }
    if (params?.category) {
      query = query.eq("หมวดหมู่", params.category)
    }
    if (params?.flag) {
      query = query.eq("flag", params.flag)
    }

    // Apply sorting
    if (params?.sort_by === "quantity_asc") {
      query = query.order("stock_level", { ascending: true })
    } else if (params?.sort_by === "quantity_desc") {
      query = query.order("stock_level", { ascending: false })
    } else {
      query = query.order("product_name", { ascending: true })
    }

    const { data, error } = await query

    if (error) throw error

    return {
      success: true,
      data: data.map((item) => ({
        product_name: item.product_name,
        product_sku: item.product_sku,
        stock_level: item.stock_level,
        quantity: item.stock_level,
        category: item.หมวดหมู่,
        flag: item.flag,
        status: item.flag,
        unchanged_counter: item.unchanged_counter,
      })),
      total: data.length,
    }
  } catch (error) {
    console.error("[v0] Failed to fetch stock levels:", error)
    return { success: false, data: [], total: 0 }
  }
}

export async function getStockCategories() {
  try {
    const { data, error } = await supabase.from("base_stock").select("หมวดหมู่").not("หมวดหมู่", "is", null)

    if (error) throw error

    // Get unique categories
    const categories = [...new Set(data.map((item) => item.หมวดหมู่))]

    return {
      success: true,
      data: categories.filter(Boolean),
    }
  } catch (error) {
    console.error("[v0] Failed to fetch categories:", error)
    return { success: false, data: [] }
  }
}

// Notifications Functions
export async function getNotifications() {
  try {
    const { data, error } = await supabase
      .from("stock_notifications")
      .select("*")
      .order("created_at", { ascending: false })

    if (error) throw error

    return data.map((item) => ({
      Product: item.Product,
      Stock: item.Stock,
      Last_Stock: item.Last_Stock,
      "Decrease_Rate(%)": item["Decrease_Rate(%)"],
      Weeks_To_Empty: item.Weeks_To_Empty,
      MinStock: item.MinStock,
      Buffer: item.Buffer,
      Reorder_Qty: item.Reorder_Qty,
      Status: item.Status,
      Description: item.Description,
    }))
  } catch (error) {
    console.error("[v0] Failed to fetch notifications:", error)
    return []
  }
}

export async function checkBaseStock() {
  try {
    const { count, error } = await supabase.from("base_stock").select("*", { count: "exact", head: true })

    if (error) throw error

    return {
      exists: true,
      has_data: (count || 0) > 0,
      row_count: count || 0,
    }
  } catch (error) {
    console.error("[v0] Failed to check base_stock:", error)
    return { exists: false, has_data: false }
  }
}

// Dashboard Analytics
export async function getDashboardAnalytics() {
  try {
    // Get total stock items
    const { count: totalItems } = await supabase.from("base_stock").select("*", { count: "exact", head: true })

    // Get low stock alerts (where stock_level < MinStock from notifications)
    const { data: lowStockData } = await supabase.from("stock_notifications").select("*").eq("Status", "low_stock")

    // Get out of stock items
    const { data: outOfStockData } = await supabase.from("base_stock").select("*").eq("stock_level", 0)

    // Get sales this month from base_data
    const currentDate = new Date()
    const currentYear = currentDate.getFullYear()
    const currentMonth = currentDate.getMonth() + 1

    const { data: salesData } = await supabase
      .from("base_data")
      .select("total_quantity")
      .eq("sales_year", currentYear)
      .eq("sales_month", currentMonth)

    const salesThisMonth = salesData?.reduce((sum, item) => sum + (item.total_quantity || 0), 0) || 0

    return {
      success: true,
      data: {
        total_stock_items: totalItems || 0,
        low_stock_alerts: lowStockData?.length || 0,
        sales_this_month: salesThisMonth * 100, // Assuming 100 baht per unit
        out_of_stock: outOfStockData?.length || 0,
      },
    }
  } catch (error) {
    console.error("[v0] Failed to fetch dashboard analytics:", error)
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

// Analysis Functions
export async function getAnalysisHistoricalSales(sku: string) {
  try {
    const { data, error } = await supabase
      .from("base_data")
      .select("*")
      .ilike("product_sku", `%${sku}%`)
      .order("sales_date", { ascending: true })

    if (error) throw error

    // Group by month and size
    const chartData: any[] = []
    const tableData: any[] = []
    const sizes = new Set<string>()

    data.forEach((item) => {
      const month = `${item.sales_year}-${String(item.sales_month).padStart(2, "0")}`
      sizes.add(item.product_sku)

      chartData.push({
        month,
        size: item.product_sku,
        quantity: item.total_quantity,
      })

      tableData.push({
        date: item.sales_date,
        size: item.product_sku,
        quantity: item.total_quantity,
        income: item.total_quantity * 100, // Assuming 100 baht per unit
      })
    })

    return {
      success: true,
      message: "Data fetched successfully",
      chart_data: chartData,
      table_data: tableData,
      sizes: Array.from(sizes),
    }
  } catch (error) {
    console.error("[v0] Failed to fetch historical sales:", error)
    return { success: false, message: "Failed to fetch data", chart_data: [], table_data: [], sizes: [] }
  }
}

export async function getAnalysisBestSellers(year: number, month: number, topN = 10) {
  try {
    const { data, error } = await supabase
      .from("base_data")
      .select("product_sku, product_name, total_quantity")
      .eq("sales_year", year)
      .eq("sales_month", month)
      .order("total_quantity", { ascending: false })
      .limit(topN)

    if (error) throw error

    return {
      success: true,
      message: "Data fetched successfully",
      data: data.map((item, index) => ({
        rank: index + 1,
        base_sku: item.product_sku,
        name: item.product_name,
        size: item.product_sku,
        quantity: item.total_quantity,
      })),
    }
  } catch (error) {
    console.error("[v0] Failed to fetch best sellers:", error)
    return { success: false, message: "Failed to fetch data", data: [] }
  }
}

export async function getAnalysisTotalIncome(product_sku = "", category = "") {
  try {
    let query = supabase.from("base_data").select("product_sku, product_name, total_quantity, sales_year, sales_month")

    if (product_sku) {
      query = query.ilike("product_sku", `%${product_sku}%`)
    }
    if (category) {
      query = query.eq("category", category)
    }

    const { data, error } = await query

    if (error) throw error

    // Group by product
    const productMap = new Map()
    const monthlyIncome = new Map()

    data.forEach((item) => {
      const key = item.product_sku
      if (!productMap.has(key)) {
        productMap.set(key, {
          Product_name: item.product_name,
          Product_sku: item.product_sku,
          Total_Quantity: 0,
          Avg_Monthly_Revenue_Baht: 0,
        })
      }
      const product = productMap.get(key)
      product.Total_Quantity += item.total_quantity

      const monthKey = `${item.sales_year}-${String(item.sales_month).padStart(2, "0")}`
      if (!monthlyIncome.has(monthKey)) {
        monthlyIncome.set(monthKey, 0)
      }
      monthlyIncome.set(monthKey, monthlyIncome.get(monthKey) + item.total_quantity * 100)
    })

    // Calculate average monthly revenue
    productMap.forEach((product) => {
      product.Avg_Monthly_Revenue_Baht = (product.Total_Quantity * 100) / Math.max(monthlyIncome.size, 1)
    })

    const tableData = Array.from(productMap.values())
    const chartData = Array.from(monthlyIncome.entries()).map(([month, total_income]) => ({
      month,
      total_income,
    }))

    const grandTotal = tableData.reduce((sum, item) => sum + item.Total_Quantity * 100, 0)

    return {
      success: true,
      message: "Data fetched successfully",
      table_data: tableData,
      chart_data: chartData,
      grand_total: grandTotal,
    }
  } catch (error) {
    console.error("[v0] Failed to fetch total income:", error)
    return { success: false, message: "Failed to fetch data", table_data: [], chart_data: [], grand_total: 0 }
  }
}

export async function getAnalysisBaseSKUs(search = "") {
  try {
    let query = supabase.from("base_stock").select("product_sku")

    if (search) {
      query = query.ilike("product_sku", `%${search}%`)
    }

    const { data, error } = await query

    if (error) throw error

    const uniqueSKUs = [...new Set(data.map((item) => item.product_sku))]

    return {
      success: true,
      base_skus: uniqueSKUs,
      total: uniqueSKUs.length,
    }
  } catch (error) {
    console.error("[v0] Failed to fetch base SKUs:", error)
    return { success: false, base_skus: [], total: 0 }
  }
}

export async function getAnalysisPerformanceProducts(search = "") {
  try {
    let query = supabase.from("all_products").select("product_sku, product_name, category")

    if (search) {
      query = query.or(`product_name.ilike.%${search}%,product_sku.ilike.%${search}%`)
    }

    const { data, error } = await query

    if (error) throw error

    // Group by category
    const categories: Record<string, Array<{ product_sku: string; product_name: string }>> = {}

    data.forEach((item) => {
      const cat = item.category || "Uncategorized"
      if (!categories[cat]) {
        categories[cat] = []
      }
      categories[cat].push({
        product_sku: item.product_sku,
        product_name: item.product_name,
      })
    })

    return {
      success: true,
      categories,
      all_products: data.map((item) => ({
        product_sku: item.product_sku,
        product_name: item.product_name,
        category: item.category || "Uncategorized",
      })),
    }
  } catch (error) {
    console.error("[v0] Failed to fetch performance products:", error)
    return { success: false, categories: {}, all_products: [] }
  }
}

export async function getAnalysisPerformance(skuList: string[]) {
  try {
    const { data, error } = await supabase
      .from("base_data")
      .select("product_sku, product_name, total_quantity, sales_month")
      .in("product_sku", skuList)

    if (error) throw error

    // Group by SKU for table
    const tableMap = new Map()
    const chartData: Record<string, Array<{ month: number; value: number }>> = {}

    data.forEach((item) => {
      // Table data
      if (!tableMap.has(item.product_sku)) {
        tableMap.set(item.product_sku, {
          Item: item.product_sku,
          Product_name: item.product_name,
          Quantity: 0,
        })
      }
      const tableItem = tableMap.get(item.product_sku)
      tableItem.Quantity += item.total_quantity

      // Chart data
      if (!chartData[item.product_sku]) {
        chartData[item.product_sku] = []
      }
      chartData[item.product_sku].push({
        month: item.sales_month,
        value: item.total_quantity,
      })
    })

    return {
      success: true,
      message: "Data fetched successfully",
      table_data: Array.from(tableMap.values()),
      chart_data: chartData,
    }
  } catch (error) {
    console.error("[v0] Failed to fetch performance comparison:", error)
    return { success: false, message: "Failed to fetch data", table_data: [], chart_data: {} }
  }
}

export async function getSearchSuggestions(search: string) {
  try {
    const { data, error } = await supabase
      .from("all_products")
      .select("product_sku, product_name, category")
      .or(`product_name.ilike.%${search}%,product_sku.ilike.%${search}%,category.ilike.%${search}%`)
      .limit(10)

    if (error) throw error

    const suggestions = data.map((item) => ({
      value: item.product_sku,
      type: "product",
      label: `${item.product_name} (${item.product_sku})`,
    }))

    return {
      success: true,
      suggestions,
    }
  } catch (error) {
    console.error("[v0] Failed to fetch search suggestions:", error)
    return { success: false, suggestions: [] }
  }
}

// Prediction Functions - Keep using backend for ML operations
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function predictSales(nForecast = 3) {
  try {
    const response = await fetch(`${API_BASE_URL}/predict?n_forecast=${nForecast}`, {
      method: "POST",
    })

    if (!response.ok) {
      throw new Error(`Prediction failed: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error("[v0] Prediction failed:", error)
    throw error
  }
}

export async function getExistingForecasts() {
  try {
    const { data, error } = await supabase.from("forecasts").select("*").order("forecast_date", { ascending: true })

    if (error) throw error

    return {
      status: "success",
      forecast_rows: data.length,
      forecast: data.map((item) => ({
        product_sku: item.product_sku,
        forecast_date: item.forecast_date,
        predicted_sales: item.predicted_sales,
        current_sales: item.current_sales,
        current_date_col: item.current_date_col,
      })),
      message: "Forecasts loaded from database",
    }
  } catch (error) {
    console.error("[v0] Failed to fetch forecasts:", error)
    return {
      status: "error",
      forecast_rows: 0,
      forecast: [],
      message: "No forecasts available",
    }
  }
}

export async function clearForecasts() {
  try {
    const { error } = await supabase.from("forecasts").delete().neq("id", 0) // Delete all rows

    if (error) throw error

    return {
      success: true,
      message: "Forecasts cleared successfully",
    }
  } catch (error) {
    console.error("[v0] Failed to clear forecasts:", error)
    throw error
  }
}

export async function trainModel(salesFile: File, productFile?: File) {
  // Keep using backend for ML training
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
