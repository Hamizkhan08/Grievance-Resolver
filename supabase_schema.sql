-- Supabase Schema for Agentic Public Grievance Resolver
-- India-specific Public Grievance Management System

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Complaints table
CREATE TABLE IF NOT EXISTS complaints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    description TEXT NOT NULL,
    structured_category VARCHAR(100) NOT NULL,
    location JSONB NOT NULL, -- {country, state, district, city, pincode, address}
    responsible_department VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    urgency VARCHAR(20) NOT NULL,
    sla_deadline TIMESTAMPTZ NOT NULL,
    escalation_level VARCHAR(50) NOT NULL DEFAULT 'none',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    citizen_name VARCHAR(255),
    citizen_email VARCHAR(255),
    citizen_phone VARCHAR(20),
    attachments TEXT[] DEFAULT '{}',
    agent_metadata JSONB DEFAULT '{}'
);

-- Escalations table
CREATE TABLE IF NOT EXISTS escalations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_id UUID NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    escalation_level VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    escalated_to VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_department ON complaints(responsible_department);
CREATE INDEX IF NOT EXISTS idx_complaints_sla_deadline ON complaints(sla_deadline);
CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints(created_at);
CREATE INDEX IF NOT EXISTS idx_escalations_complaint_id ON escalations(complaint_id);
CREATE INDEX IF NOT EXISTS idx_escalations_created_at ON escalations(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_complaints_updated_at
    BEFORE UPDATE ON complaints
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) Policies
ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;
ALTER TABLE escalations ENABLE ROW LEVEL SECURITY;

-- Policy: Citizens can view their own complaints (by email/phone)
CREATE POLICY "Citizens can view own complaints"
    ON complaints FOR SELECT
    USING (
        auth.jwt() ->> 'email' = citizen_email OR
        auth.jwt() ->> 'phone' = citizen_phone
    );

-- Policy: Public can create complaints (for demo purposes)
-- In production, you may want to require authentication
CREATE POLICY "Public can create complaints"
    ON complaints FOR INSERT
    WITH CHECK (true);

-- Policy: Service role can insert (for backend operations)
CREATE POLICY "Service role can insert complaints"
    ON complaints FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

-- Policy: Admins can view all complaints
-- Note: Configure admin role in Supabase Auth
CREATE POLICY "Admins can view all complaints"
    ON complaints FOR SELECT
    USING (
        auth.jwt() ->> 'role' = 'admin'
    );

-- Policy: Service role can do everything (for backend operations)
CREATE POLICY "Service role full access complaints"
    ON complaints FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Similar policies for escalations
CREATE POLICY "Citizens can view own escalations"
    ON escalations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM complaints
            WHERE complaints.id = escalations.complaint_id
            AND (
                complaints.citizen_email = auth.jwt() ->> 'email' OR
                complaints.citizen_phone = auth.jwt() ->> 'phone'
            )
        )
    );

CREATE POLICY "Admins can view all escalations"
    ON escalations FOR SELECT
    USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Service role full access escalations"
    ON escalations FOR ALL
    USING (auth.role() = 'service_role');

-- View for complaint status (simplified for API)
CREATE OR REPLACE VIEW complaint_status_view AS
SELECT
    id,
    status,
    escalation_level,
    responsible_department,
    sla_deadline,
    created_at,
    updated_at,
    EXTRACT(EPOCH FROM (sla_deadline - NOW())) / 3600 AS time_remaining_hours
FROM complaints;

-- Function to get complaint metrics
CREATE OR REPLACE FUNCTION get_complaint_metrics()
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_complaints', COUNT(*),
        'open', COUNT(*) FILTER (WHERE status = 'open'),
        'in_progress', COUNT(*) FILTER (WHERE status = 'in_progress'),
        'resolved', COUNT(*) FILTER (WHERE status = 'resolved'),
        'escalated', COUNT(*) FILTER (WHERE status = 'escalated'),
        'sla_breaches', COUNT(*) FILTER (
            WHERE sla_deadline < NOW()
            AND status NOT IN ('resolved', 'closed')
        )
    ) INTO result
    FROM complaints;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

