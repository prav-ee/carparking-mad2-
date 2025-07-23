from extensions import db
from datetime import datetime

class ParkingHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    parking_time = db.Column(db.DateTime, default=datetime.utcnow)
    released_time = db.Column(db.DateTime, nullable=True)
    total_cost = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='active')  # 'active' or 'out'

    user = db.relationship('User', backref='parking_history', lazy=True)
    vehicle = db.relationship('Vehicle', backref='parking_history', lazy=True)
    lot = db.relationship('ParkingLot', backref='parking_history', lazy=True) 