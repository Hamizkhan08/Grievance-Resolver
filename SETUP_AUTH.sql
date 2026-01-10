-- Setup Authentication and Admin User
-- This script sets up Supabase Auth and creates the admin user

-- Note: The admin user (resolvergrievance@gmail.com) should be created through Supabase Dashboard
-- Go to Authentication > Users > Add User
-- Email: resolvergrievance@gmail.com
-- Password: 123456789
-- Auto Confirm User: Yes

-- Alternatively, you can use the Supabase Management API or create the user programmatically
-- The role is determined by email in the AuthContext.jsx file

-- If you want to store user roles in a separate table, you can create this:
CREATE TABLE IF NOT EXISTS user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('admin', 'citizen')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id),
  UNIQUE(email)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_roles_email ON user_roles(email);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);

-- Enable RLS
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own role
CREATE POLICY "Users can read own role"
  ON user_roles
  FOR SELECT
  USING (auth.uid() = user_id);

-- Policy: Service role can do everything
CREATE POLICY "Service role full access user_roles"
  ON user_roles
  FOR ALL
  USING (auth.role() = 'service_role');

-- Insert admin user role (after creating the user in Supabase Auth)
-- Replace 'USER_UUID_HERE' with the actual UUID from auth.users table
-- INSERT INTO user_roles (user_id, email, role)
-- VALUES ('USER_UUID_HERE', 'resolvergrievance@gmail.com', 'admin')
-- ON CONFLICT (email) DO UPDATE SET role = 'admin';

-- Note: The current implementation uses email-based role checking in AuthContext.jsx
-- This is simpler and doesn't require database queries
-- If you want to use the database approach, update AuthContext.jsx to query this table
