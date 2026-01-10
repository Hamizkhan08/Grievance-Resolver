-- Add image support to forum posts
-- Run this migration after ADD_FORUM_TABLES.sql

-- Add image_urls column to store image URLs or base64 data
ALTER TABLE forum_posts 
ADD COLUMN IF NOT EXISTS image_urls JSONB DEFAULT '[]'::jsonb;

-- Add index for image queries (optional, for performance)
CREATE INDEX IF NOT EXISTS idx_forum_posts_has_images 
ON forum_posts USING GIN (image_urls) 
WHERE jsonb_array_length(image_urls) > 0;
