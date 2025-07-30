import os
from flask import Flask
from extensions import db
from models.parking_history import ParkingHistory
from models.user import User

# Adjust path as needed
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    print('All ParkingHistory records:')
    histories = ParkingHistory.query.all()
    for h in histories:
        user = User.query.get(h.user_id)
        print(f'ID: {h.id}, user_id: {h.user_id}, user_email: {user.email if user else "?"}, vehicle_id: {h.vehicle_id}, lot_id: {h.lot_id}, spot_id: {h.spot_id}, status: {h.status}')

    # Uncomment below to delete all ParkingHistory records not belonging to a specific user
    # target_user_id = ... # set this to the correct user id
    # to_delete = ParkingHistory.query.filter(ParkingHistory.user_id != target_user_id).all()
    # for h in to_delete:
    #     print(f'Deleting history ID: {h.id} (user_id: {h.user_id})')
    #     db.session.delete(h)
    # db.session.commit()
    # print('Cleanup complete.') 