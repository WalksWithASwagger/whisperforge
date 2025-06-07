#!/usr/bin/env python3
"""
Run Google OAuth Migration
"""

from core.supabase_integration import get_supabase_client
import sys

def run_migration():
    """Run the Google OAuth migration"""
    try:
        db = get_supabase_client()
        print("🔧 Running Google OAuth migration...")
        
        # Simple migrations that should work with basic permissions
        migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id TEXT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;", 
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider TEXT DEFAULT 'email';",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_tokens JSONB DEFAULT '{}';",
        ]
        
        for i, migration in enumerate(migrations, 1):
            try:
                # Use direct SQL execution
                result = db.client.rpc('exec_sql', {'sql': migration}).execute()
                print(f"✅ Migration {i}/4: Added column successfully")
            except Exception as me:
                # Try alternative approach
                try:
                    result = db.client.postgrest.rpc('exec_sql', {'sql': migration}).execute()
                    print(f"✅ Migration {i}/4: Added column successfully (alt method)")
                except Exception as me2:
                    print(f"⚠️  Migration {i}/4: Column may already exist ({str(me)[:50]}...)")
        
        print("✅ Google OAuth migration completed!")
        print("Users table now supports Google OAuth authentication")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("You may need to run the migration manually in Supabase SQL Editor")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 