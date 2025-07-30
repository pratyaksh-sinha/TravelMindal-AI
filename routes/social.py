from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import User, Post, Comment, Like
import logging

social_bp = Blueprint('social', __name__, url_prefix='/social')

@social_bp.route('/', methods=['GET'])
def social_page():
    """Render the social feed interface."""
    return render_template('social.html')

@social_bp.route('/posts', methods=['GET'])
def get_posts():
    """Get all posts for the social feed."""
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get posts with pagination
        posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page)
        
        posts_data = []
        for post in posts.items:
            user = User.query.get(post.user_id)
            likes_count = Like.query.filter_by(post_id=post.id).count()
            comments_count = Comment.query.filter_by(post_id=post.id).count()
            
            posts_data.append({
                "id": post.id,
                "content": post.content,
                "location": post.location,
                "created_at": post.created_at.isoformat(),
                "user": {
                    "id": user.id,
                    "username": user.username
                },
                "likes_count": likes_count,
                "comments_count": comments_count
            })
        
        return jsonify({
            "posts": posts_data,
            "pagination": {
                "page": posts.page,
                "per_page": posts.per_page,
                "total_pages": posts.pages,
                "total_items": posts.total
            }
        }), 200
    except Exception as e:
        logging.error(f"Error fetching posts: {str(e)}")
        return jsonify({"error": "An error occurred while fetching posts"}), 500

@social_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    """Create a new post."""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    content = data.get('content')
    location = data.get('location')
    
    if not content:
        return jsonify({"error": "Content is required"}), 400
    
    post = Post(
        user_id=user_id,
        content=content,
        location=location
    )
    
    try:
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            "message": "Post created successfully",
            "post": {
                "id": post.id,
                "content": post.content,
                "location": post.location,
                "created_at": post.created_at.isoformat(),
                "user": {
                    "id": user_id,
                    "username": User.query.get(user_id).username
                },
                "likes_count": 0,
                "comments_count": 0
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating post: {str(e)}")
        return jsonify({"error": "An error occurred while creating the post"}), 500

@social_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Get a specific post with its comments."""
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    user = User.query.get(post.user_id)
    likes_count = Like.query.filter_by(post_id=post.id).count()
    
    # Get comments
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.created_at).all()
    comments_data = []
    for comment in comments:
        comment_user = User.query.get(comment.user_id)
        comments_data.append({
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "user": {
                "id": comment_user.id,
                "username": comment_user.username
            }
        })
    
    return jsonify({
        "post": {
            "id": post.id,
            "content": post.content,
            "location": post.location,
            "created_at": post.created_at.isoformat(),
            "user": {
                "id": user.id,
                "username": user.username
            },
            "likes_count": likes_count,
            "comments": comments_data
        }
    }), 200

@social_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    """Add a comment to a post."""
    user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({"error": "Comment content is required"}), 400
    
    comment = Comment(
        post_id=post_id,
        user_id=user_id,
        content=content
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            "message": "Comment added successfully",
            "comment": {
                "id": comment.id,
                "content": comment.content,
                "created_at": comment.created_at.isoformat(),
                "user": {
                    "id": user_id,
                    "username": User.query.get(user_id).username
                }
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding comment: {str(e)}")
        return jsonify({"error": "An error occurred while adding the comment"}), 500

@social_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    """Like a post."""
    user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    # Check if user already liked the post
    existing_like = Like.query.filter_by(post_id=post_id, user_id=user_id).first()
    if existing_like:
        return jsonify({"error": "You already liked this post"}), 400
    
    like = Like(
        post_id=post_id,
        user_id=user_id
    )
    
    try:
        db.session.add(like)
        db.session.commit()
        
        likes_count = Like.query.filter_by(post_id=post_id).count()
        
        return jsonify({
            "message": "Post liked successfully",
            "likes_count": likes_count
        }), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error liking post: {str(e)}")
        return jsonify({"error": "An error occurred while liking the post"}), 500

@social_bp.route('/posts/<int:post_id>/unlike', methods=['POST'])
@jwt_required()
def unlike_post(post_id):
    """Unlike a post."""
    user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    # Find user's like
    like = Like.query.filter_by(post_id=post_id, user_id=user_id).first()
    if not like:
        return jsonify({"error": "You haven't liked this post"}), 400
    
    try:
        db.session.delete(like)
        db.session.commit()
        
        likes_count = Like.query.filter_by(post_id=post_id).count()
        
        return jsonify({
            "message": "Post unliked successfully",
            "likes_count": likes_count
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error unliking post: {str(e)}")
        return jsonify({"error": "An error occurred while unliking the post"}), 500
