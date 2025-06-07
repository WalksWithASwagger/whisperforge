-- Google OAuth Migration for WhisperForge
-- Add columns to support Google OAuth authentication

-- Add Google OAuth columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS google_id TEXT,
ADD COLUMN IF NOT EXISTS avatar_url TEXT,
ADD COLUMN IF NOT EXISTS auth_provider TEXT DEFAULT 'email',
ADD COLUMN IF NOT EXISTS oauth_tokens JSONB DEFAULT '{}';

-- Create index for Google ID lookups
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_auth_provider ON users(auth_provider);

-- Update existing users to have 'email' as auth_provider
UPDATE users SET auth_provider = 'email' WHERE auth_provider IS NULL;

-- Make password nullable for OAuth users
ALTER TABLE users ALTER COLUMN password DROP NOT NULL;

-- Add constraint to ensure either password or OAuth provider is set
ALTER TABLE users ADD CONSTRAINT check_auth_method 
CHECK (
    (password IS NOT NULL AND auth_provider = 'email') OR 
    (google_id IS NOT NULL AND auth_provider = 'google')
);

-- Add unique constraint for Google ID
ALTER TABLE users ADD CONSTRAINT unique_google_id UNIQUE (google_id);

COMMIT; 