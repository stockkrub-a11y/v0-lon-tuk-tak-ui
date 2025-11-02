"use client"

import type React from "react"

import { useState, useEffect, useMemo, useCallback } from "react"
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
  AlertCircle,
  PackageIcon,
  TrendingDown,
  Shield,
  Target,
  RotateCcw,
  CheckCircle,
  CloudUpload,
  Edit2,
  Save,
  ArrowUpDown,
} from "lucide-react"

import { getNotifications, checkBaseStock, uploadStockFiles, updateNotificationManualValues } from "@/lib/api"

type NotificationStatus = "critical" | "warning" | "safe"
type SortOption = "name-asc" | "name-desc" | "quantity-asc" | "quantity-desc" | "none" // Added SortOption type

interface Notification {
  id: string
  status: NotificationStatus
  title: string
  product: string
  sku: string
  category: string // Added Category mapping
  estimatedTime: string
  recommendUnits: number
  currentStock: number
  decreaseRate: string
  timeToRunOut: string
  minStock: number
  buffer: number
  recommendedRestock: number
}

export default function NotificationsPage() {
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null)
  const [showFilterModal, setShowFilterModal] = useState(false)
  const [selectedStatuses, setSelectedStatuses] = useState<NotificationStatus[]>([])
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]) // Added state for selected categories
  const [searchQuery, setSearchQuery] = useState("") // Added state for search query
  const [categorySearch, setCategorySearch] = useState("") // Added state for category search
  const [isPreviousStockModalOpen, setIsPreviousStockModalOpen] = useState(false)
  const [isCurrentStockModalOpen, setIsCurrentStockModalOpen] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [previousStockFile, setPreviousStockFile] = useState<File | null>(null)
  const [currentStockFile, setCurrentStockFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [baseStockExists, setBaseStockExists] = useState(false)
  const [checkingBaseStock, setCheckingBaseStock] = useState(true)
  const [isEditingMinStock, setIsEditingMinStock] = useState(false) // Added state for editing min stock
  const [isEditingBuffer, setIsEditingBuffer] = useState(false) // Added state for editing buffer
  const [editedMinStock, setEditedMinStock] = useState<number>(0) // Added state for edited min stock
  const [editedBuffer, setEditedBuffer] = useState<number>(0) // Added state for edited buffer
  const [isSaving, setIsSaving] = useState(false) // Added state for saving
  const [sortBy, setSortBy] = useState<SortOption>("none") // Added sort state

  const [isFetching, setIsFetching] = useState(false)

  useEffect(() => {
    async function checkStock() {
      try {
        const data = await checkBaseStock()
        console.log("[v0] base_stock check:", data)
        // row_count may be undefined; guard with nullish coalescing
        setBaseStockExists(Boolean(data?.exists && (data?.row_count ?? 0) > 0))
      } catch (error) {
        console.error("[v0] Failed to check base_stock:", error)
        setBaseStockExists(false)
      } finally {
        setCheckingBaseStock(false)
      }
    }

    checkStock()
  }, [])

  // Extracted fetch + mapping into a reusable function so we can refresh after updates
  const fetchAndSetNotifications = useCallback(async () => {
    if (isFetching) return // Prevent multiple simultaneous fetches

    setIsLoading(true)
    setIsFetching(true)
    try {
      console.log("[v0] ===== FETCHING NOTIFICATIONS START =====")
      console.log("[v0] API URL:", process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")

      const data: any = await getNotifications()

      console.log("[v0] ===== FETCHING NOTIFICATIONS COMPLETE =====")
      console.log("[v0] Received data:", data)

      if (!Array.isArray(data)) {
        console.error("[v0] Data is not an array:", data)
        setNotifications([])
        return
      }

      const mapped: Notification[] = data.map((item, index) => {
        console.log(`[v0] Mapping item ${index}:`, item)

        const status: NotificationStatus =
          item.Status === "Red" ? "critical" : item.Status === "Yellow" ? "warning" : "safe"

        return {
          id: String(index + 1),
          status,
          title:
            item.Description &&
            (item.Description.includes("out of stock")
              ? "Nearly Out of Stock!"
              : item.Description.includes("Decreasing rapidly")
                ? "Decreasing Rapidly"
                : "Stock is Enough"),
          product: item.Product,
          sku: item.Product_SKU || item.Product,
          category: item.Category || "Uncategorized", // Added Category mapping
          estimatedTime: `${item.Weeks_To_Empty || 0} weeks`,
          recommendUnits: item.Reorder_Qty || 0,
          currentStock: item.Stock || 0,
          decreaseRate: `${item["Decrease_Rate(%)"] || 0}%/week`,
          timeToRunOut: `${Math.round((item.Weeks_To_Empty || 0) * 7)} days`,
          minStock: item.MinStock ?? item.min_stock ?? item.minstock ?? 0,
          buffer: item.Buffer ?? item.buffer ?? item.reorder_qty ?? 0,
          recommendedRestock: item.Reorder_Qty || 0,
        }
      })
      console.log("[v0] Mapped notifications:", mapped.length)
      setNotifications(mapped)
    } catch (error) {
      console.error("[v0] Failed to fetch notifications:", error)
    } finally {
      setIsLoading(false)
      setIsFetching(false)
    }
  }, [isFetching])

  useEffect(() => {
    fetchAndSetNotifications()
  }, []) // Removed fetchAndSetNotifications from dependencies to prevent infinite loop

  const filteredAndSortedNotifications = useMemo(() => {
    return notifications
      .filter((n) => {
        // Status filter
        if (selectedStatuses.length > 0 && !selectedStatuses.includes(n.status)) {
          return false
        }

        // Category filter
        if (selectedCategories.length > 0 && !selectedCategories.includes(n.category)) {
          return false
        }

        // Search filter (searches in SKU and product name)
        if (
          searchQuery &&
          !n.sku.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !n.product.toLowerCase().includes(searchQuery.toLowerCase())
        ) {
          return false
        }

        return true
      })
      .sort((a, b) => {
        // Apply sorting
        switch (sortBy) {
          case "name-asc":
            return a.product.localeCompare(b.product)
          case "name-desc":
            return b.product.localeCompare(a.product)
          case "quantity-asc":
            return a.currentStock - b.currentStock
          case "quantity-desc":
            return b.currentStock - a.currentStock
          default:
            return 0
        }
      })
  }, [notifications, selectedStatuses, selectedCategories, searchQuery, sortBy])

  // Get unique categories from notifications
  const uniqueCategories = useMemo(() => {
    return Array.from(new Set(notifications.map((n) => n.category))).sort()
  }, [notifications])

  // Filter categories based on search
  const filteredCategories = useMemo(() => {
    return uniqueCategories.filter((cat) => cat.toLowerCase().includes(categorySearch.toLowerCase()))
  }, [uniqueCategories, categorySearch])

  const getStatusColor = (status: NotificationStatus) => {
    switch (status) {
      case "critical":
        return "border-l-[#ea5457]"
      case "warning":
        return "border-l-[#eaac54]"
      case "safe":
        return "border-l-[#00a63e]"
    }
  }

  const getStatusIcon = (status: NotificationStatus) => {
    switch (status) {
      case "critical":
        return <AlertCircle className="w-5 h-5 text-[#ea5457]" />
      case "warning":
        return <PackageIcon className="w-5 h-5 text-[#eaac54]" />
      case "safe":
        return <CheckCircle className="w-5 h-5 text-[#00a63e]" />
    }
  }

  const getStatusTextColor = (status: NotificationStatus) => {
    switch (status) {
      case "critical":
        return "text-[#ea5457]"
      case "warning":
        return "text-[#eaac54]"
      case "safe":
        return "text-[#00a63e]"
    }
  }

  const exportToCSV = () => {
    const headers = [
      "Status",
      "Product SKU", // Updated header for clarity
      "Product Name", // Added Product Name header
      "Category", // Added Category header
      "Current Stock",
      "Decrease Rate",
      "Time to Run Out",
      "Min Stock",
      "Buffer",
      "Recommended Restock",
    ]
    const rows = filteredAndSortedNotifications.map((n) => [
      n.status,
      n.sku, // Exported SKU
      n.product, // Exported Product Name
      n.category, // Exported Category
      n.currentStock,
      n.decreaseRate,
      n.timeToRunOut,
      n.minStock,
      n.buffer,
      n.recommendedRestock,
    ])

    const csvContent = [headers, ...rows].map((row) => row.join(",")).join("\n")
    const blob = new Blob([csvContent], { type: "text/csv" })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "notifications.csv"
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const toggleStatus = (status: NotificationStatus) => {
    setSelectedStatuses((prev) => (prev.includes(status) ? prev.filter((s) => s !== status) : [...prev, status]))
  }

  const toggleCategory = (category: string) => {
    // Added function to toggle category selection
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category],
    )
  }

  const handleSaveManualValues = async () => {
    if (!selectedNotification) return

    // Always use the edited values when saving
    const finalMinStock = Number(editedMinStock) || 0
    const finalBuffer = Number(editedBuffer) || 0

    console.log("[v0] Saving values to backend:", {
      sku: selectedNotification.sku,
      minStock: finalMinStock,
      buffer: finalBuffer,
    })

    setIsSaving(true)
    try {
      // Try to update via backend if available
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      try {
        console.log(
          "[v0] Sending update for SKU:",
          selectedNotification.sku,
          "minstock:",
          finalMinStock,
          "buffer:",
          finalBuffer,
        )
        const res = await fetch(
          `${apiUrl}/notifications/update_manual_values?product_sku=${encodeURIComponent(
            selectedNotification.sku,
          )}&minstock=${finalMinStock}&buffer=${finalBuffer}`,
          {
            method: "POST",
          },
        )

        if (res.ok) {
          const json = await res.json()
          console.log("[v0] Backend update response:", json)

          if (json && json.success) {
            await fetchAndSetNotifications()

            // Wait a bit longer for React state to settle
            await new Promise((resolve) => setTimeout(resolve, 200))

            // Update the selected notification with the saved values
            setSelectedNotification((prev) =>
              prev
                ? {
                    ...prev,
                    minStock: finalMinStock,
                    buffer: finalBuffer,
                  }
                : prev,
            )
            setEditedMinStock(finalMinStock)
            setEditedBuffer(finalBuffer)
            setIsEditingMinStock(false)
            setIsEditingBuffer(false)

            alert("Manual values updated and report regenerated (backend).")
            setIsSaving(false)
            return
          }
        }
      } catch (e) {
        // Backend not available or failed — fall back to Supabase-only update
        console.log("[v0] Backend failed, falling back to Supabase-only mode")
      }

      const result = await updateNotificationManualValues(selectedNotification.sku, finalMinStock, finalBuffer)
      if (result && result.success) {
        // Refresh notifications to get latest status/description
        await fetchAndSetNotifications()

        // Wait for React state to settle
        await new Promise((resolve) => setTimeout(resolve, 200))

        // Update the selected notification with the saved values
        setSelectedNotification((prev) =>
          prev
            ? {
                ...prev,
                minStock: finalMinStock,
                buffer: finalBuffer,
              }
            : prev,
        )
        setEditedMinStock(finalMinStock)
        setEditedBuffer(finalBuffer)
        setIsEditingMinStock(false)
        setIsEditingBuffer(false)

        alert("Manual values updated successfully (Supabase-only mode).")
      } else {
        alert(`Failed to update manual values: ${result?.message || "Unknown error"}`)
      }
      setIsSaving(false)
    } catch (error) {
      console.error("[v0] Failed to update manual values:", error)
      alert(`Failed to update: ${error instanceof Error ? error.message : "Unknown error"}`)
      setIsSaving(false)
    }
  }

  const handlePreviousFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      console.log("[v0] Previous stock file selected:", file.name)
      setPreviousStockFile(file)
    }
  }

  const handleCurrentFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      console.log("[v0] Current stock file selected:", file.name)
      setCurrentStockFile(file)
    }
  }

  const handleUpload = async () => {
    if (baseStockExists) {
      if (!currentStockFile) {
        alert("Please select a current stock file")
        return
      }
    } else {
      if (!previousStockFile || !currentStockFile) {
        alert("Please select both previous and current stock files")
        return
      }
    }

    setIsUploading(true)
    try {
      console.log("[v0] Starting upload for:")
      console.log("[v0] - Previous file:", previousStockFile?.name || "None")
      console.log("[v0] - Current file:", currentStockFile?.name)

      const result = await uploadStockFiles(baseStockExists ? undefined : previousStockFile, currentStockFile)

      console.log("[v0] Upload result:", result)

      // Backend returns a simple success message and notifications_count
      alert(`Upload successful! ${result.message || "Report generated"}`)
      window.location.reload()
    } catch (error) {
      console.error("[v0] Upload failed:", error)
      alert(`Upload failed: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setIsUploading(false)
      setIsCurrentStockModalOpen(false)
    }
  }

  const handleClearBaseStock = async () => {
    if (
      !confirm("Are you sure you want to clear all stock data? This will reset both stock history and notifications.")
    ) {
      return
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      const response = await fetch(`${apiUrl}/clear_stock`, {
        method: "POST",
      })

      if (!response.ok) {
        throw new Error(`Failed to clear stock: ${response.status}`)
      }

      const result = await response.json()
      alert(`Stock data cleared successfully!\n\n${result.message}`)
      window.location.reload()
    } catch (error) {
      console.error("[v0] Failed to clear stock data:", error)
      alert(`Failed to clear stock data: ${error instanceof Error ? error.message : "Unknown error"}`)
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

          <div className="flex-1 max-w-xl mx-8">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#938d7a]" />
              <input
                type="text"
                placeholder="Search for product SKU or name..." // Updated placeholder
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
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
        {/* Sidebar */}
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
              className="flex items-center gap-3 px-3 py-2.5 bg-white rounded-lg text-black font-medium"
            >
              <Bell className="w-5 h-5" />
              <span>Notifications</span>
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <div className="flex items-start justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-black mb-2">Notifications</h2>
              <p className="text-[#938d7a]">Stay updated with your inventory alerts</p>
            </div>
            <div className="flex gap-3">
              {!checkingBaseStock && !baseStockExists && (
                <button
                  onClick={() => setIsPreviousStockModalOpen(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg border border-[#cecabf] hover:bg-[#efece3] transition-colors"
                >
                  <Upload className="w-4 h-4" />
                  <span className="text-sm font-medium">Upload Previous Stock</span>
                </button>
              )}
              <button
                onClick={() => setIsCurrentStockModalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg border border-[#cecabf] hover:bg-[#efece3] transition-colors"
              >
                <Upload className="w-4 h-4" />
                <span className="text-sm font-medium">Upload Current Stock</span>
              </button>
              {baseStockExists && (
                <button
                  onClick={handleClearBaseStock}
                  className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg border border-[#ea5457] text-[#ea5457] hover:bg-[#ffe2e2] transition-colors"
                >
                  <X className="w-4 h-4" />
                  <span className="text-sm font-medium">Clear Stock</span>
                </button>
              )}
              <button
                onClick={() => setShowFilterModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg border border-[#cecabf] hover:bg-[#efece3] transition-colors"
              >
                <Filter className="w-4 h-4" />
                <span className="text-sm font-medium">Filter Notifications</span>
              </button>
            </div>
          </div>

          {/* Notifications List */}
          {isLoading ? (
            <div className="text-center py-8 text-[#938d7a]">Loading notifications...</div>
          ) : notifications.length === 0 ? (
            <div className="text-center py-8 text-[#938d7a]">
              <p className="mb-2">No notifications available.</p>
              <p className="text-sm">Please upload stock files in the Notifications page to generate stock reports.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredAndSortedNotifications.map((notification) => (
                <button
                  key={notification.id}
                  onClick={() => {
                    const currentNotification = notifications.find((n) => n.sku === notification.sku) ?? notification

                    console.log("[v0] Opening modal for:", currentNotification.sku, {
                      minStock: currentNotification.minStock,
                      buffer: currentNotification.buffer,
                    })

                    setSelectedNotification(currentNotification)
                    setEditedMinStock(Number(currentNotification.minStock) || 0)
                    setEditedBuffer(Number(currentNotification.buffer) || 0)
                    setIsEditingMinStock(false)
                    setIsEditingBuffer(false)
                    setIsSaving(false)
                  }}
                  className={`w-full bg-white rounded-lg p-6 border-l-4 ${getStatusColor(
                    notification.status,
                  )} hover:shadow-md transition-shadow text-left relative`}
                >
                  <div className="flex items-start gap-4">
                    {getStatusIcon(notification.status)}
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-black mb-1">
                        <span className={getStatusTextColor(notification.status)}>{notification.title}</span> -{" "}
                        {notification.sku}
                      </h3>
                      <p className="text-sm text-[#938d7a] mb-2">{notification.product}</p>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="px-2 py-0.5 bg-[#efece3] text-[#938d7a] text-xs rounded-full font-medium">
                          {notification.category}
                        </span>
                      </div>
                      <p className="text-sm text-[#938d7a] mt-1">
                        Estimated to run out in{" "}
                        <span className={getStatusTextColor(notification.status)}>{notification.estimatedTime}</span>
                        {notification.recommendUnits > 0 && (
                          <>
                            {" "}
                            - Recommend Restocking{" "}
                            <span className={getStatusTextColor(notification.status)}>
                              {notification.recommendUnits} Units
                            </span>
                          </>
                        )}
                      </p>
                    </div>
                    <div className="w-2 h-2 bg-[#547fff] rounded-full" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </main>
      </div>

      {/* Detail Modal */}
      {selectedNotification && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-3xl w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-xl font-bold text-black">{selectedNotification.sku}</h3>
                  <span className="px-3 py-1 bg-[#efece3] text-[#938d7a] text-sm rounded-full font-medium">
                    {selectedNotification.category}
                  </span>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      selectedNotification.status === "critical"
                        ? "bg-[#ffe2e2] text-[#9f0712]"
                        : selectedNotification.status === "warning"
                          ? "bg-[#fff4e6] text-[#eaac54]"
                          : "bg-[#ebf9f3] text-[#00a63e]"
                    }`}
                  >
                    {selectedNotification.status === "critical"
                      ? "Critical"
                      : selectedNotification.status === "warning"
                        ? "Warning"
                        : "Safe"}
                  </span>
                </div>
                <p className="text-sm text-[#938d7a]">{selectedNotification.product}</p>
                <p className="text-xs text-[#938d7a]">Updated 5m ago</p>
              </div>
              <button
                onClick={() => {
                  setSelectedNotification(null)
                  setIsEditingMinStock(false)
                  setIsEditingBuffer(false)
                  setIsSaving(false)
                }}
                className="text-[#938d7a] hover:text-black"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="border border-[#cecabf] rounded-lg p-4">
                <p className="text-xs text-[#938d7a] mb-2">Current Stock</p>
                <div className="flex items-center justify-between">
                  <p className="text-3xl font-bold text-black">{selectedNotification.currentStock}</p>
                  <PackageIcon className="w-8 h-8 text-[#938d7a]" />
                </div>
                <p className="text-xs text-[#938d7a] mt-1">units remaining</p>
              </div>

              <div className="border border-[#cecabf] rounded-lg p-4">
                <p className="text-xs text-[#938d7a] mb-2">Decrease Rate</p>
                <div className="flex items-center justify-between">
                  <p className="text-3xl font-bold text-black">{selectedNotification.decreaseRate}</p>
                  <TrendingDown className="w-8 h-8 text-[#938d7a]" />
                </div>
                <p className="text-xs text-[#938d7a] mt-1">trending down</p>
              </div>

              <div className="border border-[#cecabf] rounded-lg p-4">
                <p className="text-xs text-[#938d7a] mb-2">Time to Run Out</p>
                <div className="flex items-center justify-between">
                  <p className="text-3xl font-bold text-black">{selectedNotification.timeToRunOut}</p>
                  <AlertCircle className="w-8 h-8 text-[#938d7a]" />
                </div>
                <p className="text-xs text-[#938d7a] mt-1">at current rate</p>
              </div>

              <div className="border border-[#cecabf] rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-[#938d7a]">Min Stock</p>
                  <button
                    onClick={() => {
                      // When turning off editing, ensure we keep the edited value
                      if (isEditingMinStock) {
                        setSelectedNotification((prev) =>
                          prev
                            ? {
                                ...prev,
                                minStock: editedMinStock,
                              }
                            : prev,
                        )
                      }
                      setIsEditingMinStock(!isEditingMinStock)
                    }}
                    className="text-[#938d7a] hover:text-black"
                  >
                    <Edit2 className="w-3 h-3" />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  {isEditingMinStock ? (
                    <input
                      type="number"
                      value={editedMinStock}
                      onChange={(e) => {
                        const newValue = Number(e.target.value)
                        console.log("[v0] Setting minStock to:", newValue)
                        setEditedMinStock(isNaN(newValue) ? 0 : newValue)
                        // Update the selected notification to preserve the value
                        setSelectedNotification((prev) =>
                          prev
                            ? {
                                ...prev,
                                minStock: isNaN(newValue) ? 0 : newValue,
                              }
                            : prev,
                        )
                      }}
                      className="text-3xl font-bold text-black w-24 border-b-2 border-[#cecabf] focus:outline-none focus:border-black"
                    />
                  ) : (
                    <p className="text-3xl font-bold text-black">{editedMinStock ?? selectedNotification.minStock}</p>
                  )}
                  <Shield className="w-8 h-8 text-[#938d7a]" />
                </div>
                <p className="text-xs text-[#938d7a] mt-1">threshold</p>
              </div>

              <div className="border border-[#cecabf] rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-[#938d7a]">Buffer</p>
                  <button
                    onClick={() => {
                      // When turning off editing, ensure we keep the edited value
                      if (isEditingBuffer) {
                        setSelectedNotification((prev) =>
                          prev
                            ? {
                                ...prev,
                                buffer: editedBuffer,
                              }
                            : prev,
                        )
                      }
                      setIsEditingBuffer(!isEditingBuffer)
                    }}
                    className="text-[#938d7a] hover:text-black"
                  >
                    <Edit2 className="w-3 h-3" />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  {isEditingBuffer ? (
                    <input
                      type="number"
                      value={editedBuffer}
                      onChange={(e) => {
                        const newValue = Number(e.target.value)
                        console.log("[v0] Setting buffer to:", newValue)
                        setEditedBuffer(isNaN(newValue) ? 0 : newValue)
                        // Update the selected notification to preserve the value
                        setSelectedNotification((prev) =>
                          prev
                            ? {
                                ...prev,
                                buffer: isNaN(newValue) ? 0 : newValue,
                              }
                            : prev,
                        )
                      }}
                      className="text-3xl font-bold text-black w-24 border-b-2 border-[#cecabf] focus:outline-none focus:border-black"
                    />
                  ) : (
                    <p className="text-3xl font-bold text-black">{editedBuffer ?? selectedNotification.buffer}</p>
                  )}
                  <Target className="w-8 h-8 text-[#938d7a]" />
                </div>
                <p className="text-xs text-[#938d7a] mt-1">safety stock</p>
              </div>

              <div className="border border-[#cecabf] rounded-lg p-4">
                <p className="text-xs text-[#938d7a] mb-2">Recommended restock</p>
                <div className="flex items-center justify-between">
                  <p className="text-3xl font-bold text-black">{selectedNotification.recommendedRestock}</p>
                  <RotateCcw className="w-8 h-8 text-[#938d7a]" />
                </div>
                <p className="text-xs text-[#938d7a] mt-1">units suggested</p>
              </div>
            </div>

            {(isEditingMinStock || isEditingBuffer) && (
              <div className="flex justify-end">
                <button
                  onClick={handleSaveManualValues}
                  disabled={isSaving}
                  className="flex items-center gap-2 px-6 py-2 bg-[#cecabf] text-black rounded-lg hover:bg-[#938d7a] hover:text-white transition-colors disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  <span>{isSaving ? "Saving..." : "Save & Regenerate Report"}</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {showFilterModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-black">Filters</h3>
              <button onClick={() => setShowFilterModal(false)} className="text-[#938d7a] hover:text-black">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-6 mb-6">
              {/* Inventory Status */}
              <div>
                <p className="text-sm font-medium text-black mb-3">Inventory Status</p>
                <div className="space-y-2">
                  <button
                    onClick={() => toggleStatus("critical")}
                    className={`w-full px-4 py-2 rounded-lg text-sm text-left transition-colors ${
                      selectedStatuses.includes("critical")
                        ? "bg-[#ffe2e2] text-[#9f0712] ring-2 ring-[#ea5457]"
                        : "bg-[#ffe2e2] text-[#9f0712] hover:ring-2 hover:ring-[#ea5457]"
                    }`}
                  >
                    Critical
                  </button>
                  <button
                    onClick={() => toggleStatus("warning")}
                    className={`w-full px-4 py-2 rounded-lg text-sm text-left transition-colors ${
                      selectedStatuses.includes("warning")
                        ? "bg-[#fff4e6] text-[#eaac54] ring-2 ring-[#eaac54]"
                        : "bg-[#fff4e6] text-[#eaac54] hover:ring-2 hover:ring-[#eaac54]"
                    }`}
                  >
                    Warning
                  </button>
                  <button
                    onClick={() => toggleStatus("safe")}
                    className={`w-full px-4 py-2 rounded-lg text-sm text-left transition-colors ${
                      selectedStatuses.includes("safe")
                        ? "bg-[#ebf9f3] text-[#00a63e] ring-2 ring-[#00a63e]"
                        : "bg-[#ebf9f3] text-[#00a63e] hover:ring-2 hover:ring-[#00a63e]"
                    }`}
                  >
                    Safe
                  </button>
                </div>
              </div>

              {/* Category with search */}
              <div>
                <p className="text-sm font-medium text-black mb-3">Category</p>
                <div className="relative mb-3">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#938d7a]" />
                  <input
                    type="text"
                    placeholder="Search categories..."
                    value={categorySearch}
                    onChange={(e) => setCategorySearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-[#cecabf] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#938d7a]/20"
                  />
                </div>
                <div className="space-y-2 max-h-40 overflow-y-auto border border-[#cecabf] rounded-lg p-2">
                  {filteredCategories.length === 0 ? (
                    <p className="text-sm text-[#938d7a] text-center py-2">No categories found</p>
                  ) : (
                    filteredCategories.map((category) => (
                      <button
                        key={category}
                        onClick={() => toggleCategory(category)}
                        className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                          selectedCategories.includes(category)
                            ? "bg-[#cecabf] text-black font-medium"
                            : "hover:bg-[#f8f5ee] text-[#938d7a]"
                        }`}
                      >
                        {category}
                      </button>
                    ))
                  )}
                </div>
              </div>
            </div>

            <div className="mb-6">
              <p className="text-sm font-medium text-black mb-3">Sort By</p>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setSortBy(sortBy === "name-asc" ? "name-desc" : "name-asc")}
                  className={`flex items-center justify-between px-4 py-2 rounded-lg text-sm transition-colors ${
                    sortBy === "name-asc" || sortBy === "name-desc"
                      ? "bg-[#cecabf] text-black ring-2 ring-[#938d7a]"
                      : "bg-[#f8f5ee] text-[#938d7a] hover:bg-[#efece3]"
                  }`}
                >
                  <span>Product Name</span>
                  <ArrowUpDown className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setSortBy(sortBy === "quantity-asc" ? "quantity-desc" : "quantity-asc")}
                  className={`flex items-center justify-between px-4 py-2 rounded-lg text-sm transition-colors ${
                    sortBy === "quantity-asc" || sortBy === "quantity-desc"
                      ? "bg-[#cecabf] text-black ring-2 ring-[#938d7a]"
                      : "bg-[#f8f5ee] text-[#938d7a] hover:bg-[#efece3]"
                  }`}
                >
                  <span>Stock Quantity</span>
                  <ArrowUpDown className="w-4 h-4" />
                </button>
              </div>
              {sortBy !== "none" && (
                <p className="text-xs text-[#938d7a] mt-2">
                  Sorting by {sortBy.includes("name") ? "product name" : "stock quantity"} (
                  {sortBy.includes("asc") ? "ascending" : "descending"})
                </p>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setSelectedStatuses([])
                  setSelectedCategories([])
                  setCategorySearch("")
                  setSortBy("none")
                }}
                className="px-4 py-2 border border-[#cecabf] rounded-lg hover:bg-[#f8f5ee] transition-colors"
              >
                Reset
              </button>
              <button
                onClick={exportToCSV}
                className="px-4 py-2 border border-[#cecabf] rounded-lg hover:bg-[#f8f5ee] transition-colors"
              >
                Export Excel
              </button>
              <button
                onClick={() => setShowFilterModal(false)}
                className="flex-1 px-4 py-2 bg-[#cecabf] text-black rounded-lg hover:bg-[#938d7a] hover:text-white transition-colors"
              >
                Apply Filters
              </button>
            </div>
          </div>
        </div>
      )}

      {isPreviousStockModalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-xl p-6 relative">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-black">Upload Previous Stock</h3>
              <button
                onClick={() => {
                  setIsPreviousStockModalOpen(false)
                }}
                className="text-[#938d7a] hover:text-black transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mb-6">
              <div className="border-2 border-dashed border-[#cecabf] rounded-lg p-8">
                <div className="flex flex-col items-center justify-center gap-3">
                  <CloudUpload className="w-16 h-16 text-[#cecabf]" />
                  <p className="text-[#938d7a] text-sm">
                    {previousStockFile ? previousStockFile.name : "Upload previous stock data"}
                  </p>
                  <label className="px-4 py-2 bg-white border border-[#cecabf] rounded-lg text-sm font-medium hover:bg-[#f8f5ee] transition-colors cursor-pointer">
                    Browse
                    <input
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={handlePreviousFileChange}
                      className="hidden"
                    />
                  </label>
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <button
                onClick={() => {
                  setIsPreviousStockModalOpen(false)
                }}
                className="flex-1 px-6 py-3 bg-white border border-[#cecabf] rounded-lg text-black font-medium hover:bg-[#f8f5ee] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (previousStockFile) {
                    setIsPreviousStockModalOpen(false)
                    alert("Previous stock file uploaded. Please upload current stock file.")
                  }
                }}
                disabled={!previousStockFile}
                className="flex-1 px-6 py-3 bg-[#cecabf] rounded-lg text-black font-medium hover:bg-[#c5c5c5] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}

      {isCurrentStockModalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-xl p-6 relative">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-black">Upload Current Stock</h3>
              <button
                onClick={() => {
                  setIsCurrentStockModalOpen(false)
                }}
                className="text-[#938d7a] hover:text-black transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mb-6">
              <div className="border-2 border-dashed border-[#cecabf] rounded-lg p-8">
                <div className="flex flex-col items-center justify-center gap-3">
                  <CloudUpload className="w-16 h-16 text-[#cecabf]" />
                  <p className="text-[#938d7a] text-sm">
                    {currentStockFile ? currentStockFile.name : "Upload current stock data"}
                  </p>
                  <label className="px-4 py-2 bg-white border border-[#cecabf] rounded-lg text-sm font-medium hover:bg-[#f8f5ee] transition-colors cursor-pointer">
                    Browse
                    <input type="file" accept=".csv,.xlsx,.xls" onChange={handleCurrentFileChange} className="hidden" />
                  </label>
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <button
                onClick={() => {
                  setIsCurrentStockModalOpen(false)
                }}
                className="flex-1 px-6 py-3 bg-white border border-[#cecabf] rounded-lg text-black font-medium hover:bg-[#f8f5ee] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                disabled={
                  baseStockExists
                    ? !currentStockFile || isUploading
                    : !previousStockFile || !currentStockFile || isUploading
                }
                className="flex-1 px-6 py-3 bg-[#cecabf] rounded-lg text-black font-medium hover:bg-[#c5c5c5] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? "Processing..." : "Upload & Generate Report"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
