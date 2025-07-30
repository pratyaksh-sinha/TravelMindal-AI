from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import User, Itinerary, Activity
from utils.openai_helper import generate_itinerary, generate_travel_recommendations
import json
import logging

itinerary_bp = Blueprint('itinerary', __name__, url_prefix='/itinerary')

@itinerary_bp.route('/', methods=['GET'])
def itinerary_page():
    """Render the itinerary planner interface."""
    return render_template('itinerary.html')

@itinerary_bp.route('/recommendations', methods=['POST'])
def get_recommendations():
    """Get travel recommendations based on budget and location."""
    data = request.get_json()
    query = data.get('query')
    budget = data.get('budget')
    location = data.get('location')
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    try:
        recommendations = generate_travel_recommendations(query, budget, location)
        return jsonify(recommendations), 200
    except Exception as e:
        logging.error(f"Error generating recommendations: {str(e)}")
        return jsonify({"error": "An error occurred while generating recommendations"}), 500

@itinerary_bp.route('/plan', methods=['POST'])
def plan_trip():
    """Generate a detailed trip plan based on parameters."""
    data = request.get_json()
    location = data.get('location')
    budget = data.get('budget')
    duration = data.get('duration', 1)
    interests = data.get('interests', [])
    
    if not location or not budget:
        return jsonify({"error": "Location and budget are required"}), 400
    
    try:
        plan = generate_itinerary(location, budget, duration, interests)
        return jsonify(plan), 200
    except Exception as e:
        logging.error(f"Error generating itinerary: {str(e)}")
        return jsonify({"error": "An error occurred while generating the itinerary"}), 500

@itinerary_bp.route('/itineraries', methods=['GET'])
@jwt_required()
def get_itineraries():
    """Get all itineraries for the current user."""
    user_id = get_jwt_identity()
    itineraries = Itinerary.query.filter_by(user_id=user_id).order_by(Itinerary.created_at.desc()).all()
    
    itineraries_data = []
    for itinerary in itineraries:
        itineraries_data.append({
            "id": itinerary.id,
            "title": itinerary.title,
            "description": itinerary.description,
            "budget": itinerary.budget,
            "location": itinerary.location,
            "start_date": itinerary.start_date.isoformat() if itinerary.start_date else None,
            "end_date": itinerary.end_date.isoformat() if itinerary.end_date else None,
            "created_at": itinerary.created_at.isoformat()
        })
    
    return jsonify({"itineraries": itineraries_data}), 200

@itinerary_bp.route('/itineraries', methods=['POST'])
@jwt_required()
def create_itinerary():
    """Create a new itinerary."""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    title = data.get('title')
    description = data.get('description')
    budget = data.get('budget')
    location = data.get('location')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    activities = data.get('activities', [])
    
    if not title or not budget or not location:
        return jsonify({"error": "Title, budget, and location are required"}), 400
    
    itinerary = Itinerary(
        user_id=user_id,
        title=title,
        description=description,
        budget=budget,
        location=location,
        start_date=start_date,
        end_date=end_date
    )
    
    try:
        db.session.add(itinerary)
        db.session.commit()
        
        # Add activities
        for activity_data in activities:
            activity = Activity(
                itinerary_id=itinerary.id,
                name=activity_data.get('name'),
                description=activity_data.get('description'),
                location=activity_data.get('location'),
                cost=activity_data.get('cost'),
                date_time=activity_data.get('date_time'),
                duration=activity_data.get('duration')
            )
            db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            "message": "Itinerary created successfully",
            "itinerary": {
                "id": itinerary.id,
                "title": itinerary.title,
                "description": itinerary.description,
                "budget": itinerary.budget,
                "location": itinerary.location,
                "start_date": itinerary.start_date.isoformat() if itinerary.start_date else None,
                "end_date": itinerary.end_date.isoformat() if itinerary.end_date else None,
                "created_at": itinerary.created_at.isoformat()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating itinerary: {str(e)}")
        return jsonify({"error": "An error occurred while creating the itinerary"}), 500

@itinerary_bp.route('/itineraries/<int:itinerary_id>', methods=['GET'])
@jwt_required()
def get_itinerary(itinerary_id):
    """Get a specific itinerary with its activities."""
    user_id = get_jwt_identity()
    itinerary = Itinerary.query.filter_by(id=itinerary_id, user_id=user_id).first()
    
    if not itinerary:
        return jsonify({"error": "Itinerary not found"}), 404
    
    activities = Activity.query.filter_by(itinerary_id=itinerary_id).all()
    activities_data = []
    for activity in activities:
        activities_data.append({
            "id": activity.id,
            "name": activity.name,
            "description": activity.description,
            "location": activity.location,
            "cost": activity.cost,
            "date_time": activity.date_time.isoformat() if activity.date_time else None,
            "duration": activity.duration
        })
    
    return jsonify({
        "itinerary": {
            "id": itinerary.id,
            "title": itinerary.title,
            "description": itinerary.description,
            "budget": itinerary.budget,
            "location": itinerary.location,
            "start_date": itinerary.start_date.isoformat() if itinerary.start_date else None,
            "end_date": itinerary.end_date.isoformat() if itinerary.end_date else None,
            "created_at": itinerary.created_at.isoformat(),
            "activities": activities_data
        }
    }), 200

@itinerary_bp.route('/itineraries/<int:itinerary_id>', methods=['DELETE'])
@jwt_required()
def delete_itinerary(itinerary_id):
    """Delete an itinerary."""
    user_id = get_jwt_identity()
    itinerary = Itinerary.query.filter_by(id=itinerary_id, user_id=user_id).first()
    
    if not itinerary:
        return jsonify({"error": "Itinerary not found"}), 404
    
    try:
        # Delete associated activities
        Activity.query.filter_by(itinerary_id=itinerary_id).delete()
        
        # Delete itinerary
        db.session.delete(itinerary)
        db.session.commit()
        
        return jsonify({"message": "Itinerary deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting itinerary: {str(e)}")
        return jsonify({"error": "An error occurred while deleting the itinerary"}), 500
