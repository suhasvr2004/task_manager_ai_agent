-- ============================================================================
-- Task Manager Agent - Supabase Database Schema
-- ============================================================================
-- Run this SQL in your Supabase SQL Editor to create the required tables

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'pending',
    due_date TIMESTAMP,
    estimated_hours FLOAT,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL,
    assigned_to UUID
);

-- Reminders table
CREATE TABLE IF NOT EXISTS reminders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    reminder_time TIMESTAMP NOT NULL,
    notification_type VARCHAR(20) DEFAULT 'email',
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Calendar events table
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    calendar_id VARCHAR(255),
    event_id VARCHAR(255),
    title VARCHAR(255),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    synced_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_reminders_task_id ON reminders(task_id);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status);

-- Enable Row Level Security (optional, adjust policies as needed)
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow all operations (adjust for your security needs)
-- For development, you can use this permissive policy:
CREATE POLICY "Allow all operations for authenticated users" ON tasks
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations for authenticated users" ON reminders
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations for authenticated users" ON calendar_events
    FOR ALL USING (true) WITH CHECK (true);

-- Or for public access (development only):
-- DROP POLICY IF EXISTS "Allow all operations for authenticated users" ON tasks;
-- DROP POLICY IF EXISTS "Allow all operations for authenticated users" ON reminders;
-- DROP POLICY IF EXISTS "Allow all operations for authenticated users" ON calendar_events;

-- Allow public access (for development - remove in production!)
CREATE POLICY "Allow public access" ON tasks
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow public access" ON reminders
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow public access" ON calendar_events
    FOR ALL USING (true) WITH CHECK (true);

