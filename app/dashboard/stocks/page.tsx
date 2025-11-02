"use client"

import type React from "react"

import { useState, useEffect, useCallback, useRef } from "react"
import Link from "next/link"
import {
  Search,
  Home,
  Package,
  TrendingUp,
  BookOpen,
  Bell,
  Upload,
  Filter,
  X,
  CloudUpload,
  CheckCircle2,
  Wifi,
  WifiOff,
  AlertCircle,
  ChevronDown,
} from "lucide-react"
import { trainModel, getStockLevels, getStockCategories } from "@/lib/api"

export default function StocksPage() {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [uploadType, setUploadType] = useState<"product" | "sale">("product")
  const [stockItems, setStockItems] = useState<
    Array<{
      id: number
      name: string
      quantity: number
      category: string
      flag: string
      flagColor: string
    }>
  >([])
  const [isLoading, setIsLoading] = useState(true)
  const [salesFile, setSalesFile] = useState<File | null>(null)
  const [productFile, setProductFile] = useState<File | null>(null)
  const [currentFile, setCurrentFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [backendConnected, setBackendConnected] = useState(true)
  const [showOfflineBanner, setShowOfflineBanner] = useState(false)

  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("")
  const [selectedFlag, setSelectedFlag] = useState("")
  const [sortBy, setSortBy] = useState("name")
  const [showFilterMenu, setShowFilterMenu] = useState(false)
  const [categories, setCategories] = useState<string[]>([])

  const searchDebounceTimer = useRef<NodeJS.Timeout | null>(null)
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("")
  const [isFetching, setIsFetching] = useState(false)

  const fetchStocks = useCallback(async () => {
    if (isFetching) return

    setIsLoading(true)
    setIsFetching(true)
    try {
      console.log("[v0] Fetching stock levels...")

      const data = await getStockLevels({
        search: debouncedSearchQuery || undefined,
        category: selectedCategory || undefined,
        flag: selectedFlag || undefined,
        sort_by: sortBy || undefined,
      })

      console.log("[v0] Stock levels response:", data)

      if (data.success) {
        const mapped = data.data.map((item: any, index: number) => ({
          id: index + 1,
          name: item.product_name,
          quantity: item.quantity || item.stock_level || 0,
          category: item.category || "Uncategorized",
          flag: item.status || item.flag || "stage",
          flagColor: getFlagColor(item.status || item.flag || "stage"),
        }))
        setStockItems(mapped)
        setBackendConnected(true)
        setShowOfflineBanner(false)
      }
    } catch (error) {
      console.error("[v0] Failed to fetch stock levels:", error)
      setBackendConnected(false)
      setShowOfflineBanner(true)
    } finally {
      setIsLoading(false)
      setIsFetching(false)
    }
  }, [debouncedSearchQuery, selectedCategory, selectedFlag, sortBy]) // Removed isFetching from dependencies

  const fetchCategories = useCallback(async () => {
    try {
      const data = await getStockCategories()
      console.log("[v0] Categories response:", data)
      if (data.success) {
        setCategories(data.data || [])
      }
    } catch (error) {
      console.error("[v0] Failed to fetch categories:", error)
    }
  }, [])

  useEffect(() => {
    if (searchDebounceTimer.current) {
      clearTimeout(searchDebounceTimer.current)
    }

    searchDebounceTimer.current = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery)
    }, 300) // 300ms debounce

    return () => {
      if (searchDebounceTimer.current) {
        clearTimeout(searchDebounceTimer.current)
      }
    }
  }, [searchQuery])

  useEffect(() => {
    fetchStocks()
  }, [debouncedSearchQuery, selectedCategory, selectedFlag, sortBy]) // Removed fetchStocks from dependencies

  useEffect(() => {
    fetchCategories()
  }, []) // Removed fetchCategories from dependencies

  function getFlagColor(flag: string): string {
    switch (flag) {
      case "active":
        return "#00a63e" // green
      case "inactive":
        return "#938d7a" // gray
      case "just added stock":
        return "#4a90e2" // blue
      default:
        return "#cecabf" // default
    }
  }

  function getFlagText(flag: string): string {
    switch (flag) {
      case "active":
        return "Active"
      case "inactive":
        return "Inactive"
      case "just added stock":
        return "Just Added"
      default:
        return "Stage"
    }
  }

  const openUploadModal = (type: "product" | "sale") => {
    setUploadType(type)
    setCurrentFile(null)
    setIsUploadModalOpen(true)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      console.log("[v0] File selected:", file.name, "Type:", uploadType)
      setCurrentFile(file)
    }
  }

  const handleUpload = async () => {
    if (!currentFile) {
      alert("Please select a file to upload.")
      return
    }

    console.log("[v0] Starting upload for:", uploadType, "file:", currentFile.name)
    setIsUploading(true)

    try {
      if (uploadType === "product") {
        setProductFile(currentFile)
        alert(`Product file "${currentFile.name}" uploaded successfully! Now upload the Sales file to train the model.`)
        setIsUploadModalOpen(false)
        setCurrentFile(null)
      } else {
        setSalesFile(currentFile)

        if (!productFile) {
          alert("Please upload the Product file first before uploading the Sales file.")
          setIsUploadModalOpen(false)
          setCurrentFile(null)
          return
        }

        console.log("[v0] Training model with product:", productFile.name, "and sales:", currentFile.name)
        const result = await trainModel(currentFile, productFile)

        if (result.ml_training?.status === "completed") {
          alert(
            `Success! ${result.data_cleaning.rows_uploaded} rows uploaded and ${result.ml_training.forecast_rows} forecasts generated. Redirecting to Predict page...`,
          )
          setIsUploadModalOpen(false)
          setSalesFile(null)
          setProductFile(null)
          setCurrentFile(null)
          window.location.href = "/dashboard/predict"
        } else if (result.ml_training?.status === "skipped") {
          alert(
            `Files uploaded successfully (${result.data_cleaning.rows_uploaded} rows)!\n\n${result.ml_training.message}\n\nYou can view your stock data now. To enable forecasting, start the Python backend server.`,
          )
          setIsUploadModalOpen(false)
          setSalesFile(null)
          setProductFile(null)
          setCurrentFile(null)
          window.location.reload()
        } else if (result.ml_training?.status === "failed") {
          alert(
            `Data uploaded successfully (${result.data_cleaning.rows_uploaded} rows), but forecast generation failed: ${result.ml_training.message}. You can manually generate forecasts from the Predict page.`,
          )
          setIsUploadModalOpen(false)
          setSalesFile(null)
          setProductFile(null)
          setCurrentFile(null)
          window.location.reload()
        } else {
          alert(
            `Data uploaded successfully (${result.data_cleaning.rows_uploaded} rows). ${result.ml_training?.message || "Forecast generation was skipped."}`,
          )
          setIsUploadModalOpen(false)
          setSalesFile(null)
          setProductFile(null)
          setCurrentFile(null)
          window.location.reload()
        }
      }
    } catch (error) {
      console.error("[v0] Upload failed:", error)
      alert(`Upload failed: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f8f5ee]">
      {/* Header */}
      <header className="bg-white border-b border-[#efece3] px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-serif text-black">Lon TukTak</h1>
            <p className="text-xs text-[#938d7a]">Stock Management</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-[#f8f5ee] rounded-lg">
              {backendConnected ? (
                <>
                  <Wifi className="w-4 h-4 text-[#00a63e]" />
                  <span className="text-xs text-[#00a63e] font-medium">Supabase Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-4 h-4 text-[#ea5457]" />
                  <span className="text-xs text-[#ea5457] font-medium">Database Offline</span>
                </>
              )}
            </div>
            <div className="w-10 h-10 bg-[#ffd700] rounded flex items-center justify-center font-bold text-black text-sm">
              TG
            </div>
            <div>
              <p className="text-sm font-medium text-black">Toogton</p>
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
              className="flex items-center gap-3 px-3 py-2.5 bg-white rounded-lg text-black font-medium"
            >
              <Package className="w-5 h-5" />
              <span>Stocks</span>
            </Link>
            <Link
              href="/dashboard/predict"
              className="flex items-center gap-3 px-3 py-2.5 text-[#1e1e1e] hover:bg-white/50 rounded-lg transition-colors"
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
          {showOfflineBanner && (
            <div className="mb-6 bg-[#fff4e6] border border-[#eaac54] rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-[#eaac54] flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-medium text-black mb-1">Database Connection Error</h4>
                  <p className="text-sm text-[#938d7a] mb-2">
                    Cannot connect to Supabase. Please check your environment variables.
                  </p>
                  <p className="text-sm text-black font-medium">
                    Required: NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY
                  </p>
                </div>
                <button
                  onClick={() => setShowOfflineBanner(false)}
                  className="text-[#938d7a] hover:text-black transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Page Header */}
          <div className="flex items-start justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-black mb-2">Stock Management</h2>
              <p className="text-[#938d7a]">Monitor & manage your inventory levels</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => openUploadModal("product")}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-[#cecabf] rounded-lg hover:bg-[#efece3] transition-colors"
              >
                <Upload className="w-4 h-4 text-black" />
                <span className="text-sm font-medium text-black">Upload Product List</span>
              </button>
              <button
                onClick={() => openUploadModal("sale")}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-[#cecabf] rounded-lg hover:bg-[#efece3] transition-colors"
              >
                <Upload className="w-4 h-4 text-black" />
                <span className="text-sm font-medium text-black">Upload Sale Stock</span>
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg p-6 border border-[#cecabf]/30 mb-6">
            <h3 className="text-sm font-medium text-black mb-4">Search & Filters</h3>
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#938d7a]" />
                <input
                  type="text"
                  placeholder="Search products..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-[#f8f5ee] rounded-lg border-none outline-none text-sm text-black placeholder:text-[#938d7a]"
                />
              </div>
              <div className="relative">
                <button
                  onClick={() => setShowFilterMenu(!showFilterMenu)}
                  className="flex items-center gap-2 px-4 py-2 bg-[#efece3] rounded-lg hover:bg-[#e5e2d8] transition-colors"
                >
                  <Filter className="w-4 h-4 text-black" />
                  <span className="text-sm font-medium text-black">Filter</span>
                  <ChevronDown className="w-4 h-4 text-black" />
                </button>

                {showFilterMenu && (
                  <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-[#cecabf]/30 p-4 z-10">
                    <div className="mb-4">
                      <label className="text-xs font-medium text-[#938d7a] mb-2 block">Category</label>
                      <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="w-full px-3 py-2 bg-[#f8f5ee] rounded-lg border-none outline-none text-sm text-black"
                      >
                        <option value="">All Categories</option>
                        {categories.map((cat) => (
                          <option key={cat} value={cat}>
                            {cat}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="mb-4">
                      <label className="text-xs font-medium text-[#938d7a] mb-2 block">Status</label>
                      <select
                        value={selectedFlag}
                        onChange={(e) => setSelectedFlag(e.target.value)}
                        className="w-full px-3 py-2 bg-[#f8f5ee] rounded-lg border-none outline-none text-sm text-black"
                      >
                        <option value="">All Status</option>
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                        <option value="just added stock">Just Added</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs font-medium text-[#938d7a] mb-2 block">Sort By</label>
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="w-full px-3 py-2 bg-[#f8f5ee] rounded-lg border-none outline-none text-sm text-black"
                      >
                        <option value="name">Name (A-Z)</option>
                        <option value="quantity_asc">Quantity (Low to High)</option>
                        <option value="quantity_desc">Quantity (High to Low)</option>
                      </select>
                    </div>

                    <button
                      onClick={() => {
                        setSelectedCategory("")
                        setSelectedFlag("")
                        setSortBy("name")
                      }}
                      className="w-full mt-4 px-4 py-2 bg-[#cecabf] rounded-lg text-black text-sm font-medium hover:bg-[#c5c5c5] transition-colors"
                    >
                      Clear Filters
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg p-6 border border-[#cecabf]/30">
            <h3 className="text-sm font-medium text-black mb-4">
              Stock Items ( {isLoading ? "..." : stockItems.length} )
            </h3>
            {isLoading ? (
              <div className="text-center py-8 text-[#938d7a]">Loading stock data...</div>
            ) : stockItems.length === 0 ? (
              <div className="text-center py-8">
                <Package className="w-12 h-12 text-[#cecabf] mx-auto mb-3" />
                <p className="text-[#938d7a] mb-2">No stock data available</p>
                <p className="text-sm text-[#938d7a]">
                  {backendConnected
                    ? "Please upload stock files in the Notifications page to view stock data here."
                    : "Check your Supabase connection and upload files in the Notifications page."}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {stockItems.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-4 bg-[#f8f5ee] rounded-lg border border-[#cecabf]/20"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.flagColor }} />
                      <div>
                        <h4 className="font-medium text-black">{item.name}</h4>
                        <p className="text-sm text-[#938d7a]">Quantity: {item.quantity}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="px-3 py-1 bg-white border border-[#cecabf] rounded-full text-xs text-black">
                        {item.category}
                      </span>
                      <span
                        className="px-3 py-1 rounded-full text-xs text-white"
                        style={{ backgroundColor: item.flagColor }}
                      >
                        {getFlagText(item.flag)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>

      {isUploadModalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-2xl p-6 relative">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-black">
                Upload {uploadType === "sale" ? "Sales" : "Product"} File
              </h3>
              <button
                onClick={() => setIsUploadModalOpen(false)}
                className="text-[#938d7a] hover:text-black transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mb-6 p-4 bg-[#f8f5ee] rounded-lg space-y-2">
              <div className="flex items-center gap-2">
                {productFile ? (
                  <CheckCircle2 className="w-5 h-5 text-[#00a63e]" />
                ) : (
                  <div className="w-5 h-5 rounded-full border-2 border-[#cecabf]" />
                )}
                <p className="text-sm text-black">
                  <strong>Product file:</strong> {productFile ? productFile.name : "Not uploaded"}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {salesFile ? (
                  <CheckCircle2 className="w-5 h-5 text-[#00a63e]" />
                ) : (
                  <div className="w-5 h-5 rounded-full border-2 border-[#cecabf]" />
                )}
                <p className="text-sm text-black">
                  <strong>Sales file:</strong> {salesFile ? salesFile.name : "Not uploaded"}
                </p>
              </div>
              <p className="text-xs text-[#938d7a] mt-3 pt-3 border-t border-[#cecabf]/30">
                Note: Upload Product file first, then Sales file. The model will train automatically after both files
                are uploaded.
              </p>
            </div>

            <div className="border-2 border-dashed border-[#cecabf] rounded-lg p-12 mb-6">
              <div className="flex flex-col items-center justify-center gap-4">
                <CloudUpload className="w-24 h-24 text-[#cecabf]" />
                <p className="text-[#938d7a] text-sm">{currentFile?.name || "Drag a file here or click Browse"}</p>
              </div>
            </div>

            <div className="flex gap-4">
              <label className="flex-1 px-6 py-3 bg-white border border-[#cecabf] rounded-lg text-black font-medium hover:bg-[#f8f5ee] transition-colors text-center cursor-pointer">
                Browse
                <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFileChange} className="hidden" />
              </label>
              <button
                onClick={handleUpload}
                disabled={isUploading || !currentFile}
                className="flex-1 px-6 py-3 bg-[#cecabf] rounded-lg text-black font-medium hover:bg-[#c5c5c5] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? "Uploading..." : "Upload"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
