from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        if request.is_json:
            # API request
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            
            # Validate form data
            if not username or not email or not password:
                return jsonify({"error": "All fields are required"}), 400
                
            # Check if username or email already exists
            if User.query.filter_by(username=username).first():
                return jsonify({"error": "Username already exists"}), 400
                
            if User.query.filter_by(email=email).first():
                return jsonify({"error": "Email already exists"}), 400
                
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            
            try:
                db.session.add(user)
                db.session.commit()
                
                # Generate access token
                access_token = create_access_token(identity=user.id)
                
                return jsonify({
                    "message": "User registered successfully",
                    "access_token": access_token,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email
                    }
                }), 201
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error registering user: {str(e)}")
                return jsonify({"error": "An error occurred during registration"}), 500
        else:
            # Form submission
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Validate form data
            if not username or not email or not password:
                flash('All fields are required', 'danger')
                return render_template('register.html')
                
            # Check if username or email already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'danger')
                return render_template('register.html')
                
            if User.query.filter_by(email=email).first():
                flash('Email already exists', 'danger')
                return render_template('register.html')
                
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            
            try:
                db.session.add(user)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error registering user: {str(e)}")
                flash('An error occurred during registration', 'danger')
                return render_template('register.html')
    
    # GET request
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        if request.is_json:
            # API request
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            # Validate form data
            if not email or not password:
                return jsonify({"error": "Email and password are required"}), 400
                
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                return jsonify({"error": "Invalid email or password"}), 401
                
            # Generate access token
            access_token = create_access_token(identity=user.id)
            
            return jsonify({
                "message": "Login successful",
                "access_token": access_token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }), 200
        else:
            # Form submission
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Validate form data
            if not email or not password:
                flash('Email and password are required', 'danger')
                return render_template('login.html')
                
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                flash('Invalid email or password', 'danger')
                return render_template('login.html')
                
            # Set session for user
            # Note: In a real application, you would use flask_login here
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
    
    # GET request
    return render_template('login.html')

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "bio": user.bio,
        "location": user.location,
        "preferences": user.preferences
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    
    # Update user profile
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'bio' in data:
        user.bio = data['bio']
    if 'location' in data:
        user.location = data['location']
    if 'preferences' in data:
        user.preferences = data['preferences']
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "bio": user.bio,
                "location": user.location,
                "preferences": user.preferences
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating profile: {str(e)}")
        return jsonify({"error": "An error occurred while updating the profile"}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Handle user logout."""
    if request.is_json:
        # API request - nothing to do for JWT as tokens are stateless
        return jsonify({"message": "Logged out successfully"}), 200
    else:
        # Form submission - clear session
        # Note: In a real application, you would use flask_login here
        flash('Logged out successfully', 'success')
        return redirect(url_for('index'))
