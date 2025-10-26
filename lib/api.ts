import { createClient } from "./supabase/client"

// Helper function to get Supabase client
function getSupabaseClient() {
  return createClient()
}

// Note: Training and prediction functionality requires ML backend
// These functions now query existing forecasts from the database
export async function trainModel(salesFile: File, productFile?: File) {
  throw new Error(
    "Training requires ML backend. Please use your FastAPI backend or Supabase Edge Functions for training.",
  )
}

export async function predictSales(nForecast = 3) {
  console.log("[v0] Fetching existing forecasts for n_forecast:", nForecast)

  const supabase = getSupabaseClient()

  // Calculate the date range for forecasts
  const today = new Date()
  const futureDate = new Date()
  futureDate.setMonth(futureDate.getMonth() + nForecast)

  const { data, error } = await supabase
    .from("forecasts")
    .select("*")
    .gte("forecast_date", today.toISOString().split("T")[0])
    .lte("forecast_date", futureDate.toISOString().split("T")[0])
    .order("forecast_date", { ascending: true })

  if (error) {
    console.error("[v0] Error fetching forecasts:", error)
    throw new Error(error.message)
  }

  return {
    status: "success",
    forecast_rows: data?.length || 0,
    n_forecast: nForecast,
    forecast:
      data?.map((row) => ({
        product_sku: row.product_sku,
        forecast_date: row.forecast_date,
        predicted_sales: row.predicted_sales,
        current_sales: row.current_sales,
        current_date_col: row.current_date_col,
      })) || [],
  }
}

export async function getExistingForecasts() {
  console.log("[v0] Fetching all existing forecasts")

  const supabase = getSupabaseClient()

  const { data, error } = await supabase.from("forecasts").select("*").order("forecast_date", { ascending: true })

  if (error) {
    console.error("[v0] Error fetching forecasts:", error)
    throw new Error(error.message)
  }

  return {
    status: "success",
    forecast_rows: data?.length || 0,
    forecast:
      data?.map((row) => ({
        product_sku: row.product_sku,
        forecast_date: row.forecast_date,
        predicted_sales: row.predicted_sales,
        current_sales: row.current_sales,
        current_date_col: row.current_date_col,
      })) || [],
    message: data?.length ? "Forecasts loaded successfully" : "No forecasts available",
  }
}

export async function getHistoricalSales(baseSku: string) {
  const supabase = getSupabaseClient()

  const { data, error } = await supabase
    .from("base_data")
    .select("*")
    .eq("product_sku", baseSku)
    .order("sales_date", { ascending: true })

  if (error) {
    console.error("[v0] Error fetching historical sales:", error)
    throw new Error(error.message)
  }

  // Transform data for chart format
  const monthsMap = new Map<string, Map<string, number>>()

  data?.forEach((row) => {
    const monthKey = `${row.sales_year}-${String(row.sales_month).padStart(2, "0")}`
    if (!monthsMap.has(monthKey)) {
      monthsMap.set(monthKey, new Map())
    }
    const sizeKey = row.product_name || "default"
    const currentQty = monthsMap.get(monthKey)!.get(sizeKey) || 0
    monthsMap.get(monthKey)!.set(sizeKey, currentQty + (row.total_quantity || 0))
  })

  const months = Array.from(monthsMap.keys()).sort()
  const sizes = new Set<string>()
  monthsMap.forEach((sizeMap) => {
    sizeMap.forEach((_, size) => sizes.add(size))
  })

  const series = Array.from(sizes).map((size) => ({
    size,
    values: months.map((month) => monthsMap.get(month)?.get(size) || 0),
  }))

  return {
    chart: { months, series },
    table:
      data?.map((row) => ({
        date: row.sales_date,
        size: row.product_name || "",
        quantity: row.total_quantity || 0,
        income: 0, // Income calculation would need price data
      })) || [],
  }
}

