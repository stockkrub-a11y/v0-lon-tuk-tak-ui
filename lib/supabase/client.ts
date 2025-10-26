import { createBrowserClient } from "@supabase/ssr"

let client: ReturnType<typeof createBrowserClient> | null = null

export function createClient() {
  // Return existing client if already created
  if (client) {
    return client
  }

  // Get environment variables
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  console.log("[v0] Supabase URL:", supabaseUrl ? "✓ Set" : "✗ Missing")
  console.log("[v0] Supabase Key:", supabaseAnonKey ? "✓ Set" : "✗ Missing")

  // Validate environment variables
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "@supabase/ssr: Your project's URL and API key are required to create a Supabase client!\n\n" +
        "Check your Supabase project's API settings to find these values:\n" +
        "https://supabase.com/dashboard/project/_/settings/api",
    )
  }

  // Create and cache the client
  client = createBrowserClient(supabaseUrl, supabaseAnonKey)
  console.log("[v0] Supabase client created successfully")
  return client
}
