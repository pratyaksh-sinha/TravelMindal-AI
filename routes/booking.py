from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import User, Booking
import logging
from datetime import datetime

booking_bp = Blueprint('booking', __name__, url_prefix='/booking')

@booking_bp.route('/', methods=['GET'])
def booking_page():
    """Render the booking interface."""
    return render_template('booking.html')

@booking_bp.route('/bookings', methods=['GET'])
@jwt_required()
def get_bookings():
    """Get all bookings for the current user."""
    user_id = get_jwt_identity()
    
    # Filter bookings by status if provided
    status = request.args.get('status')
    if status:
        bookings = Booking.query.filter_by(user_id=user_id, status=status).order_by(Booking.departure_date).all()
    else:
        bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.departure_date).all()
    
    bookings_data = []
    for booking in bookings:
        bookings_data.append({
            "id": booking.id,
            "booking_type": booking.booking_type,
            "provider": booking.provider,
            "booking_ref": booking.booking_ref,
            "origin": booking.origin,
            "destination": booking.destination,
            "departure_date": booking.departure_date.isoformat() if booking.departure_date else None,
            "return_date": booking.return_date.isoformat() if booking.return_date else None,
            "status": booking.status,
            "price": booking.price,
            "created_at": booking.created_at.isoformat()
        })
    
    return jsonify({"bookings": bookings_data}), 200

@booking_bp.route('/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    """Create a new booking."""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    booking_type = data.get('booking_type')
    provider = data.get('provider')
    origin = data.get('origin')
    destination = data.get('destination')
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')
    price = data.get('price')
    
    if not booking_type or not origin or not destination or not departure_date:
        return jsonify({"error": "Booking type, origin, destination, and departure date are required"}), 400
    
    # Parse dates if provided
    try:
        departure_date = datetime.fromisoformat(departure_date)
        if return_date:
            return_date = datetime.fromisoformat(return_date)
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
    
    # Generate a booking reference (in a real app, this would come from an external API)
    booking_ref = f"TM{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    booking = Booking(
        user_id=user_id,
        booking_type=booking_type,
        provider=provider,
        booking_ref=booking_ref,
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        status="confirmed",
        price=price
    )
    
    try:
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            "message": "Booking created successfully",
            "booking": {
                "id": booking.id,
                "booking_type": booking.booking_type,
                "provider": booking.provider,
                "booking_ref": booking.booking_ref,
                "origin": booking.origin,
                "destination": booking.destination,
                "departure_date": booking.departure_date.isoformat() if booking.departure_date else None,
                "return_date": booking.return_date.isoformat() if booking.return_date else None,
                "status": booking.status,
                "price": booking.price,
                "created_at": booking.created_at.isoformat()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating booking: {str(e)}")
        return jsonify({"error": "An error occurred while creating the booking"}), 500

@booking_bp.route('/bookings/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_booking(booking_id):
    """Get a specific booking."""
    user_id = get_jwt_identity()
    booking = Booking.query.filter_by(id=booking_id, user_id=user_id).first()
    
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    return jsonify({
        "booking": {
            "id": booking.id,
            "booking_type": booking.booking_type,
            "provider": booking.provider,
            "booking_ref": booking.booking_ref,
            "origin": booking.origin,
            "destination": booking.destination,
            "departure_date": booking.departure_date.isoformat() if booking.departure_date else None,
            "return_date": booking.return_date.isoformat() if booking.return_date else None,
            "status": booking.status,
            "price": booking.price,
            "created_at": booking.created_at.isoformat()
        }
    }), 200

@booking_bp.route('/bookings/<int:booking_id>', methods=['DELETE'])
@jwt_required()
def cancel_booking(booking_id):
    """Cancel a booking."""
    user_id = get_jwt_identity()
    booking = Booking.query.filter_by(id=booking_id, user_id=user_id).first()
    
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    # Check if booking can be cancelled (e.g., not already cancelled, not in the past)
    if booking.status == "cancelled":
        return jsonify({"error": "Booking is already cancelled"}), 400
    
    if booking.departure_date and booking.departure_date < datetime.utcnow():
        return jsonify({"error": "Cannot cancel a booking that has already departed"}), 400
    
    booking.status = "cancelled"
    
    try:
        db.session.commit()
        return jsonify({"message": "Booking cancelled successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error cancelling booking: {str(e)}")
        return jsonify({"error": "An error occurred while cancelling the booking"}), 500

@booking_bp.route('/search', methods=['POST'])
def search_transport():
    """Search for available transportation options."""
    data = request.get_json()
    
    booking_type = data.get('booking_type')
    origin = data.get('origin')
    destination = data.get('destination')
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')
    passengers = data.get('passengers', 1)
    
    if not booking_type or not origin or not destination or not departure_date:
        return jsonify({"error": "Booking type, origin, destination, and departure date are required"}), 400
    
    # In a real application, this would call external APIs for flight/train/bus searches
    # For now, we'll return mock data
    
    # Generate some mock search results
    results = []
    
    # Different mock providers based on booking type
    providers = {
        "flight": ["AirIndia", "SpiceJet", "IndiGo", "Vistara"],
        "train": ["Indian Railways", "IRCTC", "Deccan Express", "Rajdhani"],
        "bus": ["RedBus", "AbhiBus", "MSRTC", "KSRTC"]
    }
    
    # Generate 3-5 random options
    import random
    from datetime import timedelta
    
    try:
        base_departure = datetime.fromisoformat(departure_date)
        
        # Generate between 3-5 options
        num_options = random.randint(3, 5)
        
        for i in range(num_options):
            # Randomize departure time by ±2 hours
            departure_offset = random.randint(-120, 120)
            departure_time = base_departure + timedelta(minutes=departure_offset)
            
            # Duration between 1-8 hours depending on type
            if booking_type == "flight":
                duration_minutes = random.randint(60, 240)
            elif booking_type == "train":
                duration_minutes = random.randint(120, 480)
            else:  # bus
                duration_minutes = random.randint(180, 480)
                
            arrival_time = departure_time + timedelta(minutes=duration_minutes)
            
            # Price range based on type
            if booking_type == "flight":
                price = random.randint(3000, 15000)
            elif booking_type == "train":
                price = random.randint(500, 3000)
            else:  # bus
                price = random.randint(300, 1500)
                
            # Select a random provider
            provider = random.choice(providers.get(booking_type, ["Unknown"]))
            
            results.append({
                "booking_type": booking_type,
                "provider": provider,
                "origin": origin,
                "destination": destination,
                "departure_time": departure_time.isoformat(),
                "arrival_time": arrival_time.isoformat(),
                "duration_minutes": duration_minutes,
                "price": price,
                "available_seats": random.randint(1, 30)
            })
        
        return jsonify({"results": results}), 200
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
    except Exception as e:
        logging.error(f"Error searching for transport: {str(e)}")
        return jsonify({"error": "An error occurred while searching for transport options"}), 500
