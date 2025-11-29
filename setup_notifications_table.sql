-- ============================================================================
-- Notifications Table Setup Script
-- ============================================================================
-- Run this SQL in your Supabase SQL Editor to create the notifications table
-- 
-- Instructions:
-- 1. Go to your Supabase project dashboard
-- 2. Navigate to SQL Editor
-- 3. Copy and paste this entire script
-- 4. Click "Run" to execute
-- 5. Restart your backend server

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    reminder_id UUID REFERENCES reminders(id) ON DELETE SET NULL,
    notification_type VARCHAR(20) DEFAULT 'in_app', -- in_app, email, sms
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_category VARCHAR(50) DEFAULT 'reminder', -- reminder, estimated_time, due_date
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_notifications_task_id ON notifications(task_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_category ON notifications(notification_category);

-- Enable Row Level Security
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if it exists (to avoid conflicts)
DROP POLICY IF EXISTS "Allow public access" ON notifications;

-- Create public access policy (for development - remove in production!)
CREATE POLICY "Allow public access" ON notifications
    FOR ALL USING (true) WITH CHECK (true);

-- Verify the table was created
SELECT 
    table_name, 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_name = 'notifications'
ORDER BY ordinal_position;