export async function getPerformanceComparison(skuList: string[]) {
  const supabase = getSupabaseClient()

  const { data, error } = await supabase
    .from("base_data")
    .select("product_sku, product_name, total_quantity")
    .in("product_sku", skuList)

  if (error) {
    console.error("[v0] Error fetching performance comparison:", error)
    throw new Error(error.message)
  }

  // Aggregate by product
  const aggregated = new Map<string, number>()
  data?.forEach((row) => {
    const key = row.product_sku
    const current = aggregated.get(key) || 0
    aggregated.set(key, current + (row.total_quantity || 0))
  })

  return {
    scatter: Array.from(aggregated.entries()).map(([item, quantity]) => ({
      item,
      quantity,
    })),
  }
}

export async function getBestSellers(year: number, month: number, topN = 10) {
  const supabase = getSupabaseClient()

  const { data, error } = await supabase
    .from("base_data")
    .select("product_sku, product_name, total_quantity")
    .eq("sales_year", year)
    .eq("sales_month", month)
    .order("total_quantity", { ascending: false })
    .limit(topN)

  if (error) {
    console.error("[v0] Error fetching best sellers:", error)
    throw new Error(error.message)
  }

  return {
    table:
      data?.map((row) => ({
        base_sku: row.product_sku,
        best_size: row.product_name || "",
        quantity: row.total_quantity || 0,
      })) || [],
  }
}

export async function getNotifications() {
  console.log("[v0] ===== getNotifications() CALLED =====")

  try {
    const supabase = getSupabaseClient()

    const { data, error } = await supabase
      .from("stock_notifications")
      .select("*")
      .order("created_at", { ascending: false })

    if (error) {
      console.error("[v0] Error fetching notifications:", error)
      return []
    }

    console.log("[v0] getNotifications() result:", data)

    return (
      data?.map((row) => ({
        Product: row.Product,
        Stock: row.Stock,
        Last_Stock: row.Last_Stock,
        "Decrease_Rate(%)": row["Decrease_Rate(%)"],
        Weeks_To_Empty: row.Weeks_To_Empty,
        MinStock: row.MinStock,
        Buffer: row.Buffer,
        Reorder_Qty: row.Reorder_Qty,
        Status: row.Status,
        Description: row.Description,
      })) || []
    )
  } catch (error) {
    console.error("[v0] getNotifications() error:", error)
    return []
  }
}

export async function getNotificationDetail(productName: string) {
  const supabase = getSupabaseClient()

  const { data, error } = await supabase.from("stock_notifications").select("*").eq("Product", productName).single()

  if (error) {
    console.error("[v0] Error fetching notification detail:", error)
    throw new Error(error.message)
  }

  return {
    Product: data.Product,
    Stock: data.Stock,
    Last_Stock: data.Last_Stock,
    "Decrease_Rate(%)": data["Decrease_Rate(%)"],
    Weeks_To_Empty: data.Weeks_To_Empty,
    MinStock: data.MinStock,
    Buffer: data.Buffer,
    Reorder_Qty: data.Reorder_Qty,
    Status: data.Status,
    Description: data.Description,
  }
}

