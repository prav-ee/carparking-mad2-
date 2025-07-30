import os
import requests
import pytz
from datetime import datetime, timedelta
from celery_app import make_celery
from flask import render_template, current_app
from flask_mail import Message
from sqlalchemy import func, and_
from extensions import db, mail
from models.user import User
from models.parking_history import ParkingHistory
from models.parking_lot import ParkingLot
from models.base import AppConfig
from celery_app import make_celery
from celery.schedules import crontab
import csv

# Delay import of app to avoid circular import

def get_celery():
    from app import app
    return make_celery(app)

celery = get_celery()

GOOGLE_CHAT_WEBHOOK_URL = os.environ.get('GOOGLE_CHAT_WEBHOOK_URL', 'https://chat.googleapis.com/v1/spaces/XXXX/messages?key=YYYY')

@celery.task
def send_daily_email_reminders():
    """
    Send daily email reminders to users who haven't parked today
    Checks if parking lots exist and if users haven't visited
    """
    with current_app.app_context():
        # Fetch reminder time from DB
        hour_cfg = AppConfig.query.filter_by(key='reminder_hour').first()
        min_cfg = AppConfig.query.filter_by(key='reminder_minute').first()
        reminder_hour = int(hour_cfg.value) if hour_cfg else 18
        reminder_minute = int(min_cfg.value) if min_cfg else 0
        
        now = datetime.utcnow()
        if now.hour != reminder_hour or now.minute != reminder_minute:
            return  # Not the configured time, skip sending
        
        today = now.date()
        
        # Check if any parking lots exist (created by admin)
        parking_lots_exist = ParkingLot.query.first() is not None
        if not parking_lots_exist:
            print("No parking lots found. Skipping reminders.")
            return
        
        # Get all users (excluding admins)
        users = User.query.filter_by(role='user').all()
        
        for user in users:
            # Check if user has parked today
            has_parked_today = ParkingHistory.query.filter(
                ParkingHistory.user_id == user.id,
                ParkingHistory.parking_time >= datetime.combine(today, datetime.min.time()),
                ParkingHistory.parking_time < datetime.combine(today + timedelta(days=1), datetime.min.time())
            ).first() is not None
            
            if not has_parked_today:
                # Send email reminder
                send_reminder_email.delay(user.id)

@celery.task
def send_reminder_email(user_id):
    """
    Send a personalized reminder email to a specific user
    """
    with current_app.app_context():
        user = User.query.get(user_id)
        if not user or not user.email:
            return {"error": "User not found or no email address"}
        
        # Get available parking lots
        available_lots = ParkingLot.query.filter_by(is_active=True).all()
        
        # Check if user has any active parking sessions
        active_session = ParkingHistory.query.filter(
            ParkingHistory.user_id == user_id,
            ParkingHistory.released_time.is_(None)
        ).first()
        
        # Prepare email content
        subject = "Daily Parking Reminder - Book Your Spot!"
        
        # Create HTML email content
        with current_app.test_request_context():
            html_content = render_template(
                'daily_reminder.html',
                user=user,
                available_lots=available_lots,
                has_active_session=active_session is not None,
                current_time=datetime.now().strftime("%I:%M %p"),
                current_date=datetime.now().strftime("%B %d, %Y")
            )
        
        try:
            msg = Message(
                subject=subject,
                recipients=[user.email],
                html=html_content
            )
            mail.send(msg)
            print(f"Reminder email sent to {user.email}")
            return {"success": True, "email": user.email}
        except Exception as e:
            print(f"Failed to send reminder email to {user.email}: {str(e)}")
            return {"error": str(e)}

