#!/usr/bin/env python3
"""
Script to check and clean up parking data
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

def check_all_parking_data():
    """Check all parking data by month"""
    with app.app_context():
        print("=== Checking All Parking Data by Month ===")
        
        # Get all parking history records
        all_records = ParkingHistory.query.order_by(ParkingHistory.parking_time.desc()).all()
        
        print(f"Total records: {len(all_records)}")
        
        # Group by month
        monthly_data = {}
        for record in all_records:
            month_key = f"{record.parking_time.year}-{record.parking_time.month:02d}"
            if month_key not in monthly_data:
                monthly_data[month_key] = []
            monthly_data[month_key].append(record)
        
        # Display by month
        for month in sorted(monthly_data.keys(), reverse=True):
            records = monthly_data[month]
            print(f"\n{month}: {len(records)} records")
            for record in records:
                user = User.query.get(record.user_id)
                print(f"  ID: {record.id}, User: {user.full_name if user else 'Unknown'}")
                print(f"    Parking: {record.parking_time}")
                print(f"    Released: {record.released_time}")
                print(f"    Status: {record.status}")
                print(f"    Cost: {record.total_cost}")

def clean_test_data():
    """Clean up test data from previous months"""
    with app.app_context():
        print("\n=== Cleaning Test Data ===")
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Delete data from previous months (likely test data)
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
        
        # Also check for data from previous years
        for year in range(current_year - 1, current_year - 5, -1):
            year_deleted = ParkingHistory.query.filter(
                ParkingHistory.parking_time >= datetime(year, 1, 1),
                ParkingHistory.parking_time < datetime(year + 1, 1, 1)
            ).delete()
            
            if year_deleted > 0:
                print(f"Deleted {year_deleted} records from year {year}")
                deleted_count += year_deleted
        
        db.session.commit()
        print(f"\n✅ Total deleted: {deleted_count} test records")

def create_current_month_data():
    """Create sample data for current month only"""
    with app.app_context():
        print("\n=== Creating Current Month Data ===")
        
        from models.parking_lot import ParkingLot
        from models.parking_spot import ParkingSpot
        from models.vehicle import Vehicle
        
        users = User.query.filter_by(role='user').all()
        parking_lot = ParkingLot.query.first()
        
        if not users or not parking_lot:
            print("❌ Need at least one user and parking lot")
            return False
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        for i, user in enumerate(users):
            print(f"Creating current month data for {user.full_name}")
            
            # Get or create vehicle
            vehicle = Vehicle.query.filter_by(user_id=user.id).first()
            if not vehicle:
                vehicle = Vehicle(
                    user_id=user.id,
                    license_plate=f"CURRENT{i+1}23",
                    vehicle_type="Car"
                )
                db.session.add(vehicle)
                db.session.commit()
            
            # Get or create spot
            spot = ParkingSpot.query.filter_by(lot_id=parking_lot.id).first()
            if not spot:
                spot = ParkingSpot(
                    lot_id=parking_lot.id,
                    spot_number=str(i+1)
                )
                db.session.add(spot)
                db.session.commit()
            
            # Create current month records
            current_records = [
                {
                    'parking_time': datetime(current_year, current_month, 1 + i, 9, 0),
                    'released_time': datetime(current_year, current_month, 1 + i, 17, 0),
                    'total_cost': 80.0,
                    'status': 'out'
                },
                {
                    'parking_time': datetime(current_year, current_month, 15 + i, 10, 0),
                    'released_time': datetime(current_year, current_month, 15 + i, 16, 0),
                    'total_cost': 60.0,
                    'status': 'out'
                },
                {
                    'parking_time': datetime(current_year, current_month, 25 + i, 8, 0),
                    'released_time': None,
                    'total_cost': None,
                    'status': 'active'
                }
            ]
            
            for record_data in current_records:
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
            
            print(f"✅ Created {len(current_records)} current month records for {user.full_name}")
        
        db.session.commit()
        print("\n✅ Current month data created successfully!")
        return True

def main():
    """Main function"""
    print("🔍 Parking Data Check and Cleanup Tool")
    print("=" * 50)
    
    # Check current data
    check_all_parking_data()
    
    # Ask what to do
    print("\nOptions:")
    print("1. Clean test data (delete previous months)")
    print("2. Create current month data only")
    print("3. Both clean and create")
    print("4. Just check data (no changes)")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        clean_test_data()
    elif choice == "2":
        create_current_month_data()
    elif choice == "3":
        clean_test_data()
        create_current_month_data()
    elif choice == "4":
        print("No changes made")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main() 