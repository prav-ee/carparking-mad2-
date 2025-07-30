#!/usr/bin/env python3
"""
Test script for daily reminder functionality
"""
import os
import sys
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db, mail
from models.user import User
from models.parking_lot import ParkingLot
from models.parking_history import ParkingHistory
from models.base import AppConfig
from tasks import send_daily_email_reminders, send_reminder_email

def test_reminder_system():
    """Test the daily reminder system"""
    with app.app_context():
        print("=== Testing Daily Reminder System ===\n")
        
        # 1. Check if parking lots exist
        parking_lots = ParkingLot.query.all()
        print(f"1. Parking lots found: {len(parking_lots)}")
        for lot in parking_lots:
            print(f"   - {lot.name} (Active: {lot.is_active})")
        
        # 2. Check users
        users = User.query.filter_by(role='user').all()
        print(f"\n2. Users found: {len(users)}")
        for user in users:
            print(f"   - {user.full_name} ({user.email})")
        
        # 3. Check today's parking activity
        today = datetime.now().date()
        users_parked_today = ParkingHistory.query.filter(
            ParkingHistory.parking_time >= datetime.combine(today, datetime.min.time()),
            ParkingHistory.parking_time < datetime.combine(today + timedelta(days=1), datetime.min.time())
        ).distinct(ParkingHistory.user_id).count()
        
        print(f"\n3. Users who parked today: {users_parked_today}")
        print(f"   Users who didn't park today: {len(users) - users_parked_today}")
        
        # 4. Check reminder time configuration
        hour_cfg = AppConfig.query.filter_by(key='reminder_hour').first()
        min_cfg = AppConfig.query.filter_by(key='reminder_minute').first()
        reminder_hour = int(hour_cfg.value) if hour_cfg else 18
        reminder_minute = int(min_cfg.value) if min_cfg else 0
        
        print(f"\n4. Reminder time configured: {reminder_hour:02d}:{reminder_minute:02d}")
        
        # 5. Test individual reminder emails for all users
        print(f"\n5. Testing reminder emails for all users:")
        success_count = 0
        for user in users:
            print(f"\n   Testing for: {user.full_name} ({user.email})")
            
            # Check if user has active session
            active_session = ParkingHistory.query.filter(
                ParkingHistory.user_id == user.id,
                ParkingHistory.released_time.is_(None)
            ).first()
            
            print(f"   Has active session: {active_session is not None}")
            
            # Test sending reminder email
            try:
                result = send_reminder_email(user.id)
                print(f"   Email result: {result}")
                success_count += 1
            except Exception as e:
                print(f"   Email error: {str(e)}")
        
        print(f"\n📧 Successfully sent emails to {success_count}/{len(users)} users")
        
        # 6. Test daily reminder function
        print(f"\n6. Testing daily reminder function...")
        try:
            result = send_daily_email_reminders()
            print(f"   Daily reminder result: {result}")
        except Exception as e:
            print(f"   Daily reminder error: {str(e)}")
        
        print("\n=== Test Complete ===")

def test_specific_user_reminder(user_email):
    """Test sending reminder to a specific user"""
    with app.app_context():
        print(f"=== Testing Daily Reminder for Specific User: {user_email} ===")
        
        user = User.query.filter_by(email=user_email).first()
        if not user:
            print(f"❌ User with email {user_email} not found")
            return False
        
        # Check if user has active session
        active_session = ParkingHistory.query.filter(
            ParkingHistory.user_id == user.id,
            ParkingHistory.released_time.is_(None)
        ).first()
        
        print(f"User: {user.full_name} ({user.email})")
        print(f"Has active session: {active_session is not None}")
        
        # Test sending reminder email
        try:
            result = send_reminder_email(user.id)
            print(f"✅ Reminder email sent successfully")
            print(f"Result: {result}")
            return True
        except Exception as e:
            print(f"❌ Email error: {str(e)}")
            return False

def main():
    """Main function"""
    # Check if specific user email is provided as argument
    if len(sys.argv) > 1:
        specific_email = sys.argv[1]
        test_specific_user_reminder(specific_email)
        return
    
    # Test all users
    test_reminder_system()

if __name__ == "__main__":
    main() 