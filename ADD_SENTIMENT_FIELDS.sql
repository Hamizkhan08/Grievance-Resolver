-- Add sentiment analysis fields to complaints table
ALTER TABLE complaints 
ADD COLUMN IF NOT EXISTS sentiment_score FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS emotion_level VARCHAR(50) DEFAULT 'calm',
ADD COLUMN IF NOT EXISTS urgency_boost FLOAT DEFAULT 0.0;

-- Add index for sentiment-based queries
CREATE INDEX IF NOT EXISTS idx_complaints_sentiment ON complaints(sentiment_score);
CREATE INDEX IF NOT EXISTS idx_complaints_emotion ON complaints(emotion_level);

-- Add comment for documentation
COMMENT ON COLUMN complaints.sentiment_score IS 'Sentiment score from -1.0 (very negative) to 1.0 (very positive)';
COMMENT ON COLUMN complaints.emotion_level IS 'Emotional state: calm, concerned, frustrated, angry, urgent';
COMMENT ON COLUMN complaints.urgency_boost IS 'Additional urgency boost (0.0 to 1.0) based on emotional state';
