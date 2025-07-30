from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import User, ChatSession, ChatMessage
from utils.openai_helper import chat_with_travel_assistant
import logging

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

@chatbot_bp.route('/', methods=['GET'])
def chat_page():
    """Render the chatbot interface."""
    return render_template('chatbot.html')

@chatbot_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_sessions():
    """Get all chat sessions for the current user."""
    user_id = get_jwt_identity()
    sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()
    
    sessions_data = []
    for session in sessions:
        last_message = ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.created_at.desc()).first()
        sessions_data.append({
            "id": session.id,
            "created_at": session.created_at.isoformat(),
            "last_message": last_message.message[:50] + "..." if last_message and len(last_message.message) > 50 else last_message.message if last_message else ""
        })
    
    return jsonify({"sessions": sessions_data}), 200

@chatbot_bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_session():
    """Create a new chat session."""
    user_id = get_jwt_identity()
    
    session = ChatSession(user_id=user_id)
    try:
        db.session.add(session)
        db.session.commit()
        return jsonify({
            "message": "Chat session created successfully",
            "session": {
                "id": session.id,
                "created_at": session.created_at.isoformat()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating chat session: {str(e)}")
        return jsonify({"error": "An error occurred while creating the chat session"}), 500

@chatbot_bp.route('/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id):
    """Get a chat session with its messages."""
    user_id = get_jwt_identity()
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    
    if not session:
        return jsonify({"error": "Chat session not found"}), 404
    
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at).all()
    messages_data = []
    for message in messages:
        messages_data.append({
            "id": message.id,
            "message": message.message,
            "is_user": message.is_user,
            "created_at": message.created_at.isoformat()
        })
    
    return jsonify({
        "session": {
            "id": session.id,
            "created_at": session.created_at.isoformat(),
            "messages": messages_data
        }
    }), 200

@chatbot_bp.route('/sessions/<int:session_id>/messages', methods=['POST'])
@jwt_required()
def send_message(session_id):
    """Send a message to the chatbot and get a response."""
    user_id = get_jwt_identity()
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    
    if not session:
        return jsonify({"error": "Chat session not found"}), 404
    
    data = request.get_json()
    message_text = data.get('message')
    
    if not message_text:
        return jsonify({"error": "Message is required"}), 400
    
    # Get chat history
    history = []
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at).all()
    for msg in messages:
        role = "user" if msg.is_user else "assistant"
        history.append({"role": role, "content": msg.message})
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        message=message_text,
        is_user=True
    )
    
    try:
        db.session.add(user_message)
        db.session.commit()
        
        # Generate AI response
        ai_response = chat_with_travel_assistant(message_text, history)
        
        # Save AI response
        ai_message = ChatMessage(
            session_id=session_id,
            message=ai_response,
            is_user=False
        )
        
        db.session.add(ai_message)
        db.session.commit()
        
        return jsonify({
            "user_message": {
                "id": user_message.id,
                "message": user_message.message,
                "is_user": user_message.is_user,
                "created_at": user_message.created_at.isoformat()
            },
            "ai_message": {
                "id": ai_message.id,
                "message": ai_message.message,
                "is_user": ai_message.is_user,
                "created_at": ai_message.created_at.isoformat()
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error processing message: {str(e)}")
        return jsonify({"error": "An error occurred while processing the message"}), 500

@chatbot_bp.route('/ask', methods=['POST'])
def ask_question():
    """Simple endpoint for asking questions without authentication or session management."""
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    try:
        response = chat_with_travel_assistant(message)
        return jsonify({"response": response}), 200
    except Exception as e:
        logging.error(f"Error processing question: {str(e)}")
        return jsonify({"error": "An error occurred while processing the question"}), 500
