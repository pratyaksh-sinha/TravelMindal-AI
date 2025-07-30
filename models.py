from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """User model for authentication and profile information."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User profile information
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    location = db.Column(db.String(100))
    preferences = db.Column(db.Text)  # Stored as JSON string
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    bookings = db.relationship('Booking', backref='user', lazy='dynamic')
    itineraries = db.relationship('Itinerary', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Set password hash using werkzeug security."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash."""
        return check_password_hash(self.password_hash, password)

class Post(db.Model):
    """Post model for social media feed."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    likes = db.relationship('Like', backref='post', lazy='dynamic')

class Comment(db.Model):
    """Comment model for posts."""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Establish relationship with user
    user = db.relationship('User', backref='comments')

class Like(db.Model):
    """Like model for posts."""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Establish relationship with user
    user = db.relationship('User', backref='likes')

class Itinerary(db.Model):
    """Itinerary model for travel plans."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    budget = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    activities = db.relationship('Activity', backref='itinerary', lazy='dynamic')

class Activity(db.Model):
    """Activity model for itinerary items."""
    id = db.Column(db.Integer, primary_key=True)
    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    cost = db.Column(db.Float)
    date_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # In minutes
    
class Booking(db.Model):
    """Booking model for travel reservations."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_type = db.Column(db.String(20), nullable=False)  # flight, train, bus, hotel
    provider = db.Column(db.String(100))
    booking_ref = db.Column(db.String(50))
    origin = db.Column(db.String(100))
    destination = db.Column(db.String(100))
    departure_date = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='confirmed')
    price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatSession(db.Model):
    """Chat session model for storing conversation history."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('ChatMessage', backref='session', lazy='dynamic')
    
    # Establish relationship with user
    user = db.relationship('User', backref='chat_sessions')

class ChatMessage(db.Model):
    """Chat message model for individual messages in a chat session."""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)  # True if message is from user, False if from AI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
