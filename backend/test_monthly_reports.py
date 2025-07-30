#!/usr/bin/env python3
"""
Test script for Monthly Report functionality with MailHog
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
from models.parking_spot import ParkingSpot
from models.vehicle import Vehicle
from tasks import send_monthly_report_email, send_all_monthly_reports, generate_monthly_report

def create_test_data_for_all_users():
    """Create test parking history data for all users"""
    with app.app_context():
        print("=== Creating Test Data for All Users ===")
        print("⚠️  WARNING: This will DELETE existing parking history for the current month!")
        print("⚠️  Use test_monthly_reports_safe.py instead to avoid data loss")
        
        # Ask for confirmation
        response = input("Do you want to continue? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            print("❌ Test cancelled by user")
            return False
        
        users = User.query.filter_by(role='user').all()
        parking_lot = ParkingLot.query.first()
        
        if not users or not parking_lot:
            print("❌ Need at least one user and parking lot to create test data")
            return False
        
        # Use current month and year
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        print(f"Creating test data for {current_month}/{current_year}")
        
        for i, user in enumerate(users):
            print(f"Creating test data for {user.full_name} ({user.email})")
            
            # Get or create a vehicle for the user
            vehicle = Vehicle.query.filter_by(user_id=user.id).first()
            if not vehicle:
                vehicle = Vehicle(
                    user_id=user.id,
                    license_plate=f"TEST{i+1}23",
                    vehicle_type="Car"
                )
                db.session.add(vehicle)
                db.session.commit()
            
            # Get or create a parking spot
            spot = ParkingSpot.query.filter_by(lot_id=parking_lot.id).first()
            if not spot:
                spot = ParkingSpot(
                    lot_id=parking_lot.id,
                    spot_number=str(i+1)
                )
                db.session.add(spot)
                db.session.commit()
            
            # Delete existing test records for this month and user
            start_date = datetime(current_year, current_month, 1)
            if current_month == 12:
                end_date = datetime(current_year + 1, 1, 1)
            else:
                end_date = datetime(current_year, current_month + 1, 1)
                
            deleted_count = ParkingHistory.query.filter(
                ParkingHistory.user_id == user.id,
                ParkingHistory.parking_time >= start_date,
                ParkingHistory.parking_time < end_date
            ).delete()
            
            if deleted_count > 0:
                print(f"⚠️  Deleted {deleted_count} existing records for {user.full_name}")
            
            # Create different test parking records for each user
            # Use realistic dates within the current month
            test_records = [
                {
                    'parking_time': datetime(current_year, current_month, 5 + i, 9, 0),  # Different days for each user
                    'released_time': datetime(current_year, current_month, 5 + i, 17, 0),
                    'total_cost': 80.0 + (i * 10),  # Different costs for each user
                    'status': 'out'
                },
                {
                    'parking_time': datetime(current_year, current_month, 12 + i, 10, 0),
                    'released_time': datetime(current_year, current_month, 12 + i, 16, 0),
                    'total_cost': 60.0 + (i * 5),
                    'status': 'out'
                },
                {
                    'parking_time': datetime(current_year, current_month, 20 + i, 8, 0),
                    'released_time': None,  # Active session
                    'total_cost': None,
                    'status': 'active'
                }
            ]
            
            for record_data in test_records:
                history = ParkingHistory(
                    user_id=user.id,
                    vehicle_id=vehicle.id,
                    lot_id=parking_lot.id,
                    spot_id=spot.id,
                    parking_time=record_data['parking_time'],
                    released_time=record_data['released_time'],
                    total_cost=record_data['total_cost'],
                    status=record_data['status']
                )
                db.session.add(history)
            
            print(f"✅ Created {len(test_records)} test parking records for {user.full_name}")
        
        db.session.commit()
        return True

def test_monthly_report_generation_for_all_users():
    """Test monthly report generation for all users"""
    with app.app_context():
        print("\n=== Testing Monthly Report Generation for All Users ===")
        
        users = User.query.filter_by(role='user').all()
        if not users:
            print("❌ No users found")
            return False
        
        success_count = 0
        for user in users:
            try:
                report_data = generate_monthly_report(user.id)
                print(f"✅ Report generated for {user.full_name} ({user.email})")
                print(f"   - Total bookings: {report_data.get('total_bookings', 0)}")
                print(f"   - Total spent: ₹{report_data.get('total_spent', 0):.2f}")
                success_count += 1
            except Exception as e:
                print(f"❌ Report generation failed for {user.full_name}: {str(e)}")
        
        print(f"\n📊 Generated reports for {success_count}/{len(users)} users")
        return success_count == len(users)

def test_monthly_report_email_for_all_users():
    """Test monthly report email sending for all users"""
    with app.app_context():
        print("\n=== Testing Monthly Report Email for All Users ===")
        
        users = User.query.filter_by(role='user').all()
        if not users:
            print("❌ No users found")
            return False
        
        # Use current month and year
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        success_count = 0
        for user in users:
            try:
                result = send_monthly_report_email(user.id, current_month, current_year)
                print(f"✅ Monthly report email sent to {user.full_name} ({user.email})")
                print(f"   - Result: {result}")
                success_count += 1
            except Exception as e:
                print(f"❌ Monthly report email failed for {user.full_name}: {str(e)}")
        
        print(f"\n📧 Sent emails to {success_count}/{len(users)} users")
        return success_count == len(users)

def test_specific_user_email(user_email):
    """Test sending email to a specific user"""
    with app.app_context():
        print(f"\n=== Testing Email for Specific User: {user_email} ===")
        
        user = User.query.filter_by(email=user_email).first()
        if not user:
            print(f"❌ User with email {user_email} not found")
            return False
        
        # Use current month and year
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        try:
            result = send_monthly_report_email(user.id, current_month, current_year)
            print(f"✅ Monthly report email sent to {user.full_name} ({user.email})")
            print(f"   - Result: {result}")
            return True
        except Exception as e:
            print(f"❌ Monthly report email failed: {str(e)}")
            return False

def test_all_monthly_reports():
    """Test sending monthly reports to all users (NOTE: This is redundant with test_monthly_report_email_for_all_users)"""
    with app.app_context():
        print("\n=== Testing All Monthly Reports ===")
        
        users = User.query.filter_by(role='user').all()
        if not users:
            print("❌ No users found")
            return False
        
        # Use current month and year
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        try:
            # Send reports for current month to all users
            success_count = 0
            for user in users:
                try:
                    result = send_monthly_report_email(user.id, current_month, current_year)
                    print(f"✅ Monthly report sent to {user.full_name} ({user.email})")
                    success_count += 1
                except Exception as e:
                    print(f"❌ Failed to send report to {user.full_name}: {str(e)}")
            
            print(f"✅ Monthly reports sent to {success_count}/{len(users)} users")
            return success_count == len(users)
        except Exception as e:
            print(f"❌ All monthly reports failed: {str(e)}")
            return False

def main():
    """Main test function"""
    print("📊 Monthly Report System Test with MailHog")
    print("=" * 50)
    
    # Check if specific user email is provided as argument
    if len(sys.argv) > 1:
        specific_email = sys.argv[1]
        test_specific_user_email(specific_email)
        return
    
    # Create test data for all users
    data_created = create_test_data_for_all_users()
    
    if data_created:
        # Test report generation for all users
        report_ok = test_monthly_report_generation_for_all_users()
        
        # Test email sending for all users (only once to avoid duplicates)
        email_ok = test_monthly_report_email_for_all_users()
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print(f"   - Test data created: {'✅' if data_created else '❌'}")
        print(f"   - Report generation: {'✅' if report_ok else '❌'}")
        print(f"   - Email sending: {'✅' if email_ok else '❌'}")
        
        if email_ok:
            print("\n📧 Check MailHog at http://localhost:8025 to view the monthly report emails!")
        
        print("\n🎉 Monthly report system is ready!")
    else:
        print("❌ Could not create test data. Please ensure you have users and parking lots in the database.")

if __name__ == "__main__":
    main() 