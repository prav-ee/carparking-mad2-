from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.vehicle import Vehicle
from models.parking_history import ParkingHistory
from datetime import datetime
import pytz
from extensions import db, cache
from sqlalchemy import cast, Integer
from models.user import User

parking_bp = Blueprint('parking', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@parking_bp.route('/lots', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60, key_prefix='available_lots')
def get_available_lots():
    lots = ParkingLot.query.all()
    return jsonify({
        'lots': [{
            'id': lot.id,
            'name': lot.name,
            'location': lot.location,
            'price_per_hour': lot.price_per_hour,
            'total_spots': len(lot.spots),
            'available_spots': len([spot for spot in lot.spots if not spot.is_occupied])
        } for lot in lots]
    }), 200

@parking_bp.route('/lots/<int:lot_id>/spots', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60, key_prefix=lambda: f"available_spots_lot_{request.view_args['lot_id']}")
def get_lot_spots(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    
    return jsonify({
        'lot': {
            'id': lot.id,
            'name': lot.name,
            'location': lot.location
        },
        'spots': [{
            'id': spot.id,
            'spot_number': spot.spot_number,
            'is_occupied': spot.is_occupied,
            'vehicle_plate': spot.vehicle.license_plate if spot.vehicle else None
        } for spot in spots]
    }), 200

@parking_bp.route('/vehicles', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60, key_prefix=lambda: f"user_vehicles_{get_current_user().id}")
def get_user_vehicles():
    vehicles = Vehicle.query.filter_by(user_id=get_current_user().id).all()
    return jsonify({
        'vehicles': [{
            'id': vehicle.id,
            'license_plate': vehicle.license_plate,
            'is_parked': vehicle.spot_id is not None,
            'spot_info': {
                'lot_name': vehicle.spot.lot.name if vehicle.spot else None,
                'spot_number': vehicle.spot.spot_number if vehicle.spot else None
            } if vehicle.spot else None
        } for vehicle in vehicles]
    }), 200

@parking_bp.route('/vehicles', methods=['POST'])
@jwt_required()
def add_vehicle():
    data = request.get_json()
    license_plate = data.get('license_plate')
    
    if not license_plate:
        return jsonify({'error': 'License plate is required'}), 400
    
    # Check if vehicle already exists
    existing_vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()
    if existing_vehicle:
        return jsonify({'error': 'Vehicle with this license plate already exists'}), 400
    
    new_vehicle = Vehicle(
        user_id=get_current_user().id,
        license_plate=license_plate
    )
    
    db.session.add(new_vehicle)
    db.session.commit()
    # Invalidate vehicles cache
    cache.delete(f"user_vehicles_{get_current_user().id}")
    return jsonify({'message': 'Vehicle added successfully', 'id': new_vehicle.id}), 201

@parking_bp.route('/history', methods=['GET'])
@jwt_required()
@cache.cached(timeout=10, key_prefix=lambda: f"user_history_{get_current_user().id}")
def get_parking_history():
    # Get current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # First, try to get current month data (excluding test vehicles)
    current_month_start = datetime(current_year, current_month, 1)
    if current_month == 12:
        current_month_end = datetime(current_year + 1, 1, 1)
    else:
        current_month_end = datetime(current_year, current_month + 1, 1)
    
    # Get current month history excluding test vehicles
    current_month_history = ParkingHistory.query.join(Vehicle).filter(
        ParkingHistory.user_id == get_current_user().id,
        ParkingHistory.parking_time >= current_month_start,
        ParkingHistory.parking_time < current_month_end,
        ~Vehicle.license_plate.like('TEST%')  # Exclude test vehicles
    ).order_by(ParkingHistory.parking_time.desc()).all()
    
    # If no current month data, get all data excluding test vehicles
    if not current_month_history:
        history = ParkingHistory.query.join(Vehicle).filter(
            ParkingHistory.user_id == get_current_user().id,
            ~Vehicle.license_plate.like('TEST%')  # Exclude test vehicles
        ).order_by(ParkingHistory.parking_time.desc()).all()
    else:
        history = current_month_history
    
    result = []
    for h in history:
        result.append({
            'id': h.id,
            'location': h.lot.name if h.lot else '',
            'address': h.lot.address if h.lot else '',
            'pincode': h.lot.pincode if h.lot else '',
            'vehicle_no': h.vehicle.license_plate if h.vehicle else '',
            'spot_id': h.spot_id,
            'parking_time': h.parking_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %I:%M %p') if h.parking_time else '',
            'released_time': h.released_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %I:%M %p') if h.released_time else '',
            'total_cost': h.total_cost,
            'price_per_hour': h.lot.price_per_hour if h.lot else 0,
            'status': h.status,
            'timestamp': h.parking_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %I:%M %p') if h.parking_time else ''
        })
    return jsonify({'history': result}), 200

@parking_bp.route('/history/refresh', methods=['POST'])
@jwt_required()
def refresh_parking_history():
    """Force refresh parking history cache"""
    try:
        # Invalidate the cache
        cache.delete(f"user_history_{get_current_user().id}")
        return jsonify({'message': 'Cache refreshed successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to refresh cache'}), 500

@parking_bp.route('/park', methods=['POST'])
@jwt_required()
def park_vehicle():
    data = request.get_json()
    vehicle_no = data.get('vehicle_no')
    spot_id = data.get('spot_id')
    
    if not vehicle_no or not spot_id:
        return jsonify({'error': 'Vehicle number and spot ID are required'}), 400
    
    # Find or create the vehicle for this user
    vehicle = Vehicle.query.filter_by(user_id=get_current_user().id, license_plate=vehicle_no).first()
    if not vehicle:
        vehicle = Vehicle(user_id=get_current_user().id, license_plate=vehicle_no)
        db.session.add(vehicle)
        db.session.commit()
    
    spot = ParkingSpot.query.get(spot_id)
    if not spot:
        return jsonify({'error': 'Parking spot not found'}), 404
    
    if spot.is_occupied:
        return jsonify({'error': 'Parking spot is already occupied'}), 400
    
    # Park the vehicle
    vehicle.spot_id = spot_id
    spot.is_occupied = True
    
    # Log history (single entry per session)
    history = ParkingHistory(user_id=get_current_user().id, vehicle_id=vehicle.id, lot_id=spot.lot_id, spot_id=spot.id, parking_time=datetime.utcnow(), status='active')
    db.session.add(history)
    db.session.commit()
    
    # Invalidate relevant caches
    cache.delete('available_lots')
    cache.delete(f"available_spots_lot_{spot.lot_id}")
    cache.delete(f"user_history_{get_current_user().id}")
    cache.delete(f"user_vehicles_{get_current_user().id}")
    return jsonify({
        'message': 'Vehicle parked successfully',
        'spot_number': spot.spot_number,
        'lot_name': spot.lot.name
    }), 200

@parking_bp.route('/unpark', methods=['POST'])
@jwt_required()
def unpark_vehicle():
    data = request.get_json()
    vehicle_id = data.get('vehicle_id')
    
    if not vehicle_id:
        return jsonify({'error': 'Vehicle ID is required'}), 400
    
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=get_current_user().id).first()
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404
    
    if not vehicle.spot_id:
        return jsonify({'error': 'Vehicle is not parked'}), 400
    
    # Unpark the vehicle
    spot = vehicle.spot
    spot.is_occupied = False
    vehicle.spot_id = None
    
    # Find the latest active history for this vehicle and spot
    history = ParkingHistory.query.filter_by(
        user_id=get_current_user().id,
        vehicle_id=vehicle.id,
        lot_id=spot.lot_id,
        spot_id=spot.id,
        status='active'
    ).order_by(ParkingHistory.parking_time.desc()).first()
    
    if not history:
        return jsonify({'error': 'Active parking history not found'}), 404
    
    # Update history
    history.released_time = datetime.utcnow()
    history.status = 'out'
    lot = spot.lot
    duration_hours = max(1, int((history.released_time - history.parking_time).total_seconds() // 3600))
    history.total_cost = duration_hours * lot.price_per_hour
    
    db.session.commit()
    
    # Invalidate relevant caches
    cache.delete('available_lots')
    cache.delete(f"available_spots_lot_{spot.lot_id}")
    cache.delete(f"user_history_{get_current_user().id}")
    cache.delete(f"user_vehicles_{get_current_user().id}")
    return jsonify({
        'message': 'Vehicle unparked successfully',
        'spot_number': spot.spot_number,
        'lot_name': spot.lot.name
    }), 200

@parking_bp.route('/auto-park', methods=['POST'])
@jwt_required()
def auto_park_vehicle():
    data = request.get_json()
    vehicle_id = data.get('vehicle_id')
    lot_id = data.get('lot_id')

    if not vehicle_id or not lot_id:
        return jsonify({'error': 'Vehicle ID and lot ID are required'}), 400

    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=get_current_user().id).first()
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    # Find the first available spot in the lot
    spot = ParkingSpot.query.filter_by(lot_id=lot_id, is_occupied=False).order_by(cast(ParkingSpot.spot_number, Integer)).first()
    if not spot:
        return jsonify({'error': 'No available spots in this lot'}), 400

    # Park the vehicle
    vehicle.spot_id = spot.id
    spot.is_occupied = True

    # Log history
    history = ParkingHistory(user_id=get_current_user().id, vehicle_id=vehicle.id, lot_id=lot_id, action='park', timestamp=datetime.utcnow())
    db.session.add(history)
    db.session.commit()

    return jsonify({
        'message': 'Vehicle auto-parked successfully',
        'spot_id': spot.id,
        'spot_number': spot.spot_number,
        'lot_name': spot.lot.name
    }), 200 

@parking_bp.route('/export-csv', methods=['POST'])
@jwt_required()
def export_csv():
    from tasks import export_user_parking_history_csv
    user_id = get_current_user().id
    task = export_user_parking_history_csv.delay(user_id)
    return jsonify({'message': 'CSV export started', 'task_id': task.id})

@parking_bp.route('/export-csv-status/<task_id>', methods=['GET'])
@jwt_required()
def export_csv_status(task_id):
    from celery.result import AsyncResult
    from tasks import celery  # Use the celery object with correct config
    result = AsyncResult(task_id, app=celery)
    if result.state == 'SUCCESS':
        data = result.result
        if data and data.get('success'):
            return jsonify({
                'ready': True,
                'download_url': f'/api/parking/download-csv/{data.get("filename")}'
            })
        else:
            return jsonify({'ready': False, 'error': data.get('error', 'Unknown error')})
    elif result.state == 'FAILURE':
        return jsonify({'ready': False, 'error': 'Export failed'})
    else:
        return jsonify({'ready': False})

@parking_bp.route('/download-csv/<filename>', methods=['GET'])
@jwt_required()
def download_csv(filename):
    expected_prefix = f'user_{get_current_user().id}_parking_history'
    if not filename.startswith(expected_prefix):
        return jsonify({'error': 'Access denied'}), 403
    import os
    export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../exports')
    export_dir = os.path.abspath(export_dir)
    if not os.path.exists(os.path.join(export_dir, filename)):
        return jsonify({'error': 'File not found'}), 404
    return send_from_directory(export_dir, filename, as_attachment=True) 

@parking_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_parking():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'phone': user.phone
    }), 200 

@parking_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user_parking():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    data = request.get_json()
    updated = False
    if 'full_name' in data and data['full_name']:
        user.full_name = data['full_name']
        updated = True
    if 'phone' in data and data['phone']:
        user.phone = data['phone']
        updated = True
    if 'email' in data and data['email']:
        # Optionally, check for email uniqueness
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user.id:
            return jsonify({'error': 'Email already in use'}), 400
        user.email = data['email']
        updated = True
    if updated:
        db.session.commit()
        return jsonify({'message': 'User updated successfully'}), 200
    else:
        return jsonify({'message': 'No changes made'}), 200 