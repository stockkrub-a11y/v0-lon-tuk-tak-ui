import { createClient as createSupabaseClient } from "@supabase/supabase-js"

export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ""
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ""

  // Only log in development
  if (process.env.NODE_ENV === "development") {
    console.log("[v0] Initializing Supabase client")
    console.log("[v0] Supabase URL:", supabaseUrl ? "✓ Configured" : "✗ Missing")
    console.log("[v0] Supabase Key:", supabaseKey ? "✓ Configured" : "✗ Missing")
  }

  if (!supabaseUrl || !supabaseKey) {
    if (process.env.NODE_ENV === "development") {
      console.error("[v0] ❌ Supabase credentials missing!")
      console.error("[v0] Environment variables should be set in Vercel project settings")
      console.error("[v0]   NEXT_PUBLIC_SUPABASE_URL")
      console.error("[v0]   NEXT_PUBLIC_SUPABASE_ANON_KEY")
    }
    // Return a dummy client instead of throwing to prevent app crash
    return createSupabaseClient("https://placeholder.supabase.co", "placeholder-key")
  }

  if (process.env.NODE_ENV === "development") {
    console.log("[v0] ✓ Supabase client created successfully")
  }

  return createSupabaseClient(supabaseUrl, supabaseKey)
}

export function getSupabaseClient() {
  return createClient()
}
