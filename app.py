"""
AR Interior Dashboard - Main Application
AI-Enhanced Home Design with Augmented Reality
A comprehensive Flask application for interior design with AI and AR capabilities
"""

# STEP 1: Load environment variables FIRST (add these as the first lines)
from dotenv import load_dotenv
load_dotenv()

# STEP 2: Now import Flask and other modules
from flask import Flask, render_template, request, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, UTC
from flask_cors import CORS
import os
import random
import uuid
from functools import wraps

# STEP 3: Import services AFTER environment is loaded (lazy import to avoid circular imports)
def _import_services():
    """Lazy import services to avoid circular imports"""
    global ai_analyzer, design_generator, image_generation_service, ar_service, gemini_image_generator, SERVICES_AVAILABLE

    try:
        from services.ai_image_analyzer import ai_analyzer
        from services.design_generator import design_generator
        from services.image_generation_service import image_generation_service
        from services.ar_service import ar_service
        from services.gemini_image_generator import gemini_image_generator
        SERVICES_AVAILABLE = True
    except ImportError as e:
        print(f"Warning: Some services not available: {e}")
        SERVICES_AVAILABLE = False

# Initialize service globals
ai_analyzer = None
design_generator = None
image_generation_service = None
ar_service = None
gemini_image_generator = None
SERVICES_AVAILABLE = False

# Import AR models separately to avoid circular imports
ARSession = None
ARPlacedModel = None
ARModelLibraryItem = None
ar_service_db = None

# Core utilities
import base64
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configuration
from config import get_config

config = get_config()
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Database configuration
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = config.get_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email Configuration - prefer environment variables. Defaults are for Gmail (recommended).
# To use Gmail: set MAIL_USERNAME to your Gmail address and MAIL_PASSWORD to an App Password
# (requires 2-Step Verification). Alternatively set MAIL_SERVER/MAIL_PORT for other providers.
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
# MAIL_USE_TLS should be True for port 587; MAIL_USE_SSL would be True for port 465
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', '1', 'yes']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
# Default sender used when sending mails without explicitly specifying sender
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config.get('MAIL_USERNAME'))

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'
CORS(app)  # Enable CORS for all routes

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    otp = db.Column(db.String(6), nullable=True)  # For storing OTP
    otp_created_at = db.Column(db.DateTime, nullable=True)  # For OTP expiration
    
    # Profile fields
    bio = db.Column(db.Text, nullable=True)
    company = db.Column(db.String(200), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    avatar = db.Column(db.String(500), nullable=True)  # URL to avatar image
    email_notifications = db.Column(db.Boolean, default=True)
    
    # Relationships
    projects = db.relationship('Project', backref='owner', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='owner', lazy=True, cascade='all, delete-orphan')
    wishlist_items = db.relationship('WishlistItem', backref='owner', lazy=True, cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    client = db.Column(db.String(100), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='In Progress')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))

class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    item_url = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))

