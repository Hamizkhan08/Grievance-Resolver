-- Forum and Voting System for Public Grievance Resolver
-- Allows citizens to discuss and upvote similar incidents

-- Forum Posts table (for discussions on complaints)
CREATE TABLE IF NOT EXISTS forum_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_id UUID NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    content TEXT NOT NULL,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Votes table (tracks who voted on what)
CREATE TABLE IF NOT EXISTS votes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_id UUID NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    voter_email VARCHAR(255) NOT NULL,
    vote_type VARCHAR(10) NOT NULL CHECK (vote_type IN ('upvote', 'downvote')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(complaint_id, voter_email, vote_type)
);

-- Complaint upvotes tracking (aggregated for performance)
ALTER TABLE complaints 
ADD COLUMN IF NOT EXISTS upvote_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS forum_post_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS community_priority_boost FLOAT DEFAULT 0.0;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_forum_posts_complaint_id ON forum_posts(complaint_id);
CREATE INDEX IF NOT EXISTS idx_forum_posts_created_at ON forum_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_votes_complaint_id ON votes(complaint_id);
CREATE INDEX IF NOT EXISTS idx_votes_voter_email ON votes(voter_email);
CREATE INDEX IF NOT EXISTS idx_complaints_upvote_count ON complaints(upvote_count);
CREATE INDEX IF NOT EXISTS idx_complaints_community_priority ON complaints(community_priority_boost);

-- Function to update complaint upvote count
CREATE OR REPLACE FUNCTION update_complaint_upvote_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE complaints
    SET upvote_count = (
        SELECT COUNT(*) 
        FROM votes 
        WHERE complaint_id = NEW.complaint_id 
        AND vote_type = 'upvote'
    ) - (
        SELECT COUNT(*) 
        FROM votes 
        WHERE complaint_id = NEW.complaint_id 
        AND vote_type = 'downvote'
    ),
    community_priority_boost = LEAST(
        (SELECT COUNT(*) FROM votes WHERE complaint_id = NEW.complaint_id AND vote_type = 'upvote')::FLOAT / 10.0,
        1.0
    )
    WHERE id = NEW.complaint_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update upvote count
CREATE TRIGGER update_complaint_upvotes
    AFTER INSERT OR UPDATE OR DELETE ON votes
    FOR EACH ROW
    EXECUTE FUNCTION update_complaint_upvote_count();

-- Function to update forum post count
CREATE OR REPLACE FUNCTION update_forum_post_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE complaints
    SET forum_post_count = (
        SELECT COUNT(*) 
        FROM forum_posts 
        WHERE complaint_id = NEW.complaint_id
    )
    WHERE id = NEW.complaint_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update forum post count
CREATE TRIGGER update_forum_post_count_trigger
    AFTER INSERT OR DELETE ON forum_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_forum_post_count();

-- Row Level Security for forum
ALTER TABLE forum_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE votes ENABLE ROW LEVEL SECURITY;

-- Policy: Public can view forum posts
CREATE POLICY "Public can view forum posts"
    ON forum_posts FOR SELECT
    USING (true);

-- Policy: Public can create forum posts
CREATE POLICY "Public can create forum posts"
    ON forum_posts FOR INSERT
    WITH CHECK (true);

-- Policy: Service role full access
CREATE POLICY "Service role full access forum_posts"
    ON forum_posts FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Policy: Public can view votes
CREATE POLICY "Public can view votes"
    ON votes FOR SELECT
    USING (true);

-- Policy: Public can create votes
CREATE POLICY "Public can create votes"
    ON votes FOR INSERT
    WITH CHECK (true);

-- Policy: Service role full access votes
CREATE POLICY "Service role full access votes"
    ON votes FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');
