-- Migration to fix OAuth password issue
-- Run this in your Supabase SQL editor to allow OAuth users without passwords

-- Make password column nullable
ALTER TABLE users 
ALTER COLUMN password DROP NOT NULL;

-- Optionally add a check constraint to ensure either password exists OR user is OAuth
-- (This allows both email/password users and OAuth users)
-- ALTER TABLE users 
-- ADD CONSTRAINT check_auth_method 
-- CHECK (password IS NOT NULL OR (password IS NULL AND auth.jwt() IS NOT NULL));

-- Update any existing OAuth users that might have failed
-- UPDATE users SET password = NULL WHERE password = '';

-- Verify the change
SELECT column_name, is_nullable, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'password'; 