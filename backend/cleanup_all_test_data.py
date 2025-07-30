#!/usr/bin/env python3
"""
Comprehensive cleanup script to remove all test data and restore original state
"""
import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from models.user import User
from models.parking_history import ParkingHistory
from models.vehicle import Vehicle

def cleanup_all_test_data():
    """Remove all test data and restore original state"""
    with app.app_context():
        print("🧹 Comprehensive Test Data Cleanup")
        print("=" * 50)
        
        # 1. Remove all vehicles with TEST prefix
        test_vehicles = Vehicle.query.filter(Vehicle.license_plate.like('TEST%')).all()
        print(f"Found {len(test_vehicles)} test vehicles")
        
        for vehicle in test_vehicles:
            # Delete parking history for this test vehicle
            vehicle_deleted = ParkingHistory.query.filter_by(vehicle_id=vehicle.id).delete()
            print(f"Deleted {vehicle_deleted} records for vehicle {vehicle.license_plate}")
            
            # Delete the test vehicle
            db.session.delete(vehicle)
        
        # 2. Remove all parking history from previous months (likely test data)
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        deleted_count = 0
        for month in range(1, current_month):
            start_date = datetime(current_year, month, 1)
            if month == 12:
                end_date = datetime(current_year + 1, 1, 1)
            else:
                end_date = datetime(current_year, month + 1, 1)
            
            month_deleted = ParkingHistory.query.filter(
                ParkingHistory.parking_time >= start_date,
                ParkingHistory.parking_time < end_date
            ).delete()
            
            if month_deleted > 0:
                print(f"Deleted {month_deleted} records from {month}/{current_year}")
                deleted_count += month_deleted
        
        # 3. Remove data from previous years
        for year in range(current_year - 1, current_year - 5, -1):
            year_deleted = ParkingHistory.query.filter(
                ParkingHistory.parking_time >= datetime(year, 1, 1),
                ParkingHistory.parking_time < datetime(year + 1, 1, 1)
            ).delete()
            
            if year_deleted > 0:
                print(f"Deleted {year_deleted} records from year {year}")
                deleted_count += year_deleted
        
        db.session.commit()
        
        # 4. Show remaining data
        remaining_records = ParkingHistory.query.all()
        print(f"\n📊 Remaining parking records: {len(remaining_records)}")
        
        if remaining_records:
            print("\nRemaining records:")
            for record in remaining_records:
                user = User.query.get(record.user_id)
                vehicle = Vehicle.query.get(record.vehicle_id)
                print(f"  ID: {record.id}, User: {user.full_name if user else 'Unknown'}")
                print(f"    Vehicle: {vehicle.license_plate if vehicle else 'Unknown'}")
                print(f"    Parking: {record.parking_time}")
                print(f"    Status: {record.status}")
                print(f"    Cost: {record.total_cost}")
        
        print(f"\n✅ Cleanup completed! Deleted {deleted_count} test records and {len(test_vehicles)} test vehicles")

def check_current_data():
    """Check what data remains after cleanup"""
    with app.app_context():
        print("\n🔍 Current Data Status")
        print("=" * 30)
        
        # Get all parking history records
        all_records = ParkingHistory.query.order_by(ParkingHistory.parking_time.desc()).all()
        
        print(f"Total records: {len(all_records)}")
        
        if all_records:
            print("\nCurrent records:")
            for record in all_records:
                user = User.query.get(record.user_id)
                vehicle = Vehicle.query.get(record.vehicle_id)
                print(f"  ID: {record.id}")
                print(f"    User: {user.full_name if user else 'Unknown'}")
                print(f"    Vehicle: {vehicle.license_plate if vehicle else 'Unknown'}")
                print(f"    Parking: {record.parking_time}")
                print(f"    Released: {record.released_time}")
                print(f"    Status: {record.status}")
                print(f"    Cost: {record.total_cost}")
                print()

def main():
    """Main function"""
    print("🧹 Test Data Cleanup Tool")
    print("=" * 50)
    
    # Ask user what to do
    print("Options:")
    print("1. Clean up all test data")
    print("2. Check current data only")
    print("3. Both clean and check")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        cleanup_all_test_data()
    elif choice == "2":
        check_current_data()
    elif choice == "3":
        cleanup_all_test_data()
        check_current_data()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main() 