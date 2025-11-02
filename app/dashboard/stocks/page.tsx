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

  // Rest of your component implementation...
  return (
    <div className="min-h-screen bg-[#f8f5ee]">
      {/* Your full implementation here */}
    </div>
  )
}