-- ============================================================================
-- Reminders Table Setup Script
-- ============================================================================
-- Run this SQL in your Supabase SQL Editor to create the reminders table
-- 
-- Instructions:
-- 1. Go to your Supabase project dashboard
-- 2. Navigate to SQL Editor
-- 3. Copy and paste this entire script
-- 4. Click "Run" to execute
-- 5. Restart your backend server

-- Reminders table
CREATE TABLE IF NOT EXISTS reminders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    reminder_time TIMESTAMP NOT NULL,
    notification_type VARCHAR(20) DEFAULT 'in_app',
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reminders_task_id ON reminders(task_id);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status);
CREATE INDEX IF NOT EXISTS idx_reminders_time ON reminders(reminder_time) WHERE status = 'pending';

-- Enable Row Level Security
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if it exists (to avoid conflicts)
DROP POLICY IF EXISTS "Allow public access" ON reminders;
DROP POLICY IF EXISTS "Allow all operations for authenticated users" ON reminders;

-- Create public access policy (for development - remove in production!)
CREATE POLICY "Allow public access" ON reminders
    FOR ALL USING (true) WITH CHECK (true);

-- Verify the table was created
SELECT 
    table_name, 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_name = 'reminders'
ORDER BY ordinal_position;