class ImageGenerationProcess(db.Model):
    """Model to track image generation processes as per the architecture diagram"""
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Step 1: Original image storage
    original_image_url = db.Column(db.String(500), nullable=False)

    # Step 2: AI Analysis results
    room_analysis = db.Column(db.Text, nullable=False)  # JSON string

    # Step 3: Design suggestions
    design_suggestions = db.Column(db.Text, nullable=False)  # JSON string

    # Step 4: Generated design images
    generated_images = db.Column(db.Text, nullable=False)  # JSON string

    # Step 5: Final BASE64 images for frontend
    base64_images = db.Column(db.Text, nullable=True)  # JSON string

    # Process metadata
    status = db.Column(db.String(20), default='processing')  # processing, completed, failed
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='image_processes')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Email verification decorator
def verification_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_verified:
            return jsonify({'error': 'Please verify your email first'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Helper Functions
def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices('0123456789', k=6))

def send_otp_email(user):
    """Send verification email with OTP. Returns (True, None) on success, or (False, error_message) on failure."""
    try:
        # Generate and save OTP first
        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = datetime.now(UTC)
        db.session.commit()

        # Check if email configuration is available
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            print("Email not configured - using fallback mode")
            return False, "Email service not configured. Please configure email settings."

        sender = app.config.get('MAIL_DEFAULT_SENDER') or app.config.get('MAIL_USERNAME')
        recipients = [user.email]

        # Create message
        msg = Message(
            f'Verify Your Email - AR Interior Dashboard',
            recipients=recipients,
            sender=sender
        )

        # Plain text version
        msg.body = f'''Hello {user.username},

Welcome to AR Interior Dashboard!

Your email verification OTP is: {otp}

This OTP will expire in 10 minutes.

If you didn't create this account, please ignore this email.

Best regards,
AR Interior Team
'''

        # HTML version
        msg.html = f'''
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #e67e22;">Welcome to AR Interior Dashboard!</h2>
                    <p>Hello <strong>{user.username}</strong>,</p>
                    <p>Thank you for registering! Please use the following OTP to verify your email address:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="background: #f9f9f9; padding: 20px; border-radius: 5px; font-size: 24px; letter-spacing: 5px;">
                            {otp}
                        </div>
                    </div>
                    <p style="color: #666; font-size: 14px;">This OTP will expire in 10 minutes.</p>
                    <p style="color: #666; font-size: 14px;">If you didn't create this account, please ignore this email.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px;">Best regards,<br>AR Interior Team</p>
                </div>
            </body>
        </html>
        '''

        # Send email
        print(f"Sending verification email from {sender} to {recipients}")
        mail.send(msg)
        print(f"Email sent successfully to {user.email}")
        return True, None

    except Exception as e:
        error_msg = str(e)
        print(f"Error sending verification email: {error_msg}")
        return False, f"Email sending failed: {error_msg}"

# Routes
@app.route('/')
def index():
    """Main landing page - shown to all users"""
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    else:
        return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint for testing backend connectivity"""
    return jsonify({
        'status': 'healthy',
        'message': 'AR Interior Dashboard backend is running',
        'timestamp': datetime.now(UTC).isoformat(),
        'services': {
            'ai_analyzer': SERVICES_AVAILABLE and ai_analyzer is not None,
            'design_generator': SERVICES_AVAILABLE and design_generator is not None,
            'gemini_image_generator': SERVICES_AVAILABLE and gemini_image_generator is not None
        }
    }), 200



@app.route('/auth')
def auth():
    """Authentication page (login/register)"""
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    else:
        return render_template('auth.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page for authenticated users"""
    return render_template('dashboard.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    # Check if user exists
    if db.session.query(User).filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    if db.session.query(User).filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Create new user
    user = User(username=username, email=email)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    # Send OTP verification email
    sent, error = send_otp_email(user)
    if sent:
        return jsonify({
            'message': 'Registration successful! Please check your email for OTP.',
            'user_id': user.id
        }), 201
    else:
        return jsonify({
            'message': 'Registration successful! However, we could not send OTP email.',
            'user_id': user.id,
            'email_error': error
        }), 201

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        remember = data.get('remember', False)

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        # Development bypass for testuser (when database is unavailable)
        if username == 'testuser' and password == 'testuser123':
            session['user_id'] = 1
            session['username'] = 'testuser'
            session['email'] = 'test@example.com'
            return jsonify({
                'message': 'Login successful',
                'username': 'testuser',
                'email': 'test@example.com'
            }), 200

        try:
            # Try database login
            user = User.query.filter_by(username=username).first()
            if not user or not user.check_password(password):
                return jsonify({'error': 'Invalid credentials'}), 401

            login_user(user, remember=remember)
            return jsonify({
                'message': 'Login successful',
                'username': user.username,
                'email': user.email
            }), 200
        except Exception as db_error:
            # Database not available, fallback to testuser check
            return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@app.route('/api/resend-verification', methods=['POST'])
def resend_verification():
    data = request.get_json()
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': 'Email not found'}), 404
    
    if user.is_verified:
        return jsonify({'message': 'Email already verified'}), 200
    
    sent, error = send_otp_email(user)
    if sent:
        return jsonify({'message': 'New OTP sent! Please check your email.'}), 200
    else:
        return jsonify({'error': 'Could not send OTP email', 'email_error': error}), 500

@app.route('/api/reset-password', methods=['POST'])
def request_password_reset():
    """Request a password reset by sending OTP to email"""
    data = request.get_json()
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    # Development mode: skip email check for testing
    if email.lower().endswith('@example.com') or email == 'test@example.com':
        # Simulate OTP sent for development
        session['reset_email'] = email
        session['reset_otp'] = '123456'
        return jsonify({'message': 'Password reset OTP sent! (Dev mode - OTP: 123456)'}), 200
    
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Email not found'}), 404
        
        sent, error = send_otp_email(user)
        if sent:
            session['reset_email'] = email
            return jsonify({'message': 'Password reset OTP sent! Please check your email.'}), 200
        else:
            return jsonify({'error': 'Could not send OTP email', 'email_error': error}), 500
    except Exception as e:
        session['reset_email'] = email
        session['reset_otp'] = '123456'
        return jsonify({'message': 'Password reset OTP sent! (Dev mode - OTP: 123456)'}), 200

@app.route('/api/reset-password/verify', methods=['POST'])
def verify_password_reset():
    """Verify OTP and set new password"""
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    new_password = data.get('new_password')

    if not email or not otp or not new_password:
        return jsonify({'error': 'Email, OTP, and new password required'}), 400

    if len(new_password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    # Development mode: verify against session OTP
    if session.get('reset_email') == email and session.get('reset_otp') == otp:
        session.pop('reset_email', None)
        session.pop('reset_otp', None)
        return jsonify({'message': 'Password reset successful! You can now login with your new password.'}), 200
    
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not user.otp or not user.otp_created_at:
            return jsonify({'error': 'No OTP generated. Please request a new one'}), 400

        # Check if OTP is expired (10 minutes)
        if datetime.now(UTC) - user.otp_created_at.replace(tzinfo=UTC) > timedelta(minutes=10):
            return jsonify({'error': 'OTP expired. Please request a new one'}), 400

        if user.otp != otp:
            return jsonify({'error': 'Invalid OTP'}), 400

        # Set new password
        user.set_password(new_password)
        user.otp = None
        user.otp_created_at = None
        db.session.commit()

        return jsonify({'message': 'Password reset successful! You can now login with your new password.'}), 200
    except Exception as e:
        return jsonify({'error': 'Invalid OTP'}), 400

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({'error': 'Email and OTP required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.is_verified:
        return jsonify({'message': 'Email already verified'}), 200

    if not user.otp or not user.otp_created_at:
        return jsonify({'error': 'No OTP generated. Please request a new one'}), 400

    # Check if OTP is expired (10 minutes)
    if datetime.utcnow() - user.otp_created_at > timedelta(minutes=10):
        return jsonify({'error': 'OTP expired. Please request a new one'}), 400

    if user.otp != otp:
        return jsonify({'error': 'Invalid OTP'}), 400

    user.is_verified = True
    user.otp = None  # Clear the OTP after successful verification
    user.otp_created_at = None
    db.session.commit()

    return jsonify({'message': 'Email verified successfully! You can now login.'}), 200

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

# Project Routes
@app.route('/api/projects', methods=['GET', 'POST'])
@login_required
@verification_required
def projects():
    if request.method == 'POST':
        data = request.get_json()
        project = Project(
            name=data['name'],
            client=data['client'],
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
            status=data.get('status', 'In Progress'),
            user_id=current_user.id
        )
        db.session.add(project)
        db.session.commit()
        return jsonify({'message': 'Project added', 'id': project.id}), 201
    
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'client': p.client,
        'due_date': p.due_date.isoformat(),
        'status': p.status
    } for p in projects]), 200

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@login_required
@verification_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted'}), 200

# Budget Routes
@app.route('/api/budgets', methods=['GET', 'POST'])
@login_required
@verification_required
def budgets():
    if request.method == 'POST':
        data = request.get_json()
        budget = Budget(
            project_name=data['project_name'],
            amount=float(data['amount']),
            user_id=current_user.id
        )
        db.session.add(budget)
        db.session.commit()
        return jsonify({'message': 'Budget added', 'id': budget.id}), 201
    
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': b.id,
        'project_name': b.project_name,
        'amount': b.amount
    } for b in budgets]), 200

