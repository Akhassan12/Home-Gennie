"""
Complete AR Service Implementation for Interior Design
Implements WebXR-based AR with 3D model placement and interaction
"""
import os
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from flask import current_app
import numpy as np

class AR3DModel:
    """Represents a 3D model for AR placement"""

    def __init__(self, model_id: str, name: str, category: str,
                 glb_url: str, dimensions: Dict[str, float]):
        self.model_id = model_id
        self.name = name
        self.category = category
        self.glb_url = glb_url
        self.dimensions = dimensions
        self.transform = {
            'position': {'x': 0, 'y': 0, 'z': 0},
            'rotation': {'x': 0, 'y': 0, 'z': 0},
            'scale': {'x': 1, 'y': 1, 'z': 1}
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'model_id': self.model_id,
            'name': self.name,
            'category': self.category,
            'glb_url': self.glb_url,
            'dimensions': self.dimensions,
            'transform': self.transform
        }

    def update_transform(self, position: Dict = None, rotation: Dict = None, scale: Dict = None):
        """Update model transformation"""
        if position:
            self.transform['position'].update(position)
        if rotation:
            self.transform['rotation'].update(rotation)
        if scale:
            self.transform['scale'].update(scale)


class ARScene:
    """Manages an AR scene with multiple models"""

    def __init__(self, scene_id: str, room_type: str):
        self.scene_id = scene_id
        self.room_type = room_type
        self.models: List[AR3DModel] = []
        self.lighting = self._default_lighting()
        self.environment = self._default_environment()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def _default_lighting(self) -> Dict[str, Any]:
        """Default lighting configuration"""
        return {
            'ambient': {
                'color': '#FFFFFF',
                'intensity': 0.6
            },
            'directional': {
                'color': '#FFFFFF',
                'intensity': 0.8,
                'position': {'x': 5, 'y': 10, 'z': 5}
            },
            'hemisphere': {
                'sky_color': '#87CEEB',
                'ground_color': '#8B4513',
                'intensity': 0.5
            }
        }

    def _default_environment(self) -> Dict[str, Any]:
        """Default environment settings"""
        return {
            'background_color': '#E5E5E5',
            'floor_grid': True,
            'floor_color': '#F5F5F5',
            'shadows': True,
            'fog': {
                'enabled': False,
                'color': '#FFFFFF',
                'near': 10,
                'far': 50
            }
        }

    def add_model(self, model: AR3DModel):
        """Add a 3D model to the scene"""
        self.models.append(model)
        self.updated_at = datetime.utcnow()

    def remove_model(self, model_id: str) -> bool:
        """Remove a model from the scene"""
        initial_length = len(self.models)
        self.models = [m for m in self.models if m.model_id != model_id]
        if len(self.models) < initial_length:
            self.updated_at = datetime.utcnow()
            return True
        return False

    def get_model(self, model_id: str) -> Optional[AR3DModel]:
        """Get a specific model by ID"""
        for model in self.models:
            if model.model_id == model_id:
                return model
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert scene to dictionary"""
        return {
            'scene_id': self.scene_id,
            'room_type': self.room_type,
            'models': [m.to_dict() for m in self.models],
            'lighting': self.lighting,
            'environment': self.environment,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ARModelLibrary:
    """Library of available 3D models for AR"""

    def __init__(self):
        self.models = self._initialize_model_library()

    def _initialize_model_library(self) -> Dict[str, AR3DModel]:
        """Initialize the 3D model library"""
        models = {}

        # Furniture models - using actual files from static/ar_assets/models/
        furniture_items = [
            {
                'id': 'sofa_morden',
                'name': 'Modern Sofa',
                'category': 'seating',
                'glb_url': '/static/ar_assets/models/sofa_morden.glb',
                'dimensions': {'width': 2.0, 'height': 0.85, 'depth': 0.95}
            },
            {
                'id': 'sofa_budget_friendly',
                'name': 'Budget Friendly Sofa',
                'category': 'seating',
                'glb_url': '/static/ar_assets/models/sofa_budget_friendly.glb',
                'dimensions': {'width': 1.8, 'height': 0.80, 'depth': 0.90}
            },
            {
                'id': 'sofa_combination',
                'name': 'Sofa Combination',
                'category': 'seating',
                'glb_url': '/static/ar_assets/models/sofa_combination.glb',
                'dimensions': {'width': 2.2, 'height': 0.85, 'depth': 1.0}
            },
            {
                'id': 'old_sofa',
                'name': 'Classic Sofa',
                'category': 'seating',
                'glb_url': '/static/ar_assets/models/old_sofa.glb',
                'dimensions': {'width': 1.9, 'height': 0.82, 'depth': 0.88}
            },
            {
                'id': 'antique_table',
                'name': 'Antique Table',
                'category': 'tables',
                'glb_url': '/static/ar_assets/models/antique_table.glb',
                'dimensions': {'width': 1.5, 'height': 0.75, 'depth': 0.9}
            },
            {
                'id': 'folding_table',
                'name': 'Folding Table',
                'category': 'tables',
                'glb_url': '/static/ar_assets/models/folding_table.glb',
                'dimensions': {'width': 1.2, 'height': 0.75, 'depth': 0.8}
            },
            {
                'id': 'antique_wooden_desk',
                'name': 'Antique Wooden Desk',
                'category': 'tables',
                'glb_url': '/static/ar_assets/models/antique_wooden_desk_with_props.glb',
                'dimensions': {'width': 1.6, 'height': 0.8, 'depth': 0.9}
            },
            {
                'id': 'modern_desk_lamp',
                'name': 'Modern Desk Lamp',
                'category': 'lighting',
                'glb_url': '/static/ar_assets/models/modern_desk_lamp.glb',
                'dimensions': {'width': 0.3, 'height': 0.6, 'depth': 0.3}
            },
            {
                'id': 'chest_of_drawers',
                'name': 'Chest of Drawers',
                'category': 'storage',
                'glb_url': '/static/ar_assets/models/old_1950s_american_chest_of_drawers.glb',
                'dimensions': {'width': 1.2, 'height': 1.0, 'depth': 0.5}
            },
            {
                'id': 'mirror_decorative',
                'name': 'Decorative Mirror',
                'category': 'decor',
                'glb_url': '/static/ar_assets/models/mirror.glb',
                'dimensions': {'width': 0.8, 'height': 1.2, 'depth': 0.1}
            },
            {
                'id': 'kitchen_setup',
                'name': 'Kitchen Setup',
                'category': 'decor',
                'glb_url': '/static/ar_assets/models/kitchen.glb',
                'dimensions': {'width': 3.0, 'height': 2.5, 'depth': 2.0}
            }
        ]

        for item in furniture_items:
            model = AR3DModel(
                model_id=item['id'],
                name=item['name'],
                category=item['category'],
                glb_url=item['glb_url'],
                dimensions=item['dimensions']
            )
            models[item['id']] = model

        return models

    def get_model(self, model_id: str) -> Optional[AR3DModel]:
        """Get a model by ID"""
        return self.models.get(model_id)

    def get_models_by_category(self, category: str) -> List[AR3DModel]:
        """Get all models in a category"""
        return [m for m in self.models.values() if m.category == category]

    def get_all_models(self) -> List[AR3DModel]:
        """Get all available models"""
        return list(self.models.values())

    def search_models(self, query: str) -> List[AR3DModel]:
        """Search models by name or category"""
        query_lower = query.lower()
        return [
            m for m in self.models.values()
            if query_lower in m.name.lower() or query_lower in m.category.lower()
        ]


class ARSessionManager:
    """Manages AR sessions and persistence"""

    def __init__(self):
        self.active_sessions: Dict[str, ARScene] = {}
        self.model_library = ARModelLibrary()

    def create_session(self, room_type: str, design_data: Dict[str, Any] = None) -> ARScene:
        """Create a new AR session"""
        session_id = str(uuid.uuid4())
        scene = ARScene(session_id, room_type)

        # Add furniture from design data if provided
        if design_data:
            self._populate_scene_from_design(scene, design_data)

        self.active_sessions[session_id] = scene
        return scene

    def _populate_scene_from_design(self, scene: ARScene, design_data: Dict[str, Any]):
        """Populate scene with furniture from design concept"""
        key_elements = design_data.get('key_elements', [])

        # Map design elements to 3D models (using actual model IDs)
        element_to_model = {
            'sofa': 'sofa_morden',
            'chair': 'sofa_budget_friendly',
            'coffee table': 'antique_table',
            'bookshelf': 'chest_of_drawers',
            'lamp': 'modern_desk_lamp',
            'table': 'folding_table',
            'desk': 'antique_wooden_desk',
            'mirror': 'mirror_decorative',
            'kitchen': 'kitchen_setup'
        }

        # Add models based on design elements
        added_models = set()
        for element in key_elements[:5]:  # Limit to 5 items
            element_lower = element.lower()
            for keyword, model_id in element_to_model.items():
                if keyword in element_lower and model_id not in added_models:
                    model = self.model_library.get_model(model_id)
                    if model:
                        # Create a new instance
                        new_model = AR3DModel(
                            model_id=f"{model_id}_{uuid.uuid4().hex[:8]}",
                            name=model.name,
                            category=model.category,
                            glb_url=model.glb_url,
                            dimensions=model.dimensions.copy()
                        )
                        scene.add_model(new_model)
                        added_models.add(model_id)
                    break

    def get_session(self, session_id: str) -> Optional[ARScene]:
        """Get an existing AR session"""
        return self.active_sessions.get(session_id)

    def update_model_transform(self, session_id: str, model_id: str,
                              position: Dict = None, rotation: Dict = None,
                              scale: Dict = None) -> bool:
        """Update a model's transform in a session"""
        scene = self.get_session(session_id)
        if not scene:
            return False

        model = scene.get_model(model_id)
        if not model:
            return False

        model.update_transform(position, rotation, scale)
        scene.updated_at = datetime.utcnow()
        return True

    def add_model_to_session(self, session_id: str, model_id: str) -> Optional[str]:
        """Add a model from library to a session"""
        scene = self.get_session(session_id)
        if not scene:
            return None

        library_model = self.model_library.get_model(model_id)
        if not library_model:
            return None

        # Create new instance with unique ID
        instance_id = f"{model_id}_{uuid.uuid4().hex[:8]}"
        new_model = AR3DModel(
            model_id=instance_id,
            name=library_model.name,
            category=library_model.category,
            glb_url=library_model.glb_url,
            dimensions=library_model.dimensions.copy()
        )

        scene.add_model(new_model)
        return instance_id

    def remove_model_from_session(self, session_id: str, model_id: str) -> bool:
        """Remove a model from a session"""
        scene = self.get_session(session_id)
        if not scene:
            return False

        return scene.remove_model(model_id)

    def save_session(self, session_id: str) -> Dict[str, Any]:
        """Save session data (would save to database in production)"""
        scene = self.get_session(session_id)
        if not scene:
            return {'success': False, 'error': 'Session not found'}

        # In production, save to database
        # For now, return the scene data
        return {
            'success': True,
            'session_id': session_id,
            'data': scene.to_dict()
        }

    def load_session(self, session_data: Dict[str, Any]) -> str:
        """Load a saved session"""
        session_id = session_data.get('scene_id', str(uuid.uuid4()))

        # Reconstruct scene from saved data
        scene = ARScene(session_id, session_data.get('room_type', 'Living Room'))

        # Restore models
        for model_data in session_data.get('models', []):
            model = AR3DModel(
                model_id=model_data['model_id'],
                name=model_data['name'],
                category=model_data['category'],
                glb_url=model_data['glb_url'],
                dimensions=model_data['dimensions']
            )
            model.transform = model_data.get('transform', model.transform)
            scene.add_model(model)

        # Restore lighting and environment
        scene.lighting = session_data.get('lighting', scene.lighting)
        scene.environment = session_data.get('environment', scene.environment)

        self.active_sessions[session_id] = scene
        return session_id

    def delete_session(self, session_id: str) -> bool:
        """Delete an AR session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False

    def get_webxr_config(self) -> Dict[str, Any]:
        """Get WebXR configuration for client"""
        return {
            'required_features': ['hit-test', 'dom-overlay'],
            'optional_features': [
                'light-estimation',
                'camera-access',
                'plane-detection',
                'anchors',
                'hand-tracking'
            ],
            'dom_overlay': {'root': '#ar-overlay'},
            'session_mode': 'immersive-ar',
            'reference_space_type': 'local-floor',
            'frame_rate': 'high'
        }


class ARService:
    """Main AR service interface"""

    def __init__(self):
        self.session_manager = ARSessionManager()

    def initialize_ar_session(self, design_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a new AR session with design data"""
        try:
            room_type = design_data.get('analysis', {}).get('room_type', 'Living Room')
            design_concept = design_data.get('designs', [{}])[0]

            # Create AR scene
            scene = self.session_manager.create_session(room_type, design_concept)

            return {
                'success': True,
                'session_id': scene.scene_id,
                'scene_data': scene.to_dict(),
                'webxr_config': self.session_manager.get_webxr_config(),
                'model_library': [m.to_dict() for m in self.session_manager.model_library.get_all_models()]
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get AR session data"""
        scene = self.session_manager.get_session(session_id)
        if not scene:
            return {'success': False, 'error': 'Session not found'}

        return {
            'success': True,
            'scene_data': scene.to_dict()
        }

    def update_model(self, session_id: str, model_id: str,
                    position: Dict = None, rotation: Dict = None,
                    scale: Dict = None) -> Dict[str, Any]:
        """Update a 3D model's transform"""
        success = self.session_manager.update_model_transform(
            session_id, model_id, position, rotation, scale
        )

        if success:
            return {'success': True, 'message': 'Model updated'}
        return {'success': False, 'error': 'Failed to update model'}

    def add_model(self, session_id: str, model_id: str) -> Dict[str, Any]:
        """Add a model to the AR scene"""
        instance_id = self.session_manager.add_model_to_session(session_id, model_id)

        if instance_id:
            return {
                'success': True,
                'instance_id': instance_id,
                'message': 'Model added to scene'
            }
        return {'success': False, 'error': 'Failed to add model'}

    def remove_model(self, session_id: str, model_id: str) -> Dict[str, Any]:
        """Remove a model from the AR scene"""
        success = self.session_manager.remove_model_from_session(session_id, model_id)

        if success:
            return {'success': True, 'message': 'Model removed'}
        return {'success': False, 'error': 'Failed to remove model'}

    def get_model_library(self, category: str = None) -> Dict[str, Any]:
        """Get available 3D models"""
        if category:
            models = self.session_manager.model_library.get_models_by_category(category)
        else:
            models = self.session_manager.model_library.get_all_models()

        return {
            'success': True,
            'models': [m.to_dict() for m in models],
            'categories': ['seating', 'tables', 'storage', 'lighting', 'beds', 'decor']
        }

    def search_models(self, query: str) -> Dict[str, Any]:
        """Search for models"""
        models = self.session_manager.model_library.search_models(query)

        return {
            'success': True,
            'models': [m.to_dict() for m in models],
            'count': len(models)
        }

    def save_session(self, session_id: str) -> Dict[str, Any]:
        """Save AR session"""
        return self.session_manager.save_session(session_id)

    def load_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load saved AR session"""
        try:
            session_id = self.session_manager.load_session(session_data)
            return {
                'success': True,
                'session_id': session_id,
                'message': 'Session loaded successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Create singleton instance
ar_service = ARService()
