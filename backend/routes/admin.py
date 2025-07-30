from flask import Blueprint, request, jsonify
from functools import wraps
from models.user import User
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.vehicle import Vehicle
from models.parking_history import ParkingHistory
from extensions import db, cache
from sqlalchemy import func, cast, Integer
from datetime import datetime, timedelta
import pytz
import os
from flask import send_from_directory
from celery.result import AsyncResult
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.base import AppConfig
# Do NOT import from tasks at the top level

admin_bp = Blueprint('admin', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@admin_required
def dashboard():
    # Get statistics
    total_users = User.query.count()
    total_lots = ParkingLot.query.count()
    total_spots = ParkingSpot.query.count()
    occupied_spots = ParkingSpot.query.filter_by(is_occupied=True).count()
    total_vehicles = Vehicle.query.count()
    
    return jsonify({
        'stats': {
            'total_users': total_users,
            'total_lots': total_lots,
            'total_spots': total_spots,
            'occupied_spots': occupied_spots,
            'available_spots': total_spots - occupied_spots,
            'total_vehicles': total_vehicles
        }
    }), 200

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    users = User.query.filter_by(role='user').all()
    result = []
    for user in users:
        # Find all vehicles currently parked
        current_spots = []
        for vehicle in user.vehicles:
            if vehicle.spot_id:
                spot = vehicle.spot
                lot = spot.lot if spot else None
                current_spots.append({
                    'lot_name': lot.name if lot else None,
                    'spot_number': spot.spot_number if spot else None,
                    'license_plate': vehicle.license_plate,
                    'vehicle_id': vehicle.id,
                    'spot_id': spot.id if spot else None
                })
        result.append({
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'phone': user.phone,
            'address': user.address if hasattr(user, 'address') else '',
            'pincode': user.pincode if hasattr(user, 'pincode') else '',
            'current_spots': current_spots
        })
    return jsonify({'users': result}), 200

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'role' in data:
        user.role = data['role']
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'phone' in data:
        user.phone = data['phone']
    
    db.session.commit()
    cache.delete('admin_users')
    cache.delete('admin_users_search_')
    return jsonify({'message': 'User updated successfully'}), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    cache.delete('admin_users')
    cache.delete('admin_users_search_')
    return jsonify({'message': 'User deleted successfully'}), 200

@admin_bp.route('/users/search', methods=['GET'])
@jwt_required()
@admin_required
@cache.cached(timeout=30, key_prefix=lambda: f"admin_users_search_{request.args.get('query', '').lower()}")
def search_users():
    query_str = request.args.get('query', '').lower()
    users = User.query.all()
    results = []
    for user in users:
        if (query_str in (user.full_name or '').lower() or
            query_str in (user.email or '').lower() or
            query_str in (getattr(user, 'address', '') or '').lower() or
            query_str in (getattr(user, 'pincode', '') or '')):
            results.append({
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'phone': user.phone,
                'address': getattr(user, 'address', ''),
                'pincode': getattr(user, 'pincode', '')
            })
    return jsonify({'results': results}), 200

@admin_bp.route('/parking-lots', methods=['GET'])
@jwt_required()
@admin_required
@cache.cached(timeout=60, key_prefix='admin_parking_lots')
def get_parking_lots():
    lots = ParkingLot.query.all()
    return jsonify({
        'lots': [{
            'id': lot.id,
            'name': lot.name,
            'address': lot.address if hasattr(lot, 'address') else '',
            'pincode': lot.pincode if hasattr(lot, 'pincode') else '',
            'price_per_hour': lot.price_per_hour if hasattr(lot, 'price_per_hour') else 0,
            'max_spots': lot.max_spots if hasattr(lot, 'max_spots') else 0,
            'total_spots': len(lot.spots),
            'occupied_spots': len([spot for spot in lot.spots if spot.is_occupied])
        } for lot in lots]
    }), 200

@admin_bp.route('/parking-lots', methods=['POST'])
@jwt_required()
@admin_required
def create_parking_lot():
    data = request.get_json()
    print('Received data:', data)  # Debug log
    name = data.get('name')
    address = data.get('address')
    pincode = data.get('pincode')
    price_per_hour = data.get('price_per_hour')
    max_spots = data.get('max_spots')
    print('Parsed fields:', name, address, pincode, price_per_hour, max_spots)  # Debug log
    location = address  # For compatibility, or adjust as needed

    if any(x is None or x == '' for x in [name, address, pincode, price_per_hour, max_spots]):
        return jsonify({'error': 'All fields are required'}), 400

    new_lot = ParkingLot(
        name=name,
        address=address,
        pincode=pincode,
        price_per_hour=price_per_hour,
        max_spots=max_spots,
        location=location
    )
    db.session.add(new_lot)
    db.session.commit()

    # Auto-create parking spots for this lot
    spots = []
    for i in range(1, int(max_spots) + 1):
        spot = ParkingSpot(lot_id=new_lot.id, spot_number=str(i))
        db.session.add(spot)
        spots.append({'id': spot.id, 'spot_number': spot.spot_number})
    db.session.commit()

    # Invalidate relevant caches
    cache.delete('admin_parking_lots')
    cache.delete('admin_summary_revenue')
    cache.delete('admin_summary_occupancy')
    return jsonify({'message': 'Parking lot created successfully', 'id': new_lot.id, 'spots_created': len(spots)}), 201

@admin_bp.route('/parking-lots/<int:lot_id>/spots', methods=['GET'])
@jwt_required()
@admin_required
@cache.cached(timeout=60, key_prefix=lambda: f"admin_spots_lot_{request.view_args['lot_id']}")
def get_parking_lot_spots(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).order_by(cast(ParkingSpot.spot_number, Integer)).all()
    return jsonify({
        'spots': [{
            'id': spot.id,
            'spot_number': spot.spot_number,
            'is_occupied': spot.is_occupied,
            'vehicle_plate': spot.vehicle.license_plate if spot.vehicle else None
        } for spot in spots]
    }), 200 

@admin_bp.route('/parking-lots/<int:lot_id>', methods=['PUT'])
@jwt_required()
@admin_required
def edit_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    data = request.get_json()
    updated = False
    old_max_spots = lot.max_spots

    if 'name' in data:
        lot.name = data['name']
        updated = True
    if 'address' in data:
        lot.address = data['address']
        lot.location = data['address']  # keep location in sync
        updated = True
    if 'pincode' in data:
        lot.pincode = data['pincode']
        updated = True
    if 'price_per_hour' in data:
        lot.price_per_hour = data['price_per_hour']
        updated = True
    if 'max_spots' in data:
        new_max_spots = int(data['max_spots'])
        lot.max_spots = new_max_spots
        updated = True

        # Sync ParkingSpot records
        spots = ParkingSpot.query.filter_by(lot_id=lot_id).order_by(ParkingSpot.spot_number).all()
        current_spot_count = len(spots)

        if new_max_spots > current_spot_count:
            # Add new spots
            for i in range(current_spot_count + 1, new_max_spots + 1):
                new_spot = ParkingSpot(lot_id=lot_id, spot_number=str(i))
                db.session.add(new_spot)
        elif new_max_spots < current_spot_count:
            # Remove extra spots (only if not occupied)
            spots_to_remove = spots[new_max_spots:]
            for spot in spots_to_remove:
                if spot.is_occupied:
                    return jsonify({'error': f'Cannot reduce max spots: spot {spot.spot_number} is occupied'}), 400
                db.session.delete(spot)

    if updated:
        db.session.commit()
        # Invalidate relevant caches
        cache.delete('admin_parking_lots')
        cache.delete('admin_spots_lot_' + str(lot_id))
        cache.delete('admin_summary_revenue')
        cache.delete('admin_summary_occupancy')
        return jsonify({'message': 'Parking lot updated successfully'}), 200
    else:
        return jsonify({'error': 'No valid fields to update'}), 400

@admin_bp.route('/parking-lots/<int:lot_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    if any(spot.is_occupied for spot in spots):
        return jsonify({'error': 'Cannot delete lot: All spots must be empty'}), 400
    # Delete all spots first
    for spot in spots:
        db.session.delete(spot)
    db.session.delete(lot)
    db.session.commit()
    # Invalidate relevant caches
    cache.delete('admin_parking_lots')
    cache.delete('admin_spots_lot_' + str(lot_id))
    cache.delete('admin_summary_revenue')
    cache.delete('admin_summary_occupancy')
    return jsonify({'message': 'Parking lot deleted successfully'}), 200 

@admin_bp.route('/parking-spots/<int:spot_id>/details', methods=['GET'])
@jwt_required()
@admin_required
@cache.cached(timeout=30, key_prefix=lambda: f"admin_spot_details_{request.view_args['spot_id']}")
def get_spot_details(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    lot = spot.lot
    result = {
        'spot_id': spot.id,
        'spot_number': spot.spot_number,
        'status': 'Occupied' if spot.is_occupied else 'Available',
        'is_occupied': spot.is_occupied,
        'lot_name': lot.name if lot else None,
    }
    if spot.is_occupied and spot.vehicle:
        vehicle = spot.vehicle
        user = vehicle.owner
        result['vehicle'] = {
            'id': vehicle.id,
            'license_plate': vehicle.license_plate
        }
        result['user'] = {
            'id': user.id,
            'full_name': user.full_name,
            'email': user.email,
            'phone': user.phone
        }
        # Add start_time and est_parking_cost
        history = ParkingHistory.query.filter_by(vehicle_id=vehicle.id, lot_id=lot.id, spot_id=spot.id, status='active').order_by(ParkingHistory.parking_time.desc()).first()
        if history:
            result['start_time'] = history.parking_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %I:%M %p')
            now = datetime.utcnow()
            duration_hours = (now - history.parking_time).total_seconds() / 3600
            result['est_parking_cost'] = round(duration_hours * lot.price_per_hour, 2)
        else:
            # If no active history found, try to find any history for this vehicle and spot
            history = ParkingHistory.query.filter_by(vehicle_id=vehicle.id, spot_id=spot.id).order_by(ParkingHistory.parking_time.desc()).first()
            if history:
                result['start_time'] = history.parking_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %I:%M %p')
                now = datetime.utcnow()
                duration_hours = (now - history.parking_time).total_seconds() / 3600
                result['est_parking_cost'] = round(duration_hours * lot.price_per_hour, 2)
            else:
                # If no history found at all, create a default entry or use current time
                result['start_time'] = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %I:%M %p')
                result['est_parking_cost'] = 0.0  # Default cost since we don't know when parking started
    return jsonify(result), 200 

@admin_bp.route('/summary/revenue', methods=['GET'])
@jwt_required()
@admin_required
@cache.cached(timeout=30, key_prefix='admin_summary_revenue')
def summary_revenue():
    lots = ParkingLot.query.all()
    result = []
    for lot in lots:
        # Only consider completed sessions (status == 'out')
        histories = ParkingHistory.query.filter_by(lot_id=lot.id, status='out').order_by(ParkingHistory.vehicle_id, ParkingHistory.parking_time).all()
        from collections import defaultdict
        sessions = defaultdict(list)
        for h in histories:
            sessions[h.vehicle_id].append(h)
        total_revenue = 0.0
        for vehicle_id, actions in sessions.items():
            for action in actions:
                if action.parking_time and action.released_time:
                    duration_hours = (action.released_time - action.parking_time).total_seconds() / 3600
                    total_revenue += action.total_cost or (duration_hours * lot.price_per_hour)
        result.append({
            'lot_id': lot.id,
            'lot_name': lot.name,
            'revenue': round(total_revenue, 2)
        })
    return jsonify({'revenue_per_lot': result}), 200

@admin_bp.route('/summary/occupancy', methods=['GET'])
@jwt_required()
@admin_required
@cache.cached(timeout=30, key_prefix='admin_summary_occupancy')
def summary_occupancy():
    lots = ParkingLot.query.all()
    result = []
    for lot in lots:
        total_spots = len(lot.spots)
        occupied_spots = len([spot for spot in lot.spots if spot.is_occupied])
        available_spots = total_spots - occupied_spots
        result.append({
            'lot_id': lot.id,
            'lot_name': lot.name,
            'total_spots': total_spots,
            'occupied_spots': occupied_spots,
            'available_spots': available_spots
        })
    return jsonify({'occupancy_per_lot': result}), 200 

@admin_bp.route('/summary/revenue/timeseries', methods=['GET'])
@jwt_required()
@admin_required
def revenue_timeseries():
    period = request.args.get('period', 'daily')
    lot_id = request.args.get('lot_id', type=int)
    # Only consider completed sessions (status == 'out')
    query = ParkingHistory.query.filter_by(status='out')
    if lot_id:
        query = query.filter_by(lot_id=lot_id)
    # Group by period
    if period == 'monthly':
        group_expr = [func.strftime('%Y-%m', ParkingHistory.released_time)]
    elif period == 'weekly':
        group_expr = [func.strftime('%Y-%W', ParkingHistory.released_time)]
    else:
        group_expr = [func.strftime('%Y-%m-%d', ParkingHistory.released_time)]
    results = {}
    unpark_histories = query.order_by(ParkingHistory.vehicle_id, ParkingHistory.released_time).all()
    for unpark in unpark_histories:
        lot = unpark.lot
        if unpark.parking_time and unpark.released_time:
            duration_hours = (unpark.released_time - unpark.parking_time).total_seconds() / 3600
            revenue = unpark.total_cost or (duration_hours * lot.price_per_hour)
            key = unpark.released_time.strftime('%Y-%m-%d')
            if period == 'monthly':
                key = unpark.released_time.strftime('%Y-%m')
            elif period == 'weekly':
                key = unpark.released_time.strftime('%Y-%W')
            if key not in results:
                results[key] = 0.0
            results[key] += revenue
    timeseries = [{'period': k, 'revenue': round(v, 2)} for k, v in sorted(results.items())]
    return jsonify({'revenue_timeseries': timeseries}), 200

@admin_bp.route('/parking-lots/search', methods=['GET'])
@jwt_required()
@admin_required
@cache.cached(timeout=30, key_prefix=lambda: f"admin_lots_search_{request.args.get('query', '').lower()}")
def search_parking_lots():
    query_str = request.args.get('query', '').lower()
    lots = ParkingLot.query.all()
    results = []
    for lot in lots:
        if (query_str in lot.name.lower() or
            query_str in lot.address.lower() or
            query_str in lot.pincode.lower() or
            query_str in lot.location.lower()):
            results.append({
                'id': lot.id,
                'name': lot.name,
                'address': lot.address,
                'pincode': lot.pincode,
                'location': lot.location,
                'price_per_hour': lot.price_per_hour,
                'max_spots': lot.max_spots
            })
    return jsonify({'results': results}), 200

@admin_bp.route('/parking-spots/search', methods=['GET'])
@jwt_required()
@admin_required
@cache.cached(timeout=30, key_prefix=lambda: f"admin_spots_search_{request.args.get('query', '').lower()}")
def search_parking_spots():
    query_str = request.args.get('query', '').lower()
    spots = ParkingSpot.query.all()
    results = []
    for spot in spots:
        lot = spot.lot
        status = 'occupied' if spot.is_occupied else 'available'
        if (query_str in lot.name.lower() or
            query_str in spot.spot_number.lower() or
            query_str in status):
            results.append({
                'id': spot.id,
                'spot_number': spot.spot_number,
                'status': status,
                'lot_id': lot.id,
                'lot_name': lot.name
            })
    return jsonify({'results': results}), 200 

@admin_bp.route('/monthly-report/<int:user_id>', methods=['POST'])
@jwt_required()
def trigger_monthly_report(user_id):
    from tasks import send_monthly_report_email
    user_id_jwt = get_jwt_identity()
    user = User.query.get(user_id_jwt)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    print("DEBUG: request.get_json() returned:", data)
    month = data.get('month')
    year = data.get('year')
    print("DEBUG: About to call send_monthly_report_email.delay")
    task = send_monthly_report_email.delay(user_id, month, year)
    return jsonify({'message': 'Monthly report triggered', 'task_id': task.id})

@admin_bp.route('/monthly-reports/all', methods=['POST'])
@jwt_required()
def trigger_all_monthly_reports():
    from tasks import send_all_monthly_reports
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    month = data.get('month')
    year = data.get('year')
    
    # Trigger the monthly report task for all users
    task = send_all_monthly_reports.delay(month, year)
    
    return jsonify({
        'message': 'Monthly reports generation started for all users',
        'task_id': task.id
    }) 

@admin_bp.route('/export-csv', methods=['POST'])
@jwt_required()
def export_csv():
    from tasks import export_user_parking_history_csv
    user_id = get_current_user().id
    task = export_user_parking_history_csv.delay(user_id)
    return jsonify({'message': 'CSV export started', 'task_id': task.id})

@admin_bp.route('/export-csv-status/<task_id>', methods=['GET'])
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
                'download_url': f'/api/admin/download-csv/{data.get("filename")}'
            })
        else:
            return jsonify({'ready': False, 'error': data.get('error', 'Unknown error')})
    elif result.state == 'FAILURE':
        return jsonify({'ready': False, 'error': 'Export failed'})
    else:
        return jsonify({'ready': False})

@admin_bp.route('/download-csv/<filename>', methods=['GET'])
@jwt_required()
def download_csv(filename):
    expected_prefix = f'user_{get_current_user().id}_parking_history'
    if not filename.startswith(expected_prefix):
        return jsonify({'error': 'Access denied'}), 403
    import os
    from flask import send_from_directory
    export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../exports')
    export_dir = os.path.abspath(export_dir)
    if not os.path.exists(os.path.join(export_dir, filename)):
        return jsonify({'error': 'File not found'}), 404
    return send_from_directory(export_dir, filename, as_attachment=True) 

@admin_bp.route('/reminder-time', methods=['GET'])
@jwt_required()
def get_reminder_time():
    # Anyone can view
    hour = AppConfig.query.filter_by(key='reminder_hour').first()
    minute = AppConfig.query.filter_by(key='reminder_minute').first()
    return jsonify({
        'hour': int(hour.value) if hour else 18,
        'minute': int(minute.value) if minute else 0
    })

@admin_bp.route('/reminder-time', methods=['POST'])
@jwt_required()
def set_reminder_time():
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    hour = int(data.get('hour', 18))
    minute = int(data.get('minute', 0))
    # Set or update hour
    hour_cfg = AppConfig.query.filter_by(key='reminder_hour').first()
    if not hour_cfg:
        hour_cfg = AppConfig(key='reminder_hour', value=str(hour))
        db.session.add(hour_cfg)
    else:
        hour_cfg.value = str(hour)
    # Set or update minute
    min_cfg = AppConfig.query.filter_by(key='reminder_minute').first()
    if not min_cfg:
        min_cfg = AppConfig(key='reminder_minute', value=str(minute))
        db.session.add(min_cfg)
    else:
        min_cfg.value = str(minute)
    db.session.commit()
    return jsonify({'success': True, 'hour': hour, 'minute': minute}) 

@admin_bp.route('/trigger-monthly-report', methods=['POST'])
@jwt_required()
def trigger_monthly_report_manual():
    from tasks import send_monthly_report_email
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    user_id = data.get('user_id')
    month = data.get('month')
    year = data.get('year')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    task = send_monthly_report_email.delay(user_id, month, year)
    return jsonify({'message': 'Monthly report triggered', 'task_id': task.id})

@admin_bp.route('/trigger-daily-reminders', methods=['POST'])
@jwt_required()
def trigger_daily_reminders():
    from tasks import send_daily_email_reminders
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    task = send_daily_email_reminders.delay()
    return jsonify({'message': 'Daily reminders triggered', 'task_id': task.id})

@admin_bp.route('/reminder-stats', methods=['GET'])
@jwt_required()
def get_reminder_stats():
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    today = datetime.now().date()
    
    # Get total users
    total_users = User.query.filter_by(role='user').count()
    
    # Get users who parked today
    users_parked_today = ParkingHistory.query.filter(
        ParkingHistory.parking_time >= datetime.combine(today, datetime.min.time()),
        ParkingHistory.parking_time < datetime.combine(today + timedelta(days=1), datetime.min.time())
    ).distinct(ParkingHistory.user_id).count()
    
    # Get users with active sessions
    users_with_active_sessions = ParkingHistory.query.filter(
        ParkingHistory.released_time.is_(None)
    ).distinct(ParkingHistory.user_id).count()
    
    # Get reminder time
    hour_cfg = AppConfig.query.filter_by(key='reminder_hour').first()
    min_cfg = AppConfig.query.filter_by(key='reminder_minute').first()
    reminder_hour = int(hour_cfg.value) if hour_cfg else 18
    reminder_minute = int(min_cfg.value) if min_cfg else 0
    
    return jsonify({
        'total_users': total_users,
        'users_parked_today': users_parked_today,
        'users_without_parking_today': total_users - users_parked_today,
        'users_with_active_sessions': users_with_active_sessions,
        'reminder_time': f"{reminder_hour:02d}:{reminder_minute:02d}",
        'parking_lots_exist': ParkingLot.query.first() is not None
    }) 