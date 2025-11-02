"use client"

import type React from "react"

import { useState, useEffect, useMemo, useCallback, useRef } from "react"
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
type SortOption = "name-asc" | "name-desc" | "quantity-asc" | "quantity-desc" | "none"

interface Notification {
  id: string
  status: NotificationStatus
  title: string
  product: string
  sku: string
  category: string
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
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("")
  const searchDebounceTimer = useRef<NodeJS.Timeout | null>(null)
  const [categorySearch, setCategorySearch] = useState("")
  const [isPreviousStockModalOpen, setIsPreviousStockModalOpen] = useState(false)
  const [isCurrentStockModalOpen, setIsCurrentStockModalOpen] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [previousStockFile, setPreviousStockFile] = useState<File | null>(null)
  const [currentStockFile, setCurrentStockFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [baseStockExists, setBaseStockExists] = useState(false)
  const [checkingBaseStock, setCheckingBaseStock] = useState(true)
  const [isEditingMinStock, setIsEditingMinStock] = useState(false)
  const [isEditingBuffer, setIsEditingBuffer] = useState(false)
  const [editedMinStock, setEditedMinStock] = useState<number>(0)
  const [editedBuffer, setEditedBuffer] = useState<number>(0)
  const [isSaving, setIsSaving] = useState(false)
  const [sortBy, setSortBy] = useState<SortOption>("none")
  const [isFetching, setIsFetching] = useState(false)

  // Rest of your component implementation...
  return (
    <div className="min-h-screen bg-[#f8f5ee]">
      {/* Your full implementation here */}
    </div>
  )
}