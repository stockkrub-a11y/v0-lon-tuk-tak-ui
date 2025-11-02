import { getSupabaseClient } from "./supabase/client"

// This ensures the client is created after environment variables are loaded

// Stock Management Functions
export async function getStockLevels(params?: {
  search?: string
  category?: string
  flag?: string
  sort_by?: string
}) {
  try {
    const supabase = getSupabaseClient()

    console.log("[v0] Fetching stock levels with params:", params)

    let query = supabase
      .from("base_stock")
      .select("product_name, product_sku, stock_level, category, flag, unchanged_counter")

    // Apply filters
    if (params?.search) {
      query = query.or(`product_name.ilike.%${params.search}%,product_sku.ilike.%${params.search}%`)
    }
    if (params?.category) {
      query = query.eq("category", params.category)
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

    if (error) {
      console.error("[v0] Supabase error:", error.message, error)
      return { success: false, data: [], total: 0, error: error.message }
    }

    console.log("[v0] Successfully fetched", data?.length || 0, "stock items")

    return {
      success: true,
      data: data.map((item) => ({
        product_name: item.product_name,
        product_sku: item.product_sku,
        stock_level: item.stock_level,
        quantity: item.stock_level,
        category: item.category,
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
    const supabase = getSupabaseClient()

    console.log("[v0] Fetching stock categories")

    const { data, error } = await supabase.from("base_stock").select("category").not("category", "is", null)

    if (error) {
      console.error("[v0] Supabase error:", error.message, error)
      return { success: false, data: [], error: error.message }
    }

    // Get unique categories
    const categories = [...new Set(data.map((item) => item.category))]

    console.log("[v0] Successfully fetched", categories.length, "categories")

    return {
      success: true,
      data: categories.filter(Boolean),
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error"
    console.error("[v0] Failed to fetch categories:", message)
    return { success: false, data: [], error: message }
  }
}

// Notifications Functions
export async function getNotifications() {
  try {
    const supabase = getSupabaseClient()

    console.log("[v0] Fetching notifications")

    const { data, error } = await supabase
      .from("stock_notifications")
      .select("*")
      .order("created_at", { ascending: false })

    if (error) {
      console.error("[v0] Supabase error:", error)
      throw error
    }

    console.log("[v0] Successfully fetched", data?.length || 0, "notifications")

    // Normalize and return a predictable shape for the frontend. The DB
    // schema sometimes uses mixed-case or localized column names, so map
    // common variants to stable keys.
    return data.map((item: any) => {
      console.log("[v0] Raw notification item:", item)

      const normalizedItem = {
        Product: item.product ?? item.Product ?? item.product_name ?? item.Product_name ?? "",
        Product_SKU: item.product_sku ?? item.Product_SKU ?? item.ProductSKU ?? item.ProductSku ?? "",
        Category: item.category ?? item.Category ?? item["หมวดหมู่"] ?? "",
        Stock: Number(item.stock ?? item.Stock ?? item.stock_level ?? 0) || 0,
        Last_Stock: Number(item.last_stock ?? item.Last_Stock ?? 0) || 0,
        "Decrease_Rate(%)": Number(item.decrease_rate ?? item["Decrease_Rate(%)"] ?? 0) || 0,
        Weeks_To_Empty: Number(item.weeks_to_empty ?? item.Weeks_To_Empty ?? 0) || 0,
        MinStock: Number(item.minstock ?? item.MinStock ?? item.minStock ?? 0) || 0,
        Buffer: Number(item.buffer ?? item.Buffer ?? 0) || 0,
        Reorder_Qty: Number(item.reorder_qty ?? item.Reorder_Qty ?? 0) || 0,
        Status: item.status ?? item.Status ?? "Green",
        Description: item.description ?? item.Description ?? "Stock is sufficient",
        // keep original raw item for debugging
        _raw: item,
      }
      return normalizedItem
    })
  } catch (error) {
    console.error("[v0] Failed to fetch notifications:", error)
    return []
  }
}

export async function checkBaseStock() {
  try {
    const supabase = getSupabaseClient()

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
    const supabase = getSupabaseClient()

    console.log("[v0] Fetching dashboard analytics")

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

    console.log("[v0] Dashboard analytics:", {
      totalItems,
      lowStockAlerts: lowStockData?.length,
      outOfStock: outOfStockData?.length,
      salesThisMonth,
    })

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
    const supabase = getSupabaseClient()
    // First, try to find historical sales by SKU or product name in `base_data`.
    // This handles requests like a SKU lookup which should return sales over time.
    const { data: salesData, error: salesError } = await supabase
      .from("base_data")
      .select("*")
      .or(`product_sku.ilike.%${sku}%,product_name.ilike.%${sku}%`)
      .order("sales_date", { ascending: true })

    if (salesError) {
      console.error("[v0] Supabase error fetching base_data:", salesError)
      throw salesError
    }

    const chartData: any[] = []
    const tableData: any[] = []
    const sizes = new Set<string>()

    if (Array.isArray(salesData) && salesData.length > 0) {
      // Treat as SKU (historical sales) search
      salesData.forEach((item) => {
        const monthNum = Number(item.sales_month) || 0
        sizes.add(item.product_sku)

        chartData.push({
          month: monthNum,
          size: item.product_sku,
          quantity: item.total_quantity,
        })

        tableData.push({
          product_sku: item.product_sku,
          product_name: item.product_name,
          total_quantity: item.total_quantity,
          date: item.sales_date,
          income: item.total_quantity * 100,
        })
      })

      console.log(`[v0] getAnalysisHistoricalSales: SKU search for "${sku}" -> rows=${salesData.length}`)

      return {
        success: true,
        message: "Data fetched successfully",
        chart_data: chartData,
        table_data: tableData,
        sizes: Array.from(sizes),
        search_type: "sku",
      }
    }

    // If no sales records, try treating the query as a category/product search
    // and return the current stock snapshot from `base_stock`.
    const { data: stockData, error: stockError } = await supabase
      .from("base_stock")
      .select("product_sku, product_name, stock_level, flag, category")
      .or(`product_name.ilike.%${sku}%,category.ilike.%${sku}%,product_sku.ilike.%${sku}%`)
      .order("product_name", { ascending: true })

    if (stockError) {
      console.error("[v0] Supabase error fetching base_stock:", stockError)
      throw stockError
    }

    if (Array.isArray(stockData) && stockData.length > 0) {
      stockData.forEach((item: any, index: number) => {
        chartData.push({
          product_sku: item.product_sku,
          product_name: item.product_name,
          stock_level: Number(item.stock_level) || 0,
          flag: item.flag,
          category: item.category || "",
          index,
        })

        tableData.push({
          product_sku: item.product_sku,
          product_name: item.product_name,
          stock_level: Number(item.stock_level) || 0,
          flag: item.flag,
          category: item.category || "",
        })
      })

      console.log(`[v0] getAnalysisHistoricalSales: Category/product search for "${sku}" -> rows=${stockData.length}`)

      return {
        success: true,
        message: "Data fetched successfully",
        chart_data: chartData,
        table_data: tableData,
        sizes: [],
        search_type: "category",
      }
    }

    // No data found in either table
    return { success: true, message: "No data found", chart_data: [], table_data: [], sizes: [], search_type: "sku" }
  } catch (error) {
    console.error("[v0] Failed to fetch historical sales:", error)
    return { success: false, message: "Failed to fetch data", chart_data: [], table_data: [], sizes: [] }
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
    const supabase = getSupabaseClient()

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
    const supabase = getSupabaseClient()
    // Fetch SKUs from both base_stock (current snapshot) and base_data (historical sales)
    const skus = new Set<string>()

    try {
      const { data: stockData, error: stockError } = await supabase.from("base_stock").select("product_sku")

      if (stockError) {
        console.warn("[v0] Warning fetching SKUs from base_stock:", stockError)
      } else if (Array.isArray(stockData)) {
        stockData.forEach((r: any) => {
          if (r && r.product_sku) skus.add(String(r.product_sku).trim())
        })
      }
    } catch (e) {
      console.warn("[v0] Exception fetching base_stock SKUs:", e)
    }

    try {
      let dataQuery = supabase.from("base_data").select("product_sku")
      if (search) dataQuery = dataQuery.ilike("product_sku", `%${search}%`)
      const { data: baseData, error: baseError } = await dataQuery
      if (baseError) {
        console.warn("[v0] Warning fetching SKUs from base_data:", baseError)
      } else if (Array.isArray(baseData)) {
        baseData.forEach((r: any) => {
          if (r && r.product_sku) skus.add(String(r.product_sku).trim())
        })
      }
    } catch (e) {
      console.warn("[v0] Exception fetching base_data SKUs:", e)
    }

    // If a search term was provided, filter the results client-side as well
    const results = Array.from(skus).filter((s) => (search ? s.toLowerCase().includes(search.toLowerCase()) : true))

    return {
      success: true,
      base_skus: results,
      total: results.length,
    }
  } catch (error) {
    console.error("[v0] Failed to fetch base SKUs:", error)
    return { success: false, base_skus: [], total: 0 }
  }
}

export async function getAnalysisPerformanceProducts(search = "") {
  try {
    const supabase = getSupabaseClient()

    let query = supabase.from("all_products").select("product_sku, product_name, category")

    if (search) {
      query = query.or(`product_name.ilike.%${search}%,product_sku.ilike.%${search}%`)
    }

    const { data, error } = await query

    if (error) throw error
    // If all_products exists but contains no rows, fallback to base_stock
    if (!Array.isArray(data) || data.length === 0) {
      console.warn("[v0] all_products returned no rows, falling back to base_stock")
      // reuse the fallback path below
      const { data: baseData, error: baseError } = await supabase
        .from("base_stock")
        .select("product_sku, product_name, category")

      if (baseError) throw baseError

      const categories: Record<string, Array<{ product_sku: string; product_name: string }>> = {}
      const products = (baseData || []).map((item: any) => ({
        product_sku: item.product_sku,
        product_name: item.product_name,
        category: item.category || "Uncategorized",
      }))

      products.forEach((p) => {
        const cat = p.category || "Uncategorized"
        categories[cat] = categories[cat] || []
        categories[cat].push({ product_sku: p.product_sku, product_name: p.product_name })
      })

      return { success: true, categories, all_products: products }
    }

    // Group by category for all_products
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
    console.error("[v0] Failed to fetch performance products from all_products, trying base_stock fallback:", error)
    // Fallback: try reading from base_stock if all_products view/table doesn't exist
    try {
      const supabase = getSupabaseClient()
      const { data: baseData, error: baseError } = await supabase
        .from("base_stock")
        .select("product_sku, product_name, category")

      if (baseError) throw baseError

      const categories: Record<string, Array<{ product_sku: string; product_name: string }>> = {}
      const products = (baseData || []).map((item: any) => ({
        product_sku: item.product_sku,
        product_name: item.product_name,
        category: item.category || "Uncategorized",
      }))

      products.forEach((p) => {
        const cat = p.category || "Uncategorized"
        categories[cat] = categories[cat] || []
        categories[cat].push({ product_sku: p.product_sku, product_name: p.product_name })
      })

      return { success: true, categories, all_products: products }
    } catch (fallbackError) {
      console.error("[v0] Fallback to base_stock failed:", fallbackError)
      return { success: false, categories: {}, all_products: [] }
    }
  }
}

export async function getAnalysisPerformance(skuList: string[]) {
  try {
    const supabase = getSupabaseClient()

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
    const supabase = getSupabaseClient()

    const { data, error } = await supabase
      .from("all_products")
      .select("product_sku, product_name, category")
      .or(`product_name.ilike.%${search}%,product_sku.ilike.%${search}%,category.ilike.%${search}%`)
      .limit(10)

    if (error) throw error

    // If no results from all_products, try base_stock as a fallback
    let sourceData = data
    if ((!Array.isArray(data) || data.length === 0) && search) {
      try {
        const { data: baseData, error: baseErr } = await supabase
          .from("base_stock")
          .select("product_sku, product_name, category")
          .or(`product_name.ilike.%${search}%,product_sku.ilike.%${search}%,category.ilike.%${search}%`)
          .limit(10)

        if (!baseErr && Array.isArray(baseData) && baseData.length > 0) {
          sourceData = baseData
        }
      } catch (e) {
        // ignore and continue with empty suggestions
      }
    }

    const suggestions = (sourceData || []).map((item) => ({
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

console.log("[v0] API_BASE_URL configured as:", API_BASE_URL)
console.log("[v0] NEXT_PUBLIC_API_URL env var:", process.env.NEXT_PUBLIC_API_URL)

export async function predictSales(nForecast = 3) {
  try {
    const url = `${API_BASE_URL}/predict?n_forecast=${nForecast}`
    console.log("[v0] Calling prediction endpoint:", url)

    const response = await fetch(url, {
      method: "POST",
    })

    if (!response.ok) {
      throw new Error(`Prediction failed: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error("[v0] Prediction failed:", error)
    console.error("[v0] Error details:", {
      message: error instanceof Error ? error.message : String(error),
      apiBaseUrl: API_BASE_URL,
      envVar: process.env.NEXT_PUBLIC_API_URL,
    })
    throw error
  }
}

export async function getExistingForecasts() {
  try {
    const supabase = getSupabaseClient()

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
    const supabase = getSupabaseClient()

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
  const healthCheck = await checkBackendHealth()

  if (!healthCheck.connected) {
    // Backend not available - just upload files to Supabase without ML training
    console.log("[v0] Backend not available, uploading files to Supabase only")

    try {
      const supabase = getSupabaseClient()

      // Parse and upload sales file
      const salesData = await parseExcelFile(salesFile)
      if (salesData.length > 0) {
        const { error: salesError } = await supabase
          .from("base_data")
          .upsert(salesData, { onConflict: "product_sku,sales_date" })

        if (salesError) throw salesError
      }

      // Parse and upload product file if provided
      if (productFile) {
        const productData = await parseExcelFile(productFile)
        if (productData.length > 0) {
          // Insert into base_stock table
          const { error: productError } = await supabase
            .from("base_stock")
            .upsert(productData, { onConflict: "product_sku" })

          if (productError) throw productError

          // Also insert into all_products table
          const allProductsData = productData.map((item) => ({
            product_sku: item.product_sku,
            product_name: item.product_name,
            category: item.category,
            quantity: item.stock_level,
          }))

          const { error: allProductsError } = await supabase
            .from("all_products")
            .upsert(allProductsData, { onConflict: "product_sku" })

          if (allProductsError) throw allProductsError
        }
      }

      return {
        data_cleaning: {
          status: "completed",
          rows_uploaded: salesData.length,
          message: "Files uploaded successfully to database",
        },
        ml_training: {
          status: "skipped",
          message: "ML training skipped - backend not available. Start the Python backend to enable forecasting.",
          forecast_rows: 0,
        },
      }
    } catch (error) {
      console.error("[v0] Failed to upload files:", error)
      throw new Error("Failed to upload files to database")
    }
  }

  // Backend is available - use ML training
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
    let errMsg = `Upload failed: ${response.status}`
    try {
      const json = await response.json()
      errMsg = json.detail || json.message || errMsg
    } catch (e) {
      // ignore
    }
    throw new Error(errMsg)
  }

  return await response.json()
}

/**
 * Upload previous/current stock files to backend notifications endpoint.
 * previousFile: optional (for first-time upload), currentFile: required
 */
export async function uploadStockFiles(previousFile?: File | null, currentFile?: File | null) {
  const API_BASE_URL_LOCAL = process.env.NEXT_PUBLIC_API_URL || API_BASE_URL

  if (!currentFile) {
    throw new Error("Current stock file is required")
  }

  const formData = new FormData()
  // Backend expects fields: previous_stock (optional), current_stock (required)
  if (previousFile) formData.append("previous_stock", previousFile)
  formData.append("current_stock", currentFile)

  const response = await fetch(`${API_BASE_URL_LOCAL}/notifications/upload`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    let errMsg = `Upload failed: ${response.status}`
    try {
      const json = await response.json()
      errMsg = json.detail || json.message || errMsg
    } catch (e) {
      // ignore
    }
    throw new Error(errMsg)
  }

  return await response.json()
}

// Helper function to parse Excel files
async function parseExcelFile(file: File): Promise<any[]> {
  // This is a placeholder - you'll need to implement actual Excel parsing
  // For now, return empty array
  console.log("[v0] Excel parsing not implemented yet for:", file.name)
  return []
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

/**
 * Update manual MinStock/Buffer values directly in Supabase for stock_notifications.
 * This is used when the Python backend is not available (Supabase-only mode).
 */
export async function updateNotificationManualValues(
  product_sku: string,
  minstock?: number | null,
  buffer?: number | null,
) {
  try {
    const supabase = getSupabaseClient()

    // Fetch current notification row
    const { data: rows, error: fetchErr } = await supabase
      .from("stock_notifications")
      .select("*")
      .eq("product_sku", product_sku)
      .limit(1)

    if (fetchErr) throw fetchErr
    const row = Array.isArray(rows) && rows.length > 0 ? rows[0] : null
    if (!row) {
      return { success: false, message: "Product not found in stock_notifications" }
    }

    // Normalize numeric fields
    const stock = Number(row.Stock ?? row.stock_level ?? row.currentStock ?? 0) || 0
    const last_stock = Number(row.Last_Stock ?? row.last_stock ?? 0) || 0

    const weekly_sale = Math.max(last_stock - stock, 1)
    const decrease_rate = last_stock > 0 ? ((last_stock - stock) / last_stock) * 100 : 0

    // Determine new minstock and buffer using same rules as backend
    const new_minstock = typeof minstock === "number" ? minstock : Math.floor(weekly_sale * 2 * 1.5)

    let new_buffer: number
    if (typeof buffer === "number") {
      new_buffer = buffer
    } else {
      if (decrease_rate > 50) new_buffer = 20
      else if (decrease_rate > 20) new_buffer = 10
      else new_buffer = 5
      new_buffer = Math.min(new_buffer, 50)
    }

    const default_reorder = Math.max(Math.floor(weekly_sale * 1.5), 1)
    const new_reorder_qty = Math.max(new_minstock + new_buffer - stock, default_reorder)

    // Determine status and description
    const is_red = stock < new_minstock || decrease_rate > 50
    const is_yellow = !is_red && decrease_rate > 20

    let new_status = "Green"
    let new_description = "Stock is sufficient"
    if (is_red) {
      new_status = "Red"
      new_description = `Decreasing rapidly and nearly out of stock! Recommend restocking ${new_reorder_qty} units`
    } else if (is_yellow) {
      new_status = "Yellow"
      new_description = `Decreasing rapidly, should prepare to restock. Recommend restocking ${new_reorder_qty} units`
    }

    // Prepare update payload (normalize column names to lowercase where possible)
    const payload: any = {
      MinStock: new_minstock,
      Buffer: new_buffer,
      Reorder_Qty: new_reorder_qty,
      Status: new_status,
      Description: new_description,
      updated_at: new Date().toISOString(),
    }

    const { error: updateErr } = await supabase
      .from("stock_notifications")
      .update(payload)
      .eq("product_sku", product_sku)

    if (updateErr) throw updateErr

    return {
      success: true,
      product_sku,
      minstock: new_minstock,
      buffer: new_buffer,
      reorder_qty: new_reorder_qty,
      status: new_status,
      description: new_description,
    }
  } catch (error) {
    console.error("[v0] Failed to update manual notification values:", error)
    return { success: false, message: error instanceof Error ? error.message : String(error) }
  }
}
