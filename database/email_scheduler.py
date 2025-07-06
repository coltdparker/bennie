import os
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .connection import SessionLocal
from .crud import EmailScheduleCRUD, UserCRUD, EmailLogCRUD
from .models import EmailSchedule, User
from Backend.bennie_email_sender import send_language_learning_email

load_dotenv()

class EmailScheduler:
    """Handles automated email scheduling and sending."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    def get_users_for_scheduled_emails(self, day_of_week: int, time_of_day: str) -> List[User]:
        """
        Get all users who should receive emails at a specific time.
        
        Args:
            day_of_week: 0=Monday, 1=Tuesday, ..., 6=Sunday
            time_of_day: "08:00" format
        """
        schedules = EmailScheduleCRUD.get_schedules_for_time(self.db, day_of_week, time_of_day)
        user_ids = [schedule.user_id for schedule in schedules]
        
        if not user_ids:
            return []
        
        users = []
        for user_id in user_ids:
            user = UserCRUD.get_user_by_id(self.db, user_id)
            if user and user.is_active:
                users.append(user)
        
        return users
    
    def send_scheduled_emails(self, day_of_week: int, time_of_day: str) -> dict:
        """
        Send scheduled emails to all users for a specific time.
        
        Returns:
            dict: Summary of email sending results
        """
        users = self.get_users_for_scheduled_emails(day_of_week, time_of_day)
        
        results = {
            "total_users": len(users),
            "successful_sends": 0,
            "failed_sends": 0,
            "errors": []
        }
        
        for user in users:
            try:
                success = self.send_practice_email_to_user(user)
                if success:
                    results["successful_sends"] += 1
                else:
                    results["failed_sends"] += 1
            except Exception as e:
                results["failed_sends"] += 1
                results["errors"].append(f"User {user.id}: {str(e)}")
        
        return results
    
    def send_practice_email_to_user(self, user: User) -> bool:
        """
        Send a practice email to a specific user.
        
        Returns:
            bool: True if email was sent successfully
        """
        try:
            # Send the email using the existing email sender
            send_language_learning_email(
                user_name=user.name,
                user_email=user.email,
                user_language=user.target_language.value,
                user_level=user.proficiency_level
            )
            
            # Log the email
            EmailLogCRUD.log_email(
                db=self.db,
                user_id=user.id,
                email_type="practice",
                subject=f"Practice Email - {user.target_language.value.title()}",
                content="Practice email content",  # This would be the actual content
                status="sent"
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to send email to {user.email}: {e}")
            
            # Log the failed email
            EmailLogCRUD.log_email(
                db=self.db,
                user_id=user.id,
                email_type="practice",
                subject=f"Practice Email - {user.target_language.value.title()}",
                content="Failed to send",
                status="failed"
            )
            
            return False
    
    def setup_default_schedules(self, user_id: int) -> bool:
        """
        Set up default email schedules for a new user (Monday, Wednesday, Friday at 8 AM).
        
        Args:
            user_id: The user ID to set up schedules for
            
        Returns:
            bool: True if schedules were created successfully
        """
        try:
            # Monday = 0, Wednesday = 2, Friday = 4
            default_days = [0, 2, 4]  # Monday, Wednesday, Friday
            default_time = "08:00"
            
            for day in default_days:
                EmailScheduleCRUD.create_schedule(
                    db=self.db,
                    user_id=user_id,
                    day_of_week=day,
                    time_of_day=default_time
                )
            
            return True
            
        except Exception as e:
            print(f"Failed to set up default schedules for user {user_id}: {e}")
            return False
    
    def update_user_schedule(
        self,
        user_id: int,
        schedules: List[dict]
    ) -> bool:
        """
        Update a user's email schedule.
        
        Args:
            user_id: The user ID
            schedules: List of schedule dictionaries with 'day_of_week' and 'time_of_day'
            
        Returns:
            bool: True if schedules were updated successfully
        """
        try:
            # Remove existing schedules
            existing_schedules = EmailScheduleCRUD.get_user_schedules(self.db, user_id)
            for schedule in existing_schedules:
                schedule.is_active = False
                self.db.commit()
            
            # Create new schedules
            for schedule_data in schedules:
                EmailScheduleCRUD.create_schedule(
                    db=self.db,
                    user_id=user_id,
                    day_of_week=schedule_data["day_of_week"],
                    time_of_day=schedule_data["time_of_day"]
                )
            
            return True
            
        except Exception as e:
            print(f"Failed to update schedules for user {user_id}: {e}")
            return False
    
    def get_next_email_time(self, user_id: int) -> Optional[datetime]:
        """
        Get the next scheduled email time for a user.
        
        Returns:
            datetime: Next email time or None if no schedules
        """
        schedules = EmailScheduleCRUD.get_user_schedules(self.db, user_id)
        if not schedules:
            return None
        
        now = datetime.now()
        next_times = []
        
        for schedule in schedules:
            if not schedule.is_active:
                continue
                
            # Calculate next occurrence of this schedule
            next_time = self._calculate_next_schedule_time(
                schedule.day_of_week,
                schedule.time_of_day,
                now
            )
            next_times.append(next_time)
        
        return min(next_times) if next_times else None
    
    def _calculate_next_schedule_time(
        self,
        day_of_week: int,
        time_of_day: str,
        from_time: datetime
    ) -> datetime:
        """
        Calculate the next occurrence of a weekly schedule.
        
        Args:
            day_of_week: 0=Monday, 1=Tuesday, ..., 6=Sunday
            time_of_day: "08:00" format
            from_time: Starting time to calculate from
            
        Returns:
            datetime: Next occurrence of the schedule
        """
        # Parse time
        hour, minute = map(int, time_of_day.split(":"))
        
        # Get current day of week (0=Monday)
        current_day = from_time.weekday()
        
        # Calculate days until next occurrence
        days_ahead = day_of_week - current_day
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        # Calculate next occurrence
        next_date = from_time.date() + timedelta(days=days_ahead)
        next_time = datetime.combine(next_date, datetime.min.time().replace(hour=hour, minute=minute))
        
        return next_time

# Utility function for running scheduled emails
def run_scheduled_emails():
    """
    Main function to run scheduled emails.
    This should be called by a cron job or scheduler.
    """
    scheduler = EmailScheduler()
    
    # Get current time
    now = datetime.now()
    day_of_week = now.weekday()  # 0=Monday, 1=Tuesday, etc.
    time_of_day = now.strftime("%H:%M")
    
    print(f"Running scheduled emails for {day_of_week} at {time_of_day}")
    
    # Send emails for current time
    results = scheduler.send_scheduled_emails(day_of_week, time_of_day)
    
    print(f"Email sending complete:")
    print(f"  Total users: {results['total_users']}")
    print(f"  Successful: {results['successful_sends']}")
    print(f"  Failed: {results['failed_sends']}")
    
    if results['errors']:
        print("Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    return results

if __name__ == "__main__":
    # Test the scheduler
    run_scheduled_emails() 