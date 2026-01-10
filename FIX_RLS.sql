-- Fix RLS policies for backend operations
-- Run this in Supabase SQL Editor if you get RLS policy violations

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Service role full access" ON complaints;
DROP POLICY IF EXISTS "Service role can insert complaints" ON complaints;

-- Create service role policies
CREATE POLICY "Service role full access complaints"
    ON complaints FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role can insert complaints"
    ON complaints FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

-- Similar for escalations
DROP POLICY IF EXISTS "Service role full access escalations" ON escalations;

CREATE POLICY "Service role full access escalations"
    ON escalations FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');
