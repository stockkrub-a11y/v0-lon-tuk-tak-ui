"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Search, Home, Package, TrendingUp, BookOpen, Bell, Filter, X, Clock } from "lucide-react"
import { predictSales, getExistingForecasts, clearForecasts } from "@/lib/api"

interface ForecastData {
  sku: string
  forecastDate: string
  forecastDateRaw: Date
  predictedSales: string
  currentSale: string
  currentDate: string
}

export default function PredictPage() {
  const [isPredictModalOpen, setIsPredictModalOpen] = useState(false)
  const [selectedTimeRange, setSelectedTimeRange] = useState("1 Month")
  const [customMonths, setCustomMonths] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [forecastData, setForecastData] = useState<ForecastData[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)

  const timeRangeOptions = ["1 Month", "2 Month", "3 Month", "4 Month", "5 Month", "6 Month", "1 Year", "Option"]

  const loadExistingForecasts = async () => {
    try {
      console.log("[v0] Loading existing forecasts...")
      setIsLoading(true)

      const data = await getExistingForecasts()
      console.log("[v0] Forecast data received:", data)

      if (data.forecast && data.forecast.length > 0) {
        const mapped: ForecastData[] = data.forecast.map((item) => {
          const forecastDate = new Date(item.forecast_date)
          return {
            sku: item.product_sku,
            forecastDate: forecastDate.toLocaleDateString("en-US", { month: "short", year: "2-digit" }),
            forecastDateRaw: forecastDate,
            predictedSales: Math.round(item.predicted_sales).toString(),
            currentSale: Math.round(item.current_sales).toString(),
            currentDate: new Date(item.current_date_col).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
            }),
          }
        })

        mapped.sort((a, b) => {
          const skuCompare = a.sku.localeCompare(b.sku)
          if (skuCompare !== 0) return skuCompare
          return a.forecastDateRaw.getTime() - b.forecastDateRaw.getTime()
        })

        setForecastData(mapped)
        console.log("[v0] Loaded", mapped.length, "forecast records")
      } else {
        console.log("[v0] No forecast data available")
        setForecastData([])
      }
    } catch (error) {
      console.error("[v0] Error loading forecasts:", error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadExistingForecasts()
  }, [])

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible" && !isGenerating) {
        console.log("[v0] Page became visible, reloading forecasts...")
        loadExistingForecasts()
      }
    }

    document.addEventListener("visibilitychange", handleVisibilityChange)
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange)
  }, [isGenerating])

  const handlePredict = async () => {
    const months =
      selectedTimeRange === "Option"
        ? Number.parseInt(customMonths) || 1
        : selectedTimeRange === "1 Year"
          ? 12
          : Number.parseInt(selectedTimeRange.split(" ")[0])

    setIsPredictModalOpen(false)
    setIsGenerating(true)
    setIsLoading(true)
    setForecastData([])

    console.log("[v0] Starting prediction for", months, "months")

    predictSales(months)
      .then((response) => {
        console.log("[v0] Prediction completed:", response)
        const mapped: ForecastData[] = response.forecast.map((item) => {
          const forecastDate = new Date(item.forecast_date)
          return {
            sku: item.product_sku,
            forecastDate: forecastDate.toLocaleDateString("en-US", { month: "short", year: "2-digit" }),
            forecastDateRaw: forecastDate,
            predictedSales: Math.round(item.predicted_sales).toString(),
            currentSale: Math.round(item.current_sales).toString(),
            currentDate: new Date(item.current_date_col).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
            }),
          }
        })

        mapped.sort((a, b) => {
          const skuCompare = a.sku.localeCompare(b.sku)
          if (skuCompare !== 0) return skuCompare
          return a.forecastDateRaw.getTime() - b.forecastDateRaw.getTime()
        })

        setForecastData(mapped)
      })
      .catch((error) => {
        console.error("[v0] Prediction failed:", error)
        alert(
          `Prediction failed: ${error instanceof Error ? error.message : "Unknown error"}. Make sure the backend server is running for ML predictions.`,
        )
      })
      .finally(() => {
        setIsLoading(false)
        setIsGenerating(false)
      })
  }

  const handleReset = () => {
    setSelectedTimeRange("1 Month")
    setCustomMonths("")
  }

  const handleClearForecasts = async () => {
    if (confirm("Are you sure you want to clear all forecast data? This will delete forecasts from the database.")) {
      try {
        await clearForecasts()
        setForecastData([])
        alert("Forecast data cleared successfully")
      } catch (error) {
        console.error("[v0] Error clearing forecasts:", error)
        alert("Failed to clear forecast data.")
      }
    }
  }

  const handleExportExcel = () => {
    const headers = ["Product SKU", "Forecast Date", "Predicted Sales", "Current Sale", "Current Date"]
    const csvData = forecastData.map((row) => [
      row.sku,
      row.forecastDate,
      row.predictedSales,
      row.currentSale,
      row.currentDate,
    ])

    const csvContent = [headers.join(","), ...csvData.map((row) => row.join(","))].join("\n")

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
    const link = document.createElement("a")
    const url = URL.createObjectURL(blob)
    link.setAttribute("href", url)
    link.setAttribute("download", `sales_forecast_${new Date().toISOString().split("T")[0]}.csv`)
    link.style.visibility = "hidden"
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const filteredData = forecastData.filter((item) => item.sku.toLowerCase().includes(searchQuery.toLowerCase()))

  return (
    <div className="min-h-screen bg-[#f8f5ee]">
      {/* Header */}
      <header className="bg-white border-b border-[#efece3] px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-serif text-black">Lon TukTak</h1>
            <p className="text-xs text-[#938d7a]">Stock Management</p>
          </div>

          <div className="flex-1 max-w-xl mx-8">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#938d7a]" />
              <input
                type="text"
                placeholder="Search for stocks & more"
                className="w-full pl-10 pr-4 py-2 bg-[#f8f5ee] rounded-lg border-none outline-none text-sm text-black placeholder:text-[#938d7a] focus:ring-2 focus:ring-[#938d7a]/20"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#ffd700] rounded flex items-center justify-center font-bold text-black text-sm">
              TG
            </div>
            <div>
              <p className="text-sm font-medium text-black">Toogleton</p>
              <p className="text-xs text-[#938d7a]">Toogletons@gmail.com</p>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar Navigation */}
        <aside className="w-52 bg-[#efece3] min-h-[calc(100vh-73px)] p-4">
          <p className="text-xs text-[#938d7a] mb-4 px-3">Navigation</p>
          <nav className="space-y-1">
            <Link
              href="/dashboard"
              className="flex items-center gap-3 px-3 py-2.5 text-[#1e1e1e] hover:bg-white/50 rounded-lg transition-colors"
            >
              <Home className="w-5 h-5" />
              <span>Home</span>
            </Link>
            <Link
              href="/dashboard/stocks"
              className="flex items-center gap-3 px-3 py-2.5 text-[#1e1e1e] hover:bg-white/50 rounded-lg transition-colors"
            >
              <Package className="w-5 h-5" />
              <span>Stocks</span>
            </Link>
            <Link
              href="/dashboard/predict"
              className="flex items-center gap-3 px-3 py-2.5 bg-white rounded-lg text-black font-medium"
            >
              <TrendingUp className="w-5 h-5" />
              <span>Predict</span>
            </Link>
            <Link
              href="/dashboard/analysis"
              className="flex items-center gap-3 px-3 py-2.5 text-[#1e1e1e] hover:bg-white/50 rounded-lg transition-colors"
            >
              <BookOpen className="w-5 h-5" />
              <span>Analysis</span>
            </Link>
            <Link
              href="/dashboard/notifications"
              className="flex items-center gap-3 px-3 py-2.5 text-[#1e1e1e] hover:bg-white/50 rounded-lg transition-colors"
            >
              <Bell className="w-5 h-5" />
              <span>Notifications</span>
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-black mb-2">Predict Sales</h2>
            <p className="text-[#938d7a]">Monitor your sales forecast</p>
          </div>

          {/* Sales Forecast Section */}
          <div className="bg-white rounded-lg p-6 border border-[#cecabf]/30 mb-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-black">Sales Forecast</h3>
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#938d7a]" />
                  <input
                    type="text"
                    placeholder="Search products..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 bg-[#f8f5ee] rounded-lg border-none outline-none text-sm text-black placeholder:text-[#938d7a] focus:ring-2 focus:ring-[#938d7a]/20"
                  />
                </div>
                <button
                  onClick={() => setIsPredictModalOpen(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-[#efece3] hover:bg-[#cecabf] rounded-lg transition-colors"
                >
                  <Filter className="w-4 h-4 text-black" />
                  <span className="text-sm font-medium text-black">Predict System</span>
                </button>
              </div>
            </div>

            {/* Forecast Table */}
            <div className="overflow-x-auto">
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="text-[#938d7a] mb-2">
                    {isGenerating ? "Generating predictions... This may take up to 2 minutes." : "Loading forecasts..."}
                  </div>
                  <div className="text-sm text-[#938d7a]">You can navigate to other pages while waiting.</div>
                </div>
              ) : forecastData.length === 0 ? (
                <div className="text-center py-12">
                  <TrendingUp className="w-16 h-16 text-[#cecabf] mx-auto mb-4" />
                  <h4 className="text-lg font-semibold text-black mb-2">No Forecast Data Available</h4>
                  <p className="text-[#938d7a] mb-6 max-w-md mx-auto">
                    To generate sales predictions, you need to train the ML model first by uploading your product and
                    sales data files.
                  </p>

                  <div className="bg-[#f8f5ee] rounded-lg p-6 max-w-2xl mx-auto mb-6 text-left">
                    <h5 className="font-semibold text-black mb-3">How to get started:</h5>
                    <ol className="space-y-2 text-sm text-[#1e1e1e]">
                      <li className="flex items-start gap-2">
                        <span className="font-bold text-black">1.</span>
                        <span>
                          Go to the <strong>Stocks</strong> page
                        </span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="font-bold text-black">2.</span>
                        <span>
                          Click <strong>"Upload Product List"</strong> and select your product file (Excel/CSV)
                        </span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="font-bold text-black">3.</span>
                        <span>
                          Click <strong>"Upload Sale Stock"</strong> and select your sales file (Excel/CSV)
                        </span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="font-bold text-black">4.</span>
                        <span>The model will train automatically and redirect you back here</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="font-bold text-black">5.</span>
                        <span>
                          Click <strong>"Predict System"</strong> to generate forecasts
                        </span>
                      </li>
                    </ol>
                  </div>

                  <div className="flex items-center justify-center gap-3">
                    <Link
                      href="/dashboard/stocks"
                      className="px-6 py-3 bg-[#cecabf] hover:bg-[#b4bbcb] rounded-lg transition-colors text-black font-medium"
                    >
                      Go to Stocks Page
                    </Link>
                    <button
                      onClick={loadExistingForecasts}
                      className="px-6 py-3 bg-[#efece3] hover:bg-[#cecabf] rounded-lg transition-colors text-black font-medium"
                    >
                      Refresh
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                      <Clock className="w-5 h-5 text-black" />
                      <h4 className="text-lg font-semibold text-black">
                        Forecast Results ({forecastData.length} records)
                      </h4>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleExportExcel}
                        className="px-4 py-2 bg-[#4ade80] hover:bg-[#22c55e] rounded-lg transition-colors text-sm font-medium text-white"
                      >
                        Export to Excel
                      </button>
                      <button
                        onClick={handleClearForecasts}
                        className="px-4 py-2 bg-[#ef4444] hover:bg-[#dc2626] rounded-lg transition-colors text-sm font-medium text-white"
                      >
                        Clear Forecasts
                      </button>
                      <button
                        onClick={loadExistingForecasts}
                        className="px-3 py-1.5 bg-[#efece3] hover:bg-[#cecabf] rounded-lg transition-colors text-sm font-medium text-black"
                      >
                        Refresh
                      </button>
                    </div>
                  </div>
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-[#cecabf]/30">
                        <th className="text-left py-4 px-4 text-sm font-semibold text-[#1e1e1e]">Product SKU</th>
                        <th className="text-left py-4 px-4 text-sm font-semibold text-[#1e1e1e]">Forecast Date</th>
                        <th className="text-left py-4 px-4 text-sm font-semibold text-[#1e1e1e]">Predicted Sales</th>
                        <th className="text-left py-4 px-4 text-sm font-semibold text-[#1e1e1e]">Current Sale</th>
                        <th className="text-left py-4 px-4 text-sm font-semibold text-[#1e1e1e]">Current Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredData.map((row, index) => (
                        <tr key={index} className="border-b border-[#cecabf]/10 hover:bg-[#f8f5ee]/50">
                          <td className="py-4 px-4 text-black font-medium">{row.sku}</td>
                          <td className="py-4 px-4 text-[#1e1e1e]">{row.forecastDate}</td>
                          <td className="py-4 px-4 text-black font-semibold">{row.predictedSales}</td>
                          <td className="py-4 px-4 text-black font-semibold">{row.currentSale}</td>
                          <td className="py-4 px-4 text-[#1e1e1e]">{row.currentDate}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Predict Function Modal */}
      {isPredictModalOpen && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-xl font-bold text-black">Predict Function</h3>
                <p className="text-sm text-[#938d7a]">Choose your parameter (requires backend server for ML)</p>
              </div>
              <button
                onClick={() => setIsPredictModalOpen(false)}
                className="text-[#938d7a] hover:text-black transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Time Range Selection */}
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-black mb-3">Time Range</h4>
              <div className="flex flex-wrap gap-2">
                {timeRangeOptions.map((option) => (
                  <button
                    key={option}
                    onClick={() => setSelectedTimeRange(option)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedTimeRange === option
                        ? "bg-[#cecabf] text-black"
                        : "bg-[#efece3] text-[#1e1e1e] hover:bg-[#cecabf]/50"
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>

              {/* Custom Month Input */}
              {selectedTimeRange === "Option" && (
                <div className="mt-4">
                  <label className="block text-sm font-medium text-black mb-2">Enter number of months:</label>
                  <input
                    type="number"
                    min="1"
                    max="24"
                    value={customMonths}
                    onChange={(e) => setCustomMonths(e.target.value)}
                    placeholder="Enter months (e.g., 8)"
                    className="w-full px-4 py-2 bg-[#f8f5ee] rounded-lg border border-[#cecabf] outline-none text-black placeholder:text-[#938d7a] focus:ring-2 focus:ring-[#938d7a]/20"
                  />
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3">
              <button
                onClick={handleReset}
                className="px-4 py-2 text-sm font-medium text-black hover:bg-[#efece3] rounded-lg transition-colors"
              >
                Reset
              </button>
              <button
                onClick={handleExportExcel}
                disabled={forecastData.length === 0}
                className="px-4 py-2 text-sm font-medium text-black hover:bg-[#efece3] rounded-lg transition-colors disabled:opacity-50"
              >
                Export Excel
              </button>
              <button
                onClick={handlePredict}
                className="flex-1 px-6 py-2 bg-[#cecabf] hover:bg-[#b4bbcb] text-black font-medium rounded-lg transition-colors"
              >
                Predict
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