@celery.task
def generate_monthly_report(user_id, month=None, year=None):
    """
    Generate monthly activity report for a specific user
    """
    with current_app.app_context():
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year
        
        # Calculate date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            return {"error": "User not found"}
        
        # Get parking history for the month
        parking_records = ParkingHistory.query.filter(
            and_(
                ParkingHistory.user_id == user_id,
                ParkingHistory.parking_time >= start_date,
                ParkingHistory.parking_time < end_date
            )
        ).all()
        
        if not parking_records:
            return {"message": "No parking activity found for this month"}
        
        # Calculate statistics
        total_bookings = len(parking_records)
        total_hours = 0
        total_spent = 0
        parking_lot_usage = {}
        cost_breakdown = {}
        
        for record in parking_records:
            # Calculate hours
            if record.released_time:
                duration = (record.released_time - record.parking_time).total_seconds() / 3600
                total_hours += duration
            else:
                # For active bookings, calculate until now
                duration = (datetime.now() - record.parking_time).total_seconds() / 3600
                total_hours += duration
            
            # Calculate cost
            cost = record.total_cost or 0
            total_spent += cost
            
            # Track parking lot usage
            lot_name = record.lot.name
            if lot_name not in parking_lot_usage:
                parking_lot_usage[lot_name] = 0
            parking_lot_usage[lot_name] += 1
            
            # Track cost breakdown by parking lot
            if lot_name not in cost_breakdown:
                cost_breakdown[lot_name] = 0
            cost_breakdown[lot_name] += cost
        
        # Convert to lists for template
        parking_lot_usage_list = [{"name": name, "count": count} for name, count in parking_lot_usage.items()]
        parking_lot_usage_list.sort(key=lambda x: x["count"], reverse=True)
        
        cost_breakdown_list = [{"name": name, "cost": cost} for name, cost in cost_breakdown.items()]
        cost_breakdown_list.sort(key=lambda x: x["cost"], reverse=True)
        
        # Calculate average duration
        avg_duration = total_hours / total_bookings if total_bookings > 0 else 0
        
        # Get recent bookings (last 5)
        recent_bookings = ParkingHistory.query.filter(
            and_(
                ParkingHistory.user_id == user_id,
                ParkingHistory.parking_time >= start_date,
                ParkingHistory.parking_time < end_date
            )
        ).order_by(ParkingHistory.parking_time.desc()).limit(5).all()
        
        # Generate savings tip
        savings_tip = generate_savings_tip(parking_lot_usage_list, cost_breakdown_list, total_spent)
        
        # Prepare template data
        template_data = {
            "report_period": f"{start_date.strftime('%B %Y')}",
            "generated_date": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "total_bookings": total_bookings,
            "total_hours": total_hours,
            "total_spent": total_spent,
            "avg_duration": avg_duration,
            "parking_lot_usage": parking_lot_usage_list,
            "cost_breakdown": cost_breakdown_list,
            "recent_bookings": recent_bookings,
            "savings_tip": savings_tip
        }
        
        return template_data

@celery.task
def send_monthly_report_email(user_id, month=None, year=None):
    from app import app
    with app.app_context():
        # Ensure month and year are integers if provided
        if month is not None:
            try:
                month = int(month)
            except Exception:
                month = datetime.now().month
        else:
            month = datetime.now().month

        if year is not None:
            try:
                year = int(year)
            except Exception:
                year = datetime.now().year
        else:
            year = datetime.now().year

        # Create proper date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        user = User.query.get(user_id)
        if not user:
            return {"error": "User not found"}
        
        # Get parking records for the month
        records = ParkingHistory.query.filter(
            ParkingHistory.user_id == user_id,
            ParkingHistory.parking_time >= start_date,
            ParkingHistory.parking_time < end_date
        ).order_by(ParkingHistory.parking_time.desc()).all()
        
        # Calculate statistics
        total_bookings = len(records)
        total_spent = sum(r.total_cost or 0 for r in records)
        
        # Calculate parking lot usage
        lot_usage = {}
        for r in records:
            lot_name = r.lot.name if r.lot else "Unknown"
            lot_usage[lot_name] = lot_usage.get(lot_name, 0) + 1
        
        most_used_lot = max(lot_usage, key=lot_usage.get) if lot_usage else "N/A"
        
        # Calculate average session duration
        total_hours = 0
        completed_sessions = 0
        for r in records:
            if r.parking_time and r.released_time:
                duration = (r.released_time - r.parking_time).total_seconds() / 3600
                total_hours += duration
                completed_sessions += 1
            elif r.parking_time:
                # For active sessions, calculate until now
                duration = (datetime.now() - r.parking_time).total_seconds() / 3600
                total_hours += duration
                completed_sessions += 1
        
        avg_duration = total_hours / completed_sessions if completed_sessions > 0 else 0
        
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(ist)
        
        html = render_template(
            'monthly_report.html',
            user=user,
            total_bookings=total_bookings,
            total_spent=total_spent,
            most_used_lot=most_used_lot,
            records=records,
            month=start_date.strftime('%B'),
            year=year,
            current_time=current_time_ist.strftime('%I:%M %p'),
            generated_date=current_time_ist.strftime('%B %d, %Y at %I:%M %p'),
            avg_duration=avg_duration,
            total_hours=total_hours,
            completed_sessions=completed_sessions,
            pytz=pytz,
            datetime=datetime
        )
        
        subject_str = f"Your {start_date.strftime('%B %Y')} Parking Activity Report"
        
        msg = Message(
            subject=subject_str,
            recipients=[user.email],
            html=html
        )
        mail.send(msg)
        return {"success": True}

