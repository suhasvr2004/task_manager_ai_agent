"""Reminder scheduler service for checking and sending reminder notifications"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from backend.database.client import DatabaseManager
from backend.config import get_settings
from loguru import logger
import asyncio

class ReminderScheduler:
    """Service to check and process reminders"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_manager = DatabaseManager()
        self.scheduler = None
        self._running = False
    
    async def check_and_send_reminders(self):
        """Check for due reminders and estimated time completions, then send notifications"""
        try:
            now = datetime.now()
            
            # 1. Check for due reminders (optimized query with index)
            try:
                # Use indexed columns: status and reminder_time
                response = self.db_manager.supabase.client.table("reminders").select(
                    "id, task_id, reminder_time, notification_type, status"
                ).eq("status", "pending").lte("reminder_time", now.isoformat()).limit(100).execute()
                
                reminders = response.data or []
                
                if reminders:
                    logger.info(f"Found {len(reminders)} due reminder(s)")
                    # Process reminders sequentially to avoid overwhelming the database
                    for reminder in reminders:
                        await self._send_reminder_notification(reminder)
            except Exception as e:
                error_str = str(e).lower()
                if "does not exist" in error_str or "not found" in error_str or "schema cache" in error_str:
                    logger.debug("Reminders table not found (expected if not set up)")
                else:
                    logger.warning(f"Error checking reminders: {str(e)}")
            
            # 2. Check for estimated time completions
            await self._check_estimated_time_completions(now)
                
        except Exception as e:
            logger.error(f"Error in check_and_send_reminders: {str(e)}")
    
    async def _send_reminder_notification(self, reminder: Dict[str, Any]):
        """Send a reminder notification and store it in the database"""
        try:
            reminder_id = reminder.get("id")
            task_id = reminder.get("task_id")
            
            # Get task details
            task_response = self.db_manager.supabase.client.table("tasks").select(
                "id, title, description, due_date, priority"
            ).eq("id", task_id).execute()
            
            if not task_response.data:
                logger.warning(f"Task {task_id} not found for reminder {reminder_id}")
                self._update_reminder_status(reminder_id, "failed")
                return
            
            task = task_response.data[0]
            task_title = task.get("title", "Untitled Task")
            notification_type = reminder.get("notification_type", "in_app")
            
            # Store notification in database
            await self._create_notification(
                task_id=task_id,
                reminder_id=reminder_id,
                notification_type=notification_type,
                title=f"Reminder: {task_title}",
                message=f"Time to work on: {task_title}",
                category="reminder"
            )
            
            # Mark reminder as sent
            self._update_reminder_status(reminder_id, "sent")
            logger.info(f"✅ Reminder notification created for task: {task_title}")
            
        except Exception as e:
            logger.error(f"Error sending reminder notification: {str(e)}")
            try:
                self._update_reminder_status(reminder.get("id"), "failed")
            except:
                pass
    
    async def _check_estimated_time_completions(self, now: datetime):
        """Check for tasks that have reached their estimated completion time"""
        try:
            # Get all in_progress tasks with estimated_hours
            response = self.db_manager.supabase.client.table("tasks").select(
                "id, title, description, estimated_hours, created_at, updated_at, status"
            ).eq("status", "in_progress").not_.is_("estimated_hours", "null").gt("estimated_hours", 0).execute()
            
            tasks = response.data or []
            
            for task in tasks:
                task_id = task.get("id")
                task_title = task.get("title", "Untitled Task")
                estimated_hours = task.get("estimated_hours", 0)
                
                if not estimated_hours or estimated_hours <= 0:
                    continue
                
                # Use updated_at if available, otherwise created_at
                start_time_str = task.get("updated_at") or task.get("created_at")
                if not start_time_str:
                    continue
                
                try:
                    # Parse the timestamp
                    if isinstance(start_time_str, str):
                        if 'T' in start_time_str:
                            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        else:
                            start_time = datetime.fromisoformat(start_time_str)
                    else:
                        start_time = start_time_str
                    
                    # Remove timezone for comparison
                    if start_time.tzinfo:
                        start_time = start_time.replace(tzinfo=None)
                    
                    # Calculate expected completion time
                    expected_completion = start_time + timedelta(hours=estimated_hours)
                    
                    # Check if estimated time has passed (with 1 minute buffer)
                    if now >= expected_completion - timedelta(minutes=1):
                        # Check if we already sent a notification for this task
                        existing_notif = self.db_manager.supabase.client.table("notifications").select(
                            "id"
                        ).eq("task_id", task_id).eq("notification_category", "estimated_time").eq("is_read", False).execute()
                        
                        if not existing_notif.data:
                            # Create notification
                            await self._create_notification(
                                task_id=task_id,
                                reminder_id=None,
                                notification_type="in_app",
                                title=f"Estimated Time Complete: {task_title}",
                                message=f"The estimated time ({estimated_hours} hour{'s' if estimated_hours != 1 else ''}) for '{task_title}' has been reached.",
                                category="estimated_time"
                            )
                            logger.info(f"✅ Estimated time notification created for task: {task_title}")
                except Exception as e:
                    logger.warning(f"Error checking estimated time for task {task_id}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error checking estimated time completions (notifications table may not exist): {str(e)}")
    
    async def _create_notification(
        self,
        task_id: str,
        reminder_id: Optional[str],
        notification_type: str,
        title: str,
        message: str,
        category: str
    ):
        """Create a notification in the database"""
        try:
            notification_data = {
                "task_id": task_id,
                "reminder_id": reminder_id,
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "notification_category": category,
                "is_read": False,
                "created_at": datetime.now().isoformat()
            }
            
            # Remove None values
            notification_data = {k: v for k, v in notification_data.items() if v is not None}
            
            self.db_manager.supabase.client.table("notifications").insert(notification_data).execute()
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            # Don't raise - notifications are not critical
    
    def _update_reminder_status(self, reminder_id: str, status: str):
        """Update reminder status"""
        try:
            self.db_manager.supabase.client.table("reminders").update({
                "status": status
            }).eq("id", reminder_id).execute()
        except Exception as e:
            logger.error(f"Error updating reminder status: {str(e)}")
    
    def start(self):
        """Start the reminder scheduler"""
        if self._running:
            logger.warning("Reminder scheduler is already running")
            return
        
        if not self.settings.SCHEDULER_ENABLED:
            logger.info("Reminder scheduler is disabled in settings")
            return
        
        try:
            self.scheduler = AsyncIOScheduler()
            
            # Schedule reminder check job
            interval_minutes = self.settings.REMINDER_CHECK_INTERVAL_MINUTES
            self.scheduler.add_job(
                self.check_and_send_reminders,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id="check_reminders",
                name="Check and send reminders",
                replace_existing=True
            )
            
            self.scheduler.start()
            self._running = True
            logger.info(f"✅ Reminder scheduler started (checking every {interval_minutes} minutes)")
            
        except Exception as e:
            logger.error(f"Error starting reminder scheduler: {str(e)}")
            self._running = False
    
    def stop(self):
        """Stop the reminder scheduler"""
        if self.scheduler and self._running:
            try:
                self.scheduler.shutdown()
                self._running = False
                logger.info("Reminder scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping reminder scheduler: {str(e)}")

# Global scheduler instance
_reminder_scheduler = None

def get_reminder_scheduler() -> ReminderScheduler:
    """Get or create the global reminder scheduler instance"""
    global _reminder_scheduler
    if _reminder_scheduler is None:
        _reminder_scheduler = ReminderScheduler()
    return _reminder_scheduler

