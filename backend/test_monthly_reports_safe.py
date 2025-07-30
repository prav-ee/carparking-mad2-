#!/usr/bin/env python3
"""
Safe test script for Monthly Report functionality - creates test data in current month
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

def check_existing_data():
    """Check existing data before creating test data"""
    with app.app_context():
        print("🔍 Checking Existing Data")
        print("=" * 30)
        
        # Count existing records
        total_records = ParkingHistory.query.count()
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        current_month_start = datetime(current_year, current_month, 1)
        if current_month == 12:
            current_month_end = datetime(current_year + 1, 1, 1)
        else:
            current_month_end = datetime(current_year, current_month + 1, 1)
        
        current_month_records = ParkingHistory.query.filter(
            ParkingHistory.parking_time >= current_month_start,
            ParkingHistory.parking_time < current_month_end
        ).count()
        
        print(f"Total parking records: {total_records}")
        print(f"Current month ({current_month}/{current_year}) records: {current_month_records}")
        
        if current_month_records > 0:
            print(f"⚠️  You already have {current_month_records} records in the current month")
            print("   Test data will be added to these existing records")
        
        return total_records, current_month_records

def create_safe_test_data_for_all_users():
    """Create test parking history data for all users in current month with special identifier"""
    with app.app_context():
        print("=== Creating Safe Test Data for All Users (Current Month) ===")
        
        # Check existing data first
        total_records, current_month_records = check_existing_data()
        
        # Ask for confirmation
        if current_month_records > 0:
            print(f"\n⚠️  You already have {current_month_records} records in the current month")
            confirm = input("Do you want to add test data to existing records? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("❌ Test data creation cancelled")
                return False
        
        users = User.query.filter_by(role='user').all()
        parking_lot = ParkingLot.query.first()
        
        if not users or not parking_lot:
            print("❌ Need at least one user and parking lot to create test data")
            return False
        
        # Use current month and year
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        print(f"Creating test data for {current_month}/{current_year} (current month)")
        
        for i, user in enumerate(users):
            print(f"Creating test data for {user.full_name} ({user.email})")
            
            # Get or create a vehicle for the user with TEST prefix
            vehicle = Vehicle.query.filter_by(user_id=user.id, license_plate__like='TEST%').first()
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
            
            # Check if test data already exists for this user in current month
            start_date = datetime(current_year, current_month, 1)
            if current_month == 12:
                end_date = datetime(current_year + 1, 1, 1)
            else:
                end_date = datetime(current_year, current_month + 1, 1)
                
            existing_test_data = ParkingHistory.query.filter(
                ParkingHistory.user_id == user.id,
                ParkingHistory.parking_time >= start_date,
                ParkingHistory.parking_time < end_date,
                ParkingHistory.vehicle_id == vehicle.id
            ).count()
            
            if existing_test_data > 0:
                print(f"⚠️  Test data already exists for {user.full_name} in current month")
                continue
            
            # Create different test parking records for each user (in current month)
            test_records = [
                {
                    'parking_time': datetime(current_year, current_month, 5 + i, 9, 0),
                    'released_time': datetime(current_year, current_month, 5 + i, 17, 0),
                    'total_cost': 80.0 + (i * 10),
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

def cleanup_test_data():
    """Clean up test data created by this script (TEST vehicles)"""
    with app.app_context():
        print("\n=== Cleaning Up Test Data ===")
        
        # Find all vehicles with TEST prefix
        test_vehicles = Vehicle.query.filter(Vehicle.license_plate.like('TEST%')).all()
        
        if not test_vehicles:
            print("No test vehicles found")
            return
        
        deleted_count = 0
        for vehicle in test_vehicles:
            # Delete parking history for this test vehicle
            vehicle_deleted = ParkingHistory.query.filter_by(vehicle_id=vehicle.id).delete()
            deleted_count += vehicle_deleted
            print(f"Deleted {vehicle_deleted} records for vehicle {vehicle.license_plate}")
            
            # Delete the test vehicle
            db.session.delete(vehicle)
        
        db.session.commit()
        print(f"✅ Deleted {deleted_count} test records and {len(test_vehicles)} test vehicles")

def main():
    """Main test function"""
    print("📊 Safe Monthly Report System Test")
    print("=" * 50)
    print("⚠️  This script creates test data in the current month with TEST vehicles")
    print("⚠️  Use cleanup_test_data() to remove test data when done")
    
    # Check if specific user email is provided as argument
    if len(sys.argv) > 1:
        specific_email = sys.argv[1]
        test_specific_user_email(specific_email)
        return
    
    # Check existing data first
    check_existing_data()
    
    # Ask user what to do
    print("\nOptions:")
    print("1. Create test data and run all tests")
    print("2. Run tests only (no new test data)")
    print("3. Clean up test data only")
    print("4. Check existing data only")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        # Create safe test data for all users
        data_created = create_safe_test_data_for_all_users()
        
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
            
            print("\n🎉 Safe monthly report system test completed!")
            print("💡 Use cleanup_test_data() to remove test data when done")
        else:
            print("❌ Could not create test data. Please ensure you have users and parking lots in the database.")
    
    elif choice == "2":
        # Run tests only
        report_ok = test_monthly_report_generation_for_all_users()
        email_ok = test_monthly_report_email_for_all_users()
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print(f"   - Report generation: {'✅' if report_ok else '❌'}")
        print(f"   - Email sending: {'✅' if email_ok else '❌'}")
    
    elif choice == "3":
        cleanup_test_data()
    
    elif choice == "4":
        check_existing_data()
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main() 