// Script to execute RLS setup SQL against Supabase database
import { createClient } from '@supabase/supabase-js'
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// Get Supabase credentials from environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('❌ Missing Supabase credentials!')
  console.error('Required environment variables:')
  console.error('  - NEXT_PUBLIC_SUPABASE_URL')
  console.error('  - SUPABASE_SERVICE_ROLE_KEY')
  process.exit(1)
}

console.log('[v0] Initializing Supabase client with service role key...')

// Create Supabase client with service role key (has admin privileges)
const supabase = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
})

console.log('[v0] Reading SQL file...')

// Read the SQL file
const sqlFilePath = join(__dirname, '001_setup_rls_policies.sql')
const sqlContent = readFileSync(sqlFilePath, 'utf-8')

console.log('[v0] Executing SQL commands...')
console.log('---')

// Split SQL into individual statements and execute them
const statements = sqlContent
  .split(';')
  .map(s => s.trim())
  .filter(s => s.length > 0 && !s.startsWith('--'))

let successCount = 0
let errorCount = 0

for (const statement of statements) {
  if (statement.includes('--')) {
    // Skip comments
    continue
  }
  
  try {
    const { data, error } = await supabase.rpc('exec_sql', { 
      sql_query: statement 
    })
    
    if (error) {
      // Try direct execution if RPC doesn't exist
      const { error: directError } = await supabase
        .from('_sql')
        .select('*')
        .limit(0)
      
      console.log(`⚠️  Note: Direct SQL execution not available via client`)
      console.log(`   You'll need to run the SQL manually in Supabase dashboard`)
      break
    }
    
    successCount++
    console.log(`✓ Executed statement ${successCount}`)
  } catch (err) {
    errorCount++
    console.error(`✗ Error executing statement:`, err.message)
  }
}

console.log('---')
console.log(`[v0] Setup complete!`)
console.log(`   Success: ${successCount} statements`)
console.log(`   Errors: ${errorCount} statements`)

if (errorCount === 0 && successCount > 0) {
  console.log('\n✅ RLS policies updated successfully!')
  console.log('   Refresh your app to see the changes.')
} else {
  console.log('\n⚠️  Could not execute SQL via client.')
  console.log('   Please run the SQL manually:')
  console.log('   1. Go to Supabase Dashboard → SQL Editor')
  console.log('   2. Copy the contents of scripts/001_setup_rls_policies.sql')
  console.log('   3. Paste and run in the SQL Editor')
}
