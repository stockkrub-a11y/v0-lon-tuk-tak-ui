import { createClient as createSupabaseClient } from "@supabase/supabase-js"

export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

  console.log("[v0] Initializing Supabase client")
  console.log("[v0] Supabase URL:", supabaseUrl ? "✓ Configured" : "✗ Missing")
  console.log("[v0] Supabase Key:", supabaseKey ? "✓ Configured" : "✗ Missing")

  if (!supabaseUrl || !supabaseKey) {
    console.error("[v0] ❌ Supabase credentials missing!")
    console.error("[v0] Please ensure .env.local file exists with:")
    console.error("[v0]   NEXT_PUBLIC_SUPABASE_URL=https://julumxzweprvvcnealal.supabase.co")
    console.error("[v0]   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key")
    console.error("[v0] Then restart your dev server with: npm run dev")
    throw new Error("Supabase is not configured. Create .env.local file and restart dev server.")
  }

  console.log("[v0] ✓ Supabase client created successfully")
  return createSupabaseClient(supabaseUrl, supabaseKey)
}

export function getSupabaseClient() {
  return createClient()
}
