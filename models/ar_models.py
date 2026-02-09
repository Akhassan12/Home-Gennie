"""
Database Models for AR Sessions Persistence
Add these models to your database setup

This module now uses lazy initialization to avoid circular imports.
Call initialize_ar_models() after Flask app and db are set up.
"""

from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy

# Global variables - initialized after db setup
db = None
ARSession = None
ARPlacedModel = None
ARModelLibraryItem = None
GeneratedDesignTemplate = None

def initialize_ar_models(database_instance):
    """Initialize AR models after db is set up"""
    global db, ARSession, ARPlacedModel, ARModelLibraryItem, GeneratedDesignTemplate
    db = database_instance

    class ARSession(db.Model):
        """AR Session database model"""
        __tablename__ = 'ar_sessions'

        id = db.Column(db.Integer, primary_key=True)
        session_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
        room_type = db.Column(db.String(50), nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

        # Session configuration
        lighting_config = db.Column(db.Text)  # JSON string
        environment_config = db.Column(db.Text)  # JSON string

        # Timestamps
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        last_accessed = db.Column(db.DateTime, default=datetime.utcnow)

        # Status
        is_active = db.Column(db.Boolean, default=True)
        is_saved = db.Column(db.Boolean, default=False)

        # Relationships
        models = db.relationship('ARPlacedModel', backref='session', lazy='dynamic', cascade='all, delete-orphan')

        def to_dict(self):
            """Convert session to dictionary"""
            return {
                'session_id': self.session_id,
                'room_type': self.room_type,
                'lighting': json.loads(self.lighting_config) if self.lighting_config else {},
                'environment': json.loads(self.environment_config) if self.environment_config else {},
                'created_at': self.created_at.isoformat(),
                'updated_at': self.updated_at.isoformat(),
                'is_saved': self.is_saved,
                'models': [model.to_dict() for model in self.models.all()]
            }

        def update_access_time(self):
            """Update last accessed timestamp"""
            self.last_accessed = datetime.utcnow()
            db.session.commit()

    class ARPlacedModel(db.Model):
        """Placed 3D model in AR session"""
        __tablename__ = 'ar_placed_models'

        id = db.Column(db.Integer, primary_key=True)
        instance_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
        session_id = db.Column(db.String(100), db.ForeignKey('ar_sessions.session_id'), nullable=False)

        # Model information
        model_id = db.Column(db.String(100), nullable=False)
        model_name = db.Column(db.String(200))
        category = db.Column(db.String(50))
        glb_url = db.Column(db.String(500))

        # Transform data
        position_x = db.Column(db.Float, default=0.0)
        position_y = db.Column(db.Float, default=0.0)
        position_z = db.Column(db.Float, default=0.0)

        rotation_x = db.Column(db.Float, default=0.0)
        rotation_y = db.Column(db.Float, default=0.0)
        rotation_z = db.Column(db.Float, default=0.0)

        scale_x = db.Column(db.Float, default=1.0)
        scale_y = db.Column(db.Float, default=1.0)
        scale_z = db.Column(db.Float, default=1.0)

        # Dimensions
        width = db.Column(db.Float)
        height = db.Column(db.Float)
        depth = db.Column(db.Float)

        # Metadata
        placed_at = db.Column(db.DateTime, default=datetime.utcnow)
        last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def to_dict(self):
            """Convert model to dictionary"""
            return {
                'instance_id': self.instance_id,
                'model_id': self.model_id,
                'name': self.model_name,
                'category': self.category,
                'glb_url': self.glb_url,
                'transform': {
                    'position': {
                        'x': self.position_x,
                        'y': self.position_y,
                        'z': self.position_z
                    },
                    'rotation': {
                        'x': self.rotation_x,
                        'y': self.rotation_y,
                        'z': self.rotation_z
                    },
                    'scale': {
                        'x': self.scale_x,
                        'y': self.scale_y,
                        'z': self.scale_z
                    }
                },
                'dimensions': {
                    'width': self.width,
                    'height': self.height,
                    'depth': self.depth
                },
                'placed_at': self.placed_at.isoformat()
            }

        def update_transform(self, position=None, rotation=None, scale=None):
            """Update model transform"""
            if position:
                self.position_x = position.get('x', self.position_x)
                self.position_y = position.get('y', self.position_y)
                self.position_z = position.get('z', self.position_z)

            if rotation:
                self.rotation_x = rotation.get('x', self.rotation_x)
                self.rotation_y = rotation.get('y', self.rotation_y)
                self.rotation_z = rotation.get('z', self.rotation_z)

            if scale:
                self.scale_x = scale.get('x', self.scale_x)
                self.scale_y = scale.get('y', self.scale_y)
                self.scale_z = scale.get('z', self.scale_z)

            self.last_modified = datetime.utcnow()

    class ARModelLibraryItem(db.Model):
        """3D Model library item"""
        __tablename__ = 'ar_model_library'

        id = db.Column(db.Integer, primary_key=True)
        model_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
        name = db.Column(db.String(200), nullable=False)
        category = db.Column(db.String(50), nullable=False, index=True)

        # Model files
        glb_url = db.Column(db.String(500), nullable=False)
        thumbnail_url = db.Column(db.String(500))

        # Dimensions
        width = db.Column(db.Float)
        height = db.Column(db.Float)
        depth = db.Column(db.Float)

        # Metadata
        description = db.Column(db.Text)
        tags = db.Column(db.Text)  # JSON array of tags
        style = db.Column(db.String(50))

        # Stats
        usage_count = db.Column(db.Integer, default=0)
        rating = db.Column(db.Float, default=0.0)

        # Status
        is_active = db.Column(db.Boolean, default=True)
        is_premium = db.Column(db.Boolean, default=False)

        created_at = db.Column(db.DateTime, default=datetime.utcnow)

        def to_dict(self):
            """Convert to dictionary"""
            return {
                'model_id': self.model_id,
                'name': self.name,
                'category': self.category,
                'glb_url': self.glb_url,
                'thumbnail_url': self.thumbnail_url,
                'dimensions': {
                    'width': self.width,
                    'height': self.height,
                    'depth': self.depth
                },
                'description': self.description,
                'tags': json.loads(self.tags) if self.tags else [],
                'style': self.style,
                'usage_count': self.usage_count,
                'rating': self.rating,
                'is_premium': self.is_premium
            }

        def increment_usage(self):
            """Increment usage counter"""
            self.usage_count += 1
            db.session.commit()

    class GeneratedDesignTemplate(db.Model):
        """Generated design template images for fallback use"""
        __tablename__ = 'generated_design_templates'

        id = db.Column(db.Integer, primary_key=True)
        template_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
        design_name = db.Column(db.String(200), nullable=False)
        design_style = db.Column(db.String(50), nullable=False, index=True)

        # Room information
        room_type = db.Column(db.String(50), nullable=False)
        room_size = db.Column(db.String(20))
        room_shape = db.Column(db.String(20))

        # Design specifications
        color_palette = db.Column(db.Text)  # JSON array of colors
        key_elements = db.Column(db.Text)   # JSON array of elements
        design_concept = db.Column(db.Text) # JSON object with full design concept

        # Generated image data
        image_data = db.Column(db.Text, nullable=False)  # Base64 encoded image
        image_format = db.Column(db.String(10), default='png')
        image_width = db.Column(db.Integer, default=800)
        image_height = db.Column(db.Integer, default=600)

        # Generation metadata
        generated_by = db.Column(db.String(20), default='gemini')  # gemini, fallback, etc.
        api_key_status = db.Column(db.String(20), default='working')  # working, failed, expired
        generation_prompt = db.Column(db.Text)  # The prompt used for generation

        # Usage tracking
        usage_count = db.Column(db.Integer, default=0)
        last_used = db.Column(db.DateTime)

        # Status
        is_active = db.Column(db.Boolean, default=True)
        is_fallback = db.Column(db.Boolean, default=False)  # Marked as fallback template

        # Timestamps
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def to_dict(self):
            """Convert template to dictionary"""
            return {
                'template_id': self.template_id,
                'design_name': self.design_name,
                'design_style': self.design_style,
                'room_type': self.room_type,
                'room_size': self.room_size,
                'room_shape': self.room_shape,
                'color_palette': json.loads(self.color_palette) if self.color_palette else [],
                'key_elements': json.loads(self.key_elements) if self.key_elements else [],
                'design_concept': json.loads(self.design_concept) if self.design_concept else {},
                'image_data': self.image_data,
                'image_format': self.image_format,
                'image_dimensions': {
                    'width': self.image_width,
                    'height': self.image_height
                },
                'generated_by': self.generated_by,
                'api_key_status': self.api_key_status,
                'usage_count': self.usage_count,
                'last_used': self.last_used.isoformat() if self.last_used else None,
                'is_fallback': self.is_fallback,
                'created_at': self.created_at.isoformat()
            }

        def increment_usage(self):
            """Increment usage counter and update last used"""
            self.usage_count += 1
            self.last_used = datetime.utcnow()
            db.session.commit()

        def mark_as_fallback(self):
            """Mark this template as a fallback option"""
            self.is_fallback = True
            db.session.commit()

        def update_api_status(self, status):
            """Update API key status"""
            self.api_key_status = status
            db.session.commit()

    # Make classes available globally after initialization
    globals()['ARSession'] = ARSession
    globals()['ARPlacedModel'] = ARPlacedModel
    globals()['ARModelLibraryItem'] = ARModelLibraryItem
    globals()['GeneratedDesignTemplate'] = GeneratedDesignTemplate

    print("✅ AR models initialized successfully")




# Database initialization and helper functions
def init_ar_database(app):
    """Initialize AR database with app"""
    db.init_app(app)

    with app.app_context():
        try:
            db.create_all()
            print("AR Database tables created successfully")
        except Exception as e:
            print(f"⚠️ AR Database warning: {e}")


def seed_model_library():
    """Seed the model library with initial 3D models"""
    models = [
        {
            'model_id': 'modern_sofa_01',
            'name': 'Modern Sofa',
            'category': 'seating',
            'glb_url': '/static/ar_assets/models/modern_sofa.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/modern_sofa.jpg',
            'width': 2.0,
            'height': 0.85,
            'depth': 0.95,
            'description': 'Contemporary three-seater sofa with clean lines',
            'tags': json.dumps(['modern', 'sofa', 'seating', 'living room']),
            'style': 'modern'
        },
        {
            'model_id': 'accent_chair_01',
            'name': 'Accent Chair',
            'category': 'seating',
            'glb_url': '/static/ar_assets/models/accent_chair.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/accent_chair.jpg',
            'width': 0.75,
            'height': 0.90,
            'depth': 0.85,
            'description': 'Stylish accent chair perfect for reading nooks',
            'tags': json.dumps(['chair', 'accent', 'seating', 'modern']),
            'style': 'contemporary'
        },
        {
            'model_id': 'coffee_table_01',
            'name': 'Coffee Table',
            'category': 'tables',
            'glb_url': '/static/ar_assets/models/coffee_table.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/coffee_table.jpg',
            'width': 1.2,
            'height': 0.45,
            'depth': 0.7,
            'description': 'Modern coffee table with storage',
            'tags': json.dumps(['table', 'coffee table', 'living room', 'storage']),
            'style': 'modern'
        },
        {
            'model_id': 'bookshelf_01',
            'name': 'Modern Bookshelf',
            'category': 'storage',
            'glb_url': '/static/ar_assets/models/bookshelf.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/bookshelf.jpg',
            'width': 1.0,
            'height': 2.0,
            'depth': 0.35,
            'description': 'Tall bookshelf with multiple shelves',
            'tags': json.dumps(['bookshelf', 'storage', 'tall', 'modern']),
            'style': 'modern'
        },
        {
            'model_id': 'floor_lamp_01',
            'name': 'Floor Lamp',
            'category': 'lighting',
            'glb_url': '/static/ar_assets/models/floor_lamp.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/floor_lamp.jpg',
            'width': 0.3,
            'height': 1.7,
            'depth': 0.3,
            'description': 'Elegant floor lamp with fabric shade',
            'tags': json.dumps(['lamp', 'floor lamp', 'lighting', 'modern']),
            'style': 'contemporary'
        },
        {
            'model_id': 'dining_table_01',
            'name': 'Dining Table',
            'category': 'tables',
            'glb_url': '/static/ar_assets/models/dining_table.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/dining_table.jpg',
            'width': 1.8,
            'height': 0.75,
            'depth': 1.0,
            'description': 'Large dining table for 6 people',
            'tags': json.dumps(['dining table', 'table', 'dining room', 'large']),
            'style': 'modern'
        },
        {
            'model_id': 'bed_queen_01',
            'name': 'Queen Bed',
            'category': 'beds',
            'glb_url': '/static/ar_assets/models/queen_bed.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/queen_bed.jpg',
            'width': 1.6,
            'height': 0.6,
            'depth': 2.0,
            'description': 'Comfortable queen size bed with headboard',
            'tags': json.dumps(['bed', 'queen bed', 'bedroom', 'sleep']),
            'style': 'modern'
        },
        {
            'model_id': 'nightstand_01',
            'name': 'Nightstand',
            'category': 'storage',
            'glb_url': '/static/ar_assets/models/nightstand.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/nightstand.jpg',
            'width': 0.5,
            'height': 0.6,
            'depth': 0.4,
            'description': 'Bedside table with drawer',
            'tags': json.dumps(['nightstand', 'bedside table', 'storage', 'bedroom']),
            'style': 'modern'
        },
        {
            'model_id': 'plant_large_01',
            'name': 'Large Plant',
            'category': 'decor',
            'glb_url': '/static/ar_assets/models/plant_large.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/plant_large.jpg',
            'width': 0.4,
            'height': 1.2,
            'depth': 0.4,
            'description': 'Large decorative plant in ceramic pot',
            'tags': json.dumps(['plant', 'decor', 'green', 'nature']),
            'style': 'natural'
        },
        {
            'model_id': 'rug_large_01',
            'name': 'Area Rug',
            'category': 'decor',
            'glb_url': '/static/ar_assets/models/area_rug.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/area_rug.jpg',
            'width': 2.4,
            'height': 0.02,
            'depth': 1.8,
            'description': 'Large area rug with modern pattern',
            'tags': json.dumps(['rug', 'carpet', 'decor', 'flooring']),
            'style': 'modern'
        }
    ]

    for model_data in models:
        existing = ARModelLibraryItem.query.filter_by(model_id=model_data['model_id']).first()
        if not existing:
            model = ARModelLibraryItem(**model_data)
            db.session.add(model)

    db.session.commit()
    print(f"Seeded {len(models)} models to library")


# AR Service with Database Integration
class ARServiceWithDB:
    """AR Service with database persistence"""

    def __init__(self):
        self.session_manager = None  # Will be initialized with existing ARSessionManager

    def initialize_with_manager(self, session_manager):
        """Initialize with existing session manager"""
        self.session_manager = session_manager

    def create_session_db(self, room_type: str, user_id: int = None, design_data: dict = None) -> ARSession:
        """Create new AR session in database"""
        from services.ar_service import ARScene
        import uuid

        session_id = str(uuid.uuid4())

        # Create in-memory scene
        scene = ARScene(session_id, room_type)

        # Create database record
        db_session = ARSession(
            session_id=session_id,
            room_type=room_type,
            user_id=user_id,
            lighting_config=json.dumps(scene.lighting),
            environment_config=json.dumps(scene.environment)
        )

        db.session.add(db_session)
        db.session.commit()

        # Store in session manager
        self.session_manager.active_sessions[session_id] = scene

        return db_session

    def get_session_db(self, session_id: str) -> ARSession:
        """Get AR session from database"""
        return ARSession.query.filter_by(session_id=session_id).first()

    def add_model_db(self, session_id: str, model_id: str) -> ARPlacedModel:
        """Add model to session in database"""
        import uuid

        # Get session
        db_session = ARSession.query.filter_by(session_id=session_id).first()
        if not db_session:
            return None

        # Get model from library
        library_model = ARModelLibraryItem.query.filter_by(model_id=model_id).first()
        if not library_model:
            return None

        # Create placed model instance
        instance_id = f"{model_id}_{uuid.uuid4().hex[:8]}"

        placed_model = ARPlacedModel(
            instance_id=instance_id,
            session_id=session_id,
            model_id=model_id,
            model_name=library_model.name,
            category=library_model.category,
            glb_url=library_model.glb_url,
            width=library_model.width,
            height=library_model.height,
            depth=library_model.depth
        )

        db.session.add(placed_model)
        library_model.increment_usage()
        db.session.commit()

        return placed_model

    def update_model_transform_db(self, instance_id: str, position=None, rotation=None, scale=None) -> bool:
        """Update model transform in database"""
        placed_model = ARPlacedModel.query.filter_by(instance_id=instance_id).first()
        if not placed_model:
            return False

        placed_model.update_transform(position, rotation, scale)
        db.session.commit()

        return True

    def remove_model_db(self, instance_id: str) -> bool:
        """Remove model from session in database"""
        placed_model = ARPlacedModel.query.filter_by(instance_id=instance_id).first()
        if not placed_model:
            return False

        db.session.delete(placed_model)
        db.session.commit()

        return True

    def save_session_db(self, session_id: str) -> bool:
        """Mark session as saved"""
        db_session = ARSession.query.filter_by(session_id=session_id).first()
        if not db_session:
            return False

        db_session.is_saved = True
        db_session.updated_at = datetime.utcnow()
        db.session.commit()

        return True

    def get_user_sessions(self, user_id: int) -> list:
        """Get all AR sessions for a user"""
        return ARSession.query.filter_by(user_id=user_id, is_active=True).order_by(ARSession.updated_at.desc()).all()

    def delete_session_db(self, session_id: str) -> bool:
        """Delete AR session from database"""
        db_session = ARSession.query.filter_by(session_id=session_id).first()
        if not db_session:
            return False

        db.session.delete(db_session)
        db.session.commit()

        return True

    def get_model_library_db(self, category: str = None):
        """Get models from database"""
        query = ARModelLibraryItem.query.filter_by(is_active=True)

        if category:
            query = query.filter_by(category=category)

        models = query.all()
        return [model.to_dict() for model in models]

    def search_models_db(self, query: str):
        """Search models in database"""
        query_lower = query.lower()
        models = ARModelLibraryItem.query.filter(
            db.or_(
                ARModelLibraryItem.name.ilike(f'%{query}%'),
                ARModelLibraryItem.category.ilike(f'%{query}%'),
                ARModelLibraryItem.description.ilike(f'%{query}%')
            )
        ).filter_by(is_active=True).all()

        return [model.to_dict() for model in models]


# Initialize service with database
ar_service_db = ARServiceWithDB()
