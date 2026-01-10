-- Add follow-up tracking fields to complaints table
-- Run this in Supabase SQL Editor to enable follow-up tracking

ALTER TABLE complaints 
ADD COLUMN IF NOT EXISTS last_followup_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS followup_count INTEGER DEFAULT 0;

-- Add index for faster queries on follow-up fields
CREATE INDEX IF NOT EXISTS idx_complaints_last_followup 
ON complaints(last_followup_at) 
WHERE last_followup_at IS NOT NULL;

-- Add comment
COMMENT ON COLUMN complaints.last_followup_at IS 'Timestamp of last follow-up action';
COMMENT ON COLUMN complaints.followup_count IS 'Number of follow-ups performed for this complaint';