@celery.task
def send_all_monthly_reports():
    from app import app
    with app.app_context():
        users = User.query.filter_by(role='user').all()
        for user in users:
            send_monthly_report_email.delay(user.id)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(day_of_month=1, hour=9, minute=0),
        send_all_monthly_reports.s(),
        name='send-monthly-reports'
    )

@celery.task
def export_user_parking_history_csv(user_id):
    from app import app
    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            return {"error": "User not found"}
        records = ParkingHistory.query.filter_by(user_id=user_id).order_by(ParkingHistory.parking_time.desc()).all()
        if not records:
            return {"error": "No parking history found"}
        export_dir = os.path.join(current_app.root_path, 'exports')
        os.makedirs(export_dir, exist_ok=True)
        filename = f'user_{user_id}_parking_history.csv'
        filepath = os.path.join(export_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['slot_id', 'spot_id', 'lot_name', 'parking_time', 'released_time', 'cost', 'remarks'])
            for r in records:
                writer.writerow([
                    r.id,
                    r.spot_id,
                    r.lot.name if r.lot else '',
                    r.parking_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %I:%M %p') if r.parking_time else '',
                    r.released_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %I:%M %p') if r.released_time else '',
                    r.total_cost or 0,
                    r.status or ''
                ])
        return {"success": True, "filename": filename}

def generate_savings_tip(parking_lot_usage, cost_breakdown, total_spent):
    """
    Generate personalized savings tips based on user behavior
    """
    if not parking_lot_usage or not cost_breakdown:
        return None
    
    most_used_lot = parking_lot_usage[0]
    most_expensive_lot = cost_breakdown[0]
    
    tips = []
    
    # Tip based on usage pattern
    if most_used_lot["count"] > 10:
        tips.append(f"You frequently use {most_used_lot['name']}. Consider a monthly pass for better rates!")
    
    # Tip based on spending
    if total_spent > 1000:
        tips.append("Your monthly parking spending is high. Consider carpooling or using public transport on some days.")
    
    # Tip based on lot variety
    if len(parking_lot_usage) > 3:
        tips.append("You use multiple parking lots. Try to stick to one location for potential loyalty discounts.")
    
    # Tip based on expensive lots
    if most_expensive_lot["cost"] > total_spent * 0.5:
        tips.append(f"Most of your spending is at {most_expensive_lot['name']}. Look for cheaper alternatives nearby.")
    
    return " ".join(tips) if tips else "Great job managing your parking! Keep up the good work."

# Schedule monthly reports to run on the first day of every month at 9:00 AM
from celery.schedules import crontab
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run every 5 minutes to check if it's time to send reminders
    sender.add_periodic_task(
        crontab(minute='*/5'),
        send_daily_email_reminders.s(),
        name='send-daily-email-reminders'
    )
    sender.add_periodic_task(
        crontab(day_of_month=1, hour=9, minute=0),
        send_all_monthly_reports.s(),
        name='send-monthly-reports'
    ) 