export async function getDashboardAnalytics() {
  try {
    const supabase = getSupabaseClient()

    // Get total stock items
    const { count: totalStockItems } = await supabase.from("base_stock").select("*", { count: "exact", head: true })

    // Get low stock alerts (status = 'warning' or 'critical')
    const { count: lowStockAlerts } = await supabase
      .from("stock_notifications")
      .select("*", { count: "exact", head: true })
      .in("Status", ["warning", "critical"])

    // Get sales this month
    const currentDate = new Date()
    const currentYear = currentDate.getFullYear()
    const currentMonth = currentDate.getMonth() + 1

    const { data: salesData } = await supabase
      .from("base_data")
      .select("total_quantity")
      .eq("sales_year", currentYear)
      .eq("sales_month", currentMonth)

    const salesThisMonth = salesData?.reduce((sum, row) => sum + (row.total_quantity || 0), 0) || 0

    // Get out of stock items (stock_level = 0)
    const { count: outOfStock } = await supabase
      .from("base_stock")
      .select("*", { count: "exact", head: true })
      .eq("stock_level", 0)

    return {
      success: true,
      data: {
        total_stock_items: totalStockItems || 0,
        low_stock_alerts: lowStockAlerts || 0,
        sales_this_month: salesThisMonth,
        out_of_stock: outOfStock || 0,
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

export async function getStockLevels(params?: {
  search?: string
  category?: string
  flag?: string
  sort_by?: string
}) {
  try {
    const supabase = getSupabaseClient()

    let query = supabase.from("base_stock").select("*", { count: "exact" })

    if (params?.search) {
      query = query.or(`product_name.ilike.%${params.search}%,product_sku.ilike.%${params.search}%`)
    }

    if (params?.category) {
      query = query.eq("หมวดหมู่", params.category)
    }

    if (params?.flag) {
      query = query.eq("flag", params.flag)
    }

    if (params?.sort_by) {
      const [field, direction] = params.sort_by.split(":")
      query = query.order(field, { ascending: direction === "asc" })
    } else {
      query = query.order("created_at", { ascending: false })
    }

    const { data, error, count } = await query

    if (error) {
      console.error("[v0] Error fetching stock levels:", error)
      return { success: false, data: [], total: 0 }
    }

    return {
      success: true,
      data:
        data?.map((row) => ({
          product_name: row.product_name,
          product_sku: row.product_sku,
          stock_level: row.stock_level,
          category: row.หมวดหมู่ || "",
          flag: row.flag || "",
          unchanged_counter: row.unchanged_counter || 0,
        })) || [],
      total: count || 0,
    }
  } catch (error) {
    console.error("[v0] Failed to fetch stock levels:", error)
    return { success: false, data: [], total: 0 }
  }
}

export async function getStockCategories() {
  try {
    const supabase = getSupabaseClient()

    const { data, error } = await supabase.from("base_stock").select("หมวดหมู่")

    if (error) {
      console.error("[v0] Error fetching categories:", error)
      return { success: false, data: [] }
    }

    const categories = [...new Set(data?.map((row) => row.หมวดหมู่).filter(Boolean))]

    return { success: true, data: categories }
  } catch (error) {
    console.error("[v0] Failed to fetch stock categories:", error)
    return { success: false, data: [] }
  }
}

export async function getAnalysisHistoricalSales(sku: string) {
  try {
    const supabase = getSupabaseClient()

    const { data, error } = await supabase
      .from("base_data")
      .select("*")
      .eq("product_sku", sku)
      .order("sales_date", { ascending: true })

    if (error) {
      console.error("[v0] Error fetching historical sales:", error)
      return { success: false, message: "Failed to fetch data", chart_data: [], table_data: [], sizes: [] }
    }

    const sizes = [...new Set(data?.map((row) => row.product_name).filter(Boolean))]

    return {
      success: true,
      message: "Data fetched successfully",
      chart_data: data || [],
      table_data: data || [],
      sizes,
    }
  } catch (error) {
    console.error("[v0] Failed to fetch historical sales:", error)
    return { success: false, message: "Failed to fetch data", chart_data: [], table_data: [], sizes: [] }
  }
}

export async function getAnalysisPerformance(skuList: string[]) {
  try {
    const supabase = getSupabaseClient()

    const { data, error } = await supabase
      .from("base_data")
      .select("product_sku, product_name, total_quantity, sales_month")
      .in("product_sku", skuList)

    if (error) {
      console.error("[v0] Error fetching performance:", error)
      return { success: false, message: "Failed to fetch data", table_data: [], chart_data: {} }
    }

    // Aggregate by product
    const tableMap = new Map<string, { Item: string; Product_name: string; Quantity: number }>()
    const chartMap = new Map<string, Array<{ month: number; value: number }>>()

    data?.forEach((row) => {
      const sku = row.product_sku

      // Table data
      if (!tableMap.has(sku)) {
        tableMap.set(sku, {
          Item: sku,
          Product_name: row.product_name || "",
          Quantity: 0,
        })
      }
      tableMap.get(sku)!.Quantity += row.total_quantity || 0

      // Chart data
      if (!chartMap.has(sku)) {
        chartMap.set(sku, [])
      }
      chartMap.get(sku)!.push({
        month: row.sales_month,
        value: row.total_quantity || 0,
      })
    })

    return {
      success: true,
      message: "Data fetched successfully",
      table_data: Array.from(tableMap.values()),
      chart_data: Object.fromEntries(chartMap),
    }
  } catch (error) {
    console.error("[v0] Failed to fetch performance comparison:", error)
    return { success: false, message: "Failed to fetch data", table_data: [], chart_data: {} }
  }
}

export async function getAnalysisBestSellers(year: number, month: number, topN = 10) {
  try {
    const supabase = getSupabaseClient()

    const { data, error } = await supabase
      .from("base_data")
      .select("product_sku, product_name, total_quantity")
      .eq("sales_year", year)
      .eq("sales_month", month)
      .order("total_quantity", { ascending: false })
      .limit(topN)

    if (error) {
      console.error("[v0] Error fetching best sellers:", error)
      return { success: false, message: "Failed to fetch data", data: [] }
    }

    return {
      success: true,
      message: "Data fetched successfully",
      data:
        data?.map((row, index) => ({
          rank: index + 1,
          base_sku: row.product_sku,
          name: row.product_name || "",
          size: "",
          quantity: row.total_quantity || 0,
        })) || [],
    }
  } catch (error) {
    console.error("[v0] Failed to fetch best sellers:", error)
    return { success: false, message: "Failed to fetch data", data: [] }
  }
}

export async function getAnalysisTotalIncome(product_sku = "", category = "") {
  try {
    const supabase = getSupabaseClient()

    let query = supabase.from("base_data").select("*")

    if (product_sku) {
      query = query.eq("product_sku", product_sku)
    }

    if (category) {
      query = query.eq("category", category)
    }

    const { data, error } = await query

    if (error) {
      console.error("[v0] Error fetching total income:", error)
      return { success: false, message: "Failed to fetch data", table_data: [], chart_data: [], grand_total: 0 }
    }

    // Aggregate data
    const productMap = new Map<string, { total_quantity: number; months: Set<number> }>()
    const monthMap = new Map<string, number>()

    data?.forEach((row) => {
      const sku = row.product_sku
      if (!productMap.has(sku)) {
        productMap.set(sku, { total_quantity: 0, months: new Set() })
      }
      const product = productMap.get(sku)!
      product.total_quantity += row.total_quantity || 0
      product.months.add(row.sales_month)

      const monthKey = `${row.sales_year}-${String(row.sales_month).padStart(2, "0")}`
      monthMap.set(monthKey, (monthMap.get(monthKey) || 0) + (row.total_quantity || 0))
    })

    return {
      success: true,
      table_data: Array.from(productMap.entries()).map(([sku, data]) => ({
        Product_name: "",
        Product_sku: sku,
        Avg_Monthly_Revenue_Baht: 0, // Would need price data
        Total_Quantity: data.total_quantity,
      })),
      chart_data: Array.from(monthMap.entries()).map(([month, total_income]) => ({
        month,
        total_income,
      })),
      grand_total: Array.from(productMap.values()).reduce((sum, p) => sum + p.total_quantity, 0),
    }
  } catch (error) {
    console.error("[v0] Failed to fetch total income:", error)
    return { success: false, message: "Failed to fetch data", table_data: [], chart_data: [], grand_total: 0 }
  }
}

export async function checkBackendHealth() {
  // Supabase connection check
  try {
    const supabase = getSupabaseClient()
    const { error } = await supabase.from("base_stock").select("id").limit(1)

    if (error) {
      return {
        connected: false,
        error: error.message,
        url: process.env.NEXT_PUBLIC_SUPABASE_URL,
      }
    }

    return {
      connected: true,
      data: { status: "Supabase connected" },
      url: process.env.NEXT_PUBLIC_SUPABASE_URL,
    }
  } catch (error) {
    console.error("[v0] Supabase health check failed:", error)
    return {
      connected: false,
      error: error instanceof Error ? error.message : "Unknown error",
      url: process.env.NEXT_PUBLIC_SUPABASE_URL,
    }
  }
}

export async function clearForecasts() {
  try {
    const supabase = getSupabaseClient()

    const { error } = await supabase.from("forecasts").delete().neq("id", 0)

    if (error) {
      console.error("[v0] Error clearing forecasts:", error)
      throw new Error(error.message)
    }

    return {
      success: true,
      message: "Forecasts cleared successfully",
    }
  } catch (error) {
    console.error("[v0] Failed to clear forecasts:", error)
    throw error
  }
}

export async function getAnalysisBaseSKUs(search = "") {
  try {
    const supabase = getSupabaseClient()

    let query = supabase.from("base_data").select("product_sku", { count: "exact" })

    if (search) {
      query = query.ilike("product_sku", `%${search}%`)
    }

    const { data, error, count } = await query

    if (error) {
      console.error("[v0] Error fetching base SKUs:", error)
      return { success: false, base_skus: [], total: 0 }
    }

    const uniqueSKUs = [...new Set(data?.map((row) => row.product_sku))]

    return {
      success: true,
      base_skus: uniqueSKUs,
      total: count || 0,
    }
  } catch (error) {
    console.error("[v0] Failed to fetch base SKUs:", error)
    return { success: false, base_skus: [], total: 0 }
  }
}

export async function getAnalysisPerformanceProducts(search = "") {
  try {
    const supabase = getSupabaseClient()

    let query = supabase.from("all_products").select("*")

    if (search) {
      query = query.or(`product_name.ilike.%${search}%,product_sku.ilike.%${search}%`)
    }

    const { data, error } = await query

    if (error) {
      console.error("[v0] Error fetching performance products:", error)
      return { success: false, categories: {}, all_products: [] }
    }

    // Group by category
    const categories: Record<string, Array<{ product_sku: string; product_name: string }>> = {}

    data?.forEach((row) => {
      const category = row.category || "Uncategorized"
      if (!categories[category]) {
        categories[category] = []
      }
      categories[category].push({
        product_sku: row.product_sku,
        product_name: row.product_name || "",
      })
    })

    return {
      success: true,
      categories,
      all_products:
        data?.map((row) => ({
          product_sku: row.product_sku,
          product_name: row.product_name || "",
          category: row.category || "",
        })) || [],
    }
  } catch (error) {
    console.error("[v0] Failed to fetch performance products:", error)
    return { success: false, categories: {}, all_products: [] }
  }
}

export async function checkBaseStock() {
  try {
    const supabase = getSupabaseClient()

    const { count, error } = await supabase.from("base_stock").select("*", { count: "exact", head: true })

    if (error) {
      console.error("[v0] Error checking base_stock:", error)
      return { exists: false, has_data: false }
    }

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

export async function getSearchSuggestions(search: string) {
  try {
    const supabase = getSupabaseClient()

    const { data, error } = await supabase
      .from("all_products")
      .select("product_sku, product_name, category")
      .or(`product_name.ilike.%${search}%,product_sku.ilike.%${search}%`)
      .limit(10)

    if (error) {
      console.error("[v0] Error fetching search suggestions:", error)
      return { success: false, suggestions: [] }
    }

    return {
      success: true,
      suggestions:
        data?.map((row) => ({
          value: row.product_sku,
          type: "product",
          label: `${row.product_name} (${row.product_sku})`,
        })) || [],
    }
  } catch (error) {
    console.error("[v0] Failed to fetch search suggestions:", error)
    return { success: false, suggestions: [] }
  }
}