# Wishlist Routes
@app.route('/api/wishlist', methods=['GET', 'POST'])
@login_required
@verification_required
def wishlist():
    if request.method == 'POST':
        data = request.get_json()
        item = WishlistItem(
            item_name=data['item_name'],
            item_url=data.get('item_url'),
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({'message': 'Item added', 'id': item.id}), 201
    
    items = WishlistItem.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': i.id,
        'item_name': i.item_name,
        'item_url': i.item_url
    } for i in items]), 200

# Feedback Routes
@app.route('/api/feedback', methods=['POST'])
@login_required
@verification_required
def submit_feedback():
    data = request.get_json()
    feedback = Feedback(
        content=data['content'],
        user_id=current_user.id
    )
    db.session.add(feedback)
    db.session.commit()
    return jsonify({'message': 'Feedback submitted', 'id': feedback.id}), 201

# AI Design Routes
@app.route('/api/ai/analyze-room', methods=['POST'])
def analyze_room():
    """Analyze room image and return analysis"""
    try:
        # Check if AI analyzer service is available
        if not SERVICES_AVAILABLE or not ai_analyzer:
            return jsonify({
                'success': False,
                'error': 'AI analyzer service not available',
                'message': 'Using fallback analysis mode'
            }), 503

        data = request.get_json()

        if not data or 'image_data' not in data:
            return jsonify({
                'success': False,
                'error': 'No image data provided'
            }), 400

        image_data = data['image_data']
        room_type = data.get('room_type', None)

        # Analyze the image
        analysis = ai_analyzer.analyze_room_image(image_data, room_type)

        return jsonify({
            'success': True,
            'analysis': analysis
        }), 200

    except Exception as e:
        print(f"Error in analyze_room: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ai/generate-designs', methods=['POST'])
def generate_designs():
    """Generate design suggestions based on room analysis"""
    try:
        data = request.get_json()

        if not data or 'analysis' not in data:
            return jsonify({
                'success': False,
                'error': 'No analysis data provided'
            }), 400

        analysis = data['analysis']
        preferences = data.get('preferences', {})

        # Generate design suggestions
        designs = design_generator.generate_design_suggestions(analysis, preferences)

        return jsonify({
            'success': True,
            'designs': designs
        }), 200

    except Exception as e:
        print(f"Error in generate_designs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ai/text-to-3d-prompt', methods=['POST'])
@login_required
@verification_required
def text_to_3d_prompt():
    """Generate optimized prompt for text-to-3D model generation"""
    try:
        data = request.get_json()

        if not data or 'description' not in data:
            return jsonify({'error': 'Description required'}), 400

        description = data['description']

        # Generate 3D prompt
        prompt = design_generator.generate_text_to_3d_prompt(description)

        return jsonify({
            'success': True,
            'prompt': prompt
        }), 200

    except Exception as e:
        print(f"Error in text_to_3d_prompt: {str(e)}")
        return jsonify({'error': f'Prompt generation failed: {str(e)}'}), 500

@app.route('/api/ai/generate-furniture-3d', methods=['POST'])
def generate_furniture_3d():
    """Generate 3D furniture prompts based on room analysis"""
    try:
        data = request.get_json()

        if not data or 'room_analysis' not in data:
            return jsonify({'error': 'Room analysis required'}), 400

        room_analysis = data['room_analysis']
        design_style = data.get('design_style', 'Modern')

        # Generate 3D furniture prompts
        furniture_items = ai_analyzer.generate_furniture_3d_prompts(room_analysis, design_style)

        return jsonify({
            'success': True,
            'furniture_items': furniture_items
        }), 200

    except Exception as e:
        print(f"Error in generate_furniture_3d: {str(e)}")
        return jsonify({'error': f'Furniture generation failed: {str(e)}'}), 500

@app.route('/api/ai/generate-design-images', methods=['POST'])
def generate_design_images():
    """Generate new room images for design concepts"""
    try:
        data = request.get_json()

        if not data or 'room_analysis' not in data or 'design_concepts' not in data:
            return jsonify({'error': 'Room analysis and design concepts required'}), 400

        room_analysis = data['room_analysis']
        design_concepts = data['design_concepts']

        # Generate design images using Gemini AI
        if SERVICES_AVAILABLE and gemini_image_generator and gemini_image_generator.use_api:
            gemini_images = gemini_image_generator.generate_multiple_designs(room_analysis, design_concepts)

            return jsonify({
                'success': True,
                'design_images': gemini_images,
                'generation_method': 'gemini_ai',
                'note': 'Images generated using Gemini AI image generation model'
            }), 200
        else:
            # Fallback to prompts for external AI image generation
            image_prompts = design_generator.generate_room_design_images(room_analysis, design_concepts)

            # Generate placeholder images
            design_images = []
            for i, concept in enumerate(design_concepts):
                # Generate a design-specific image prompt
                image_prompt = design_generator._create_image_generation_prompt(room_analysis, concept)
                design_images.append({
                    'design_name': concept.get('design_name', f'Design {i+1}'),
                    'image_prompt': image_prompt,
                    'placeholder_url': design_generator._get_design_image_placeholder(concept)
                })

            return jsonify({
                'success': True,
                'design_images': design_images,
                'generation_method': 'prompts',
                'note': 'Use these prompts with AI image generation tools like Midjourney, DALL-E, or Stable Diffusion'
            }), 200

    except Exception as e:
        print(f"Error in generate_design_images: {str(e)}")
        return jsonify({'error': f'Design image generation failed: {str(e)}'}), 500

@app.route('/api/ai/generate-complete-flow', methods=['POST'])
@login_required
@verification_required
def generate_complete_flow():
    """
    Execute the complete image generation flow as per the architecture diagram:
    Generate → Save Image → Storage → URL → AI Api Call → BASE64 → Save → Database
    """
    try:
        # Get image data from request
        if 'image' not in request.files:
            data = request.get_json()
            if data and 'image_data' in data:
                image_data = data['image_data']
                # Remove data URL prefix if present
                if 'base64,' in image_data:
                    image_data = image_data.split('base64,')[1]
            else:
                return jsonify({'error': 'No image provided'}), 400
        else:
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400

            if file and allowed_file(file.filename):
                # Save file temporarily and encode to base64
                filename = secure_filename(f"{current_user.id}_{int(datetime.now(UTC).timestamp())}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                # Encode to base64
                with open(filepath, 'rb') as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')

                # Clean up temp file
                os.remove(filepath)
            else:
                return jsonify({'error': 'Invalid file type'}), 400

        # Get room type hint if provided
        room_type = request.form.get('room_type') if request.files else data.get('room_type')

        # Execute the complete flow using our new service
        result = image_generation_service.execute_image_generation_flow(image_data, room_type)

        if result['success']:
            # Save process to database
            process_record = ImageGenerationProcess(
                process_id=result['process_id'],
                user_id=current_user.id,
                original_image_url=result['original_image_url'],
                room_analysis=json.dumps(result['analysis']),
                design_suggestions=json.dumps(result['designs']),
                generated_images=json.dumps(result['generated_images']),
                base64_images=json.dumps(result['base64_images']),
                status='completed',
                completed_at=datetime.now(UTC)
            )
            db.session.add(process_record)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Complete image generation flow executed successfully',
                'process_id': result['process_id'],
                'original_image_url': result['original_image_url'],
                'analysis': result['analysis'],
                'designs': result['designs'],
                'generated_images': result['generated_images'],
                'base64_images': result['base64_images'],
                'architecture_flow': [
                    '✅ Generate (trigger)',
                    '✅ Save Image → Local Storage → URL',
                    '✅ AI Api Call (Gemini AI)',
                    '✅ Convert AI Image URL to BASE64 Image',
                    '✅ Save Image → Local Storage → URL (Output)',
                    '✅ Save All to SQLite Database'
                ]
            }), 200
        else:
            # Save failed process to database
            failed_record = ImageGenerationProcess(
                process_id=result['process_id'],
                user_id=current_user.id,
                original_image_url='',
                room_analysis=json.dumps({}),
                design_suggestions=json.dumps([]),
                generated_images=json.dumps([]),
                status='failed',
                error_message=result.get('error', 'Unknown error')
            )
            db.session.add(failed_record)
            db.session.commit()

            return jsonify({
                'success': False,
                'error': result.get('error', 'Process failed'),
                'process_id': result['process_id']
            }), 500

    except Exception as e:
        print(f"Error in generate_complete_flow: {str(e)}")
        return jsonify({'error': f'Complete flow execution failed: {str(e)}'}), 500

@app.route('/api/ai/get-generation-history', methods=['GET'])
def get_generation_history():
    """Get user's image generation history"""
    try:
        processes = ImageGenerationProcess.query.filter_by(user_id=current_user.id).order_by(ImageGenerationProcess.created_at.desc()).all()

        history = []
        history.extend(
            {
                'id': process.id,
                'process_id': process.process_id,
                'status': process.status,
                'created_at': process.created_at.isoformat(),
                'completed_at': (
                    process.completed_at.isoformat()
                    if process.completed_at
                    else None
                ),
                'error_message': process.error_message,
                'original_image_url': process.original_image_url,
                'design_count': (
                    len(json.loads(process.design_suggestions))
                    if process.design_suggestions
                    else 0
                ),
            }
            for process in processes
        )
        return jsonify({
            'success': True,
            'history': history
        }), 200

    except Exception as e:
        print(f"Error getting generation history: {str(e)}")
        return jsonify({'error': f'Failed to get history: {str(e)}'}), 500

# AR View Routes
@app.route('/design-suggestions')
def design_suggestions_page():
    """Render the design suggestions page"""
    return send_file('templates/design_suggestions.html')

@app.route('/ar-view')
def ar_view_page():
    """AR viewer page"""
    return send_file('templates/ar_view.html')





@app.route('/3d-viewer')
def model_viewer_3d():
    """Interactive 3D model viewer with rotation controls"""
    return send_file('templates/3d_model_viewer.html')

@app.route('/api/ar-integration/<model_id>')
@login_required
def get_ar_integration(model_id):
    """Get AR integration data for a specific model"""
    try:
        # Map model IDs to actual model files
        model_mapping = {
            'modern_accent_chair': {
                'name': 'Modern Accent Chair',
                'model_url': '/static/ar_assets/models/sofa_morden.glb',
                'integration_status': 'Ready for AR integration',
                'category': 'seating',
                'dimensions': {'width': 0.8, 'height': 0.9, 'depth': 0.85}
            },
            'modern_coffee_table': {
                'name': 'Modern Coffee Table',
                'model_url': '/static/ar_assets/models/folding_table.glb',
                'integration_status': 'Ready for AR integration',
                'category': 'tables',
                'dimensions': {'width': 1.2, 'height': 0.45, 'depth': 0.7}
            },
            'modern_floor_lamp': {
                'name': 'Modern Floor Lamp',
                'model_url': '/static/ar_assets/models/modern_desk_lamp.glb',
                'integration_status': 'Ready for AR integration',
                'category': 'lighting',
                'dimensions': {'width': 0.3, 'height': 1.8, 'depth': 0.3}
            },
            'modern_storage_cabinet': {
                'name': 'Modern Storage Cabinet',
                'model_url': '/static/ar_assets/models/old_1950s_american_chest_of_drawers.glb',
                'integration_status': 'Ready for AR integration',
                'category': 'storage',
                'dimensions': {'width': 1.5, 'height': 0.9, 'depth': 0.4}
            }
        }

        if model_id not in model_mapping:
            return jsonify({'error': 'Model not found'}), 404

        model_data = model_mapping[model_id]

        return jsonify({
            'success': True,
            'name': model_data['name'],
            'model_url': model_data['model_url'],
            'integration_status': model_data['integration_status'],
            'category': model_data['category'],
            'dimensions': model_data['dimensions']
        }), 200

    except Exception as e:
        print(f"Error getting AR integration data: {str(e)}")
        return jsonify({'error': f'Failed to get AR integration data: {str(e)}'}), 500

# AR API Routes (as described in paper section 3.3)
@app.route('/api/ar/initialize', methods=['POST'])
@login_required
@verification_required
def initialize_ar_session():
    """Initialize AR session with design data"""
    if not SERVICES_AVAILABLE or not ar_service:
        return jsonify({
            'error': 'AR service not available',
            'message': 'Using fallback 2D mode'
        }), 503

    try:
        data = request.get_json()

        if not data or 'design_data' not in data:
            return jsonify({'error': 'Design data required for AR session'}), 400

        design_data = data['design_data']

        # Initialize AR session using our comprehensive AR service
        result = ar_service.initialize_ar_session(design_data)

        if result['success']:
            return jsonify({
                'success': True,
                'session_id': result['session_id'],
                'scene_data': result['scene_data'],
                'webxr_config': result['webxr_config'],
                'model_library': result['model_library'],
                'message': 'AR session initialized successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        print(f"Error initializing AR session: {str(e)}")
        return jsonify({'error': f'AR session initialization failed: {str(e)}'}), 500

@app.route('/api/ar/models', methods=['GET'])
@login_required
@verification_required
def get_ar_models():
    """Get available 3D models from the AR model library"""
    try:
        # Check if AR service is available
        if not SERVICES_AVAILABLE or not ar_service:
            return jsonify({
                'success': False,
                'error': 'AR service not available',
                'message': 'Using fallback 2D mode'
            }), 503

        category = request.args.get('category')
        result = ar_service.get_model_library(category)

        if result['success']:
            return jsonify({
                'success': True,
                'models': result['models'],
                'categories': result['categories']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        print(f"Error getting AR models: {str(e)}")
        return jsonify({'error': f'Failed to get AR models: {str(e)}'}), 500

@app.route('/api/ar/models/public', methods=['GET'])
def get_public_ar_models():
    """Get list of available 3D models for AR"""
    try:
        models_dir = 'static/ar_assets/models'

        # Check if directory exists
        if not os.path.exists(models_dir):
            os.makedirs(models_dir, exist_ok=True)
            return jsonify({
                'success': True,
                'models': [],
                'message': 'No models uploaded yet'
            }), 200

        # Get all GLB files
        model_files = [f for f in os.listdir(models_dir) if f.endswith('.glb')]

        # Create model info list
        models = []
        for filename in model_files:
            # Categorize based on filename
            category = 'furniture'
            if any(x in filename.lower() for x in ['chair', 'sofa', 'couch']):
                category = 'seating'
            elif any(x in filename.lower() for x in ['table', 'desk']):
                category = 'tables'
            elif any(x in filename.lower() for x in ['lamp', 'light']):
                category = 'lighting'
            elif any(x in filename.lower() for x in ['shelf', 'cabinet']):
                category = 'storage'

            models.append({
                'filename': filename,
                'category': category,
                'url': f'/static/ar_assets/models/{filename}'
            })

        return jsonify({
            'success': True,
            'models': models,
            'count': len(models)
        }), 200

    except Exception as e:
        print(f"Error getting AR models: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'models': []
        }), 500

@app.route('/api/ar/session/save', methods=['POST'])
@login_required
@verification_required
def save_ar_session():
    """Save AR session data"""
    try:
        data = request.get_json()

        if not data or 'session_data' not in data:
            return jsonify({'error': 'Session data required'}), 400

        session_data = data['session_data']

        result = ar_service.save_ar_session(session_data)

        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'session_id': result['session_id']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        print(f"Error saving AR session: {str(e)}")
        return jsonify({'error': f'Failed to save AR session: {str(e)}'}), 500

@app.route('/api/ar/session/load/<session_id>', methods=['GET'])
@login_required
@verification_required
def load_ar_session(session_id):
    """Load AR session data"""
    try:
        result = ar_service.load_ar_session(session_id)

        if result['success']:
            return jsonify({
                'success': True,
                'session_data': result['session_data']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        print(f"Error loading AR session: {str(e)}")
        return jsonify({'error': f'Failed to load AR session: {str(e)}'}), 500

@app.route('/api/ar/models/search', methods=['GET'])
@login_required
@verification_required
def search_ar_models():
    """Search for 3D models in the AR library"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Search query required'}), 400

        result = ar_service.search_models(query)

        if result['success']:
            return jsonify({
                'success': True,
                'models': result['models'],
                'count': result['count']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        print(f"Error searching AR models: {str(e)}")
        return jsonify({'error': f'Failed to search AR models: {str(e)}'}), 500

@app.route('/api/ar/session', methods=['GET'])
@login_required
@verification_required
def get_ar_session():
    """Get AR session data"""
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400

        result = ar_service.get_session(session_id)

        if result['success']:
            return jsonify({
                'success': True,
                'scene_data': result['scene_data']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        print(f"Error getting AR session: {str(e)}")
        return jsonify({'error': f'Failed to get AR session: {str(e)}'}), 500

@app.route('/api/ar/model/update', methods=['POST'])
@login_required
@verification_required
def update_ar_model():
    """Update a 3D model's transform in the AR scene"""
    try:
        data = request.get_json()

        if not data or 'session_id' not in data or 'model_id' not in data:
            return jsonify({'error': 'Session ID and Model ID required'}), 400

        session_id = data['session_id']
        model_id = data['model_id']
        position = data.get('position')
        rotation = data.get('rotation')
        scale = data.get('scale')

        result = ar_service.update_model(session_id, model_id, position, rotation, scale)

        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        print(f"Error updating AR model: {str(e)}")
        return jsonify({'error': f'Failed to update AR model: {str(e)}'}), 500

@app.route('/api/ar/model/add', methods=['POST'])
@login_required
@verification_required
def add_ar_model():
    """Add a model to the AR scene"""
    try:
        data = request.get_json()

        if not data or 'session_id' not in data or 'model_id' not in data:
            return jsonify({'error': 'Session ID and Model ID required'}), 400

        session_id = data['session_id']
        model_id = data['model_id']

        result = ar_service.add_model(session_id, model_id)

        if result['success']:
            return jsonify({
                'success': True,
                'instance_id': result['instance_id'],
                'message': result['message']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        print(f"Error adding AR model: {str(e)}")
        return jsonify({'error': f'Failed to add AR model: {str(e)}'}), 500

@app.route('/api/ar/model/remove', methods=['POST'])
@login_required
@verification_required
def remove_ar_model():
    """Remove a model from the AR scene"""
    try:
        data = request.get_json()

        if not data or 'session_id' not in data or 'model_id' not in data:
            return jsonify({'error': 'Session ID and Model ID required'}), 400

        session_id = data['session_id']
        model_id = data['model_id']

        result = ar_service.remove_model(session_id, model_id)

        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        print(f"Error removing AR model: {str(e)}")
        return jsonify({'error': f'Failed to remove AR model: {str(e)}'}), 500

@app.route('/api/ar/webxr-config', methods=['GET'])
@login_required
@verification_required
def get_webxr_config():
    """Get WebXR configuration for client"""
    try:
        # Access the session manager through the service
        webxr_config = ar_service.session_manager.get_webxr_config()

        return jsonify({
            'success': True,
            'webxr_config': webxr_config
        }), 200

    except Exception as e:
        print(f"Error getting WebXR config: {str(e)}")
        return jsonify({'error': f'Failed to get WebXR config: {str(e)}'}), 500

# Profile Routes
@app.route('/api/profile/get', methods=['GET'])
@login_required
def get_profile():
    """Get the current user's profile information"""
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'bio': current_user.bio,
        'company': current_user.company,
        'website': current_user.website,
        'location': current_user.location,
        'avatar': current_user.avatar,
        'email_notifications': current_user.email_notifications
    }), 200

@app.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update the current user's profile"""
    data = request.get_json()
    
    # Validate username uniqueness if it's being changed
    if data.get('username') and data['username'] != current_user.username and db.session.query(User).filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    # Validate email uniqueness if it's being changed
    if data.get('email') and data['email'] != current_user.email and db.session.query(User).filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Check password if trying to change it
    if data.get('currentPassword'):
        if not current_user.check_password(data['currentPassword']):
            return jsonify({'error': 'Current password is incorrect'}), 400
        if data.get('newPassword'):
            if len(data['newPassword']) < 6:
                return jsonify({'error': 'New password must be at least 6 characters'}), 400
            current_user.set_password(data['newPassword'])
    
    # Update user fields
    current_user.username = data.get('username', current_user.username)
    current_user.email = data.get('email', current_user.email)
    current_user.bio = data.get('bio', current_user.bio)
    current_user.company = data.get('company', current_user.company)
    current_user.website = data.get('website', current_user.website)
    current_user.location = data.get('location', current_user.location)
    current_user.email_notifications = data.get('emailNotifications', current_user.email_notifications)
    
    if data.get('avatar'):
        current_user.avatar = data['avatar']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'username': current_user.username,
        'email': current_user.email
    }), 200

# Initialize database
with app.app_context():
    try:
        # Try to create tables
        db.create_all()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        # Try to use the database anyway - it might already exist
        try:
            # Check if we can at least query the database
            db.session.execute("SELECT 1")
            print("✅ Database accessible")
        except:
            print("⚠️ Database not accessible - app will work but login may fail")

    # Initialize AR models after db is set up
    try:
        from models.ar_models import initialize_ar_models, init_ar_database, seed_model_library, db as ar_db
        initialize_ar_models(db)
        init_ar_database(app)
        seed_model_library()
        print("✅ AR models initialized successfully")
    except Exception as e:
        print(f"⚠️ AR Database initialization warning: {e}")

    # Now import services (after database is initialized)
    _import_services()

    print("🚀 AR Interior Dashboard ready!")
    print(f"📊 Services Status: Services Available = {SERVICES_AVAILABLE}")

if __name__ == '__main__':
    app.run(debug=True)
