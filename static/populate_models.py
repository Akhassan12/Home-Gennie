# Database Population Script
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.ar_models import ARModelLibraryItem, db

def populate_model_library():
    models = [
        {
            'model_id': 'antique_table',
            'name': 'Antique Table',
            'category': 'tables',
            'glb_url': '/static/ar_assets/models/antique_table.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/antique_table.jpg',
            'width': 1.0,  # Update with actual dimensions
            'height': 1.0,
            'depth': 1.0,
            'description': 'Auto-generated model entry'
        },
        {
            'model_id': 'antique_wooden_desk_with_props',
            'name': 'Antique Wooden Desk With Props',
            'category': 'tables',
            'glb_url': '/static/ar_assets/models/antique_wooden_desk_with_props.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/antique_wooden_desk_with_props.jpg',
            'width': 1.0,  # Update with actual dimensions
            'height': 1.0,
            'depth': 1.0,
            'description': 'Auto-generated model entry'
        },
        {
            'model_id': 'folding_table',
            'name': 'Folding Table',
            'category': 'tables',
            'glb_url': '/static/ar_assets/models/folding_table.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/folding_table.jpg',
            'width': 1.0,  # Update with actual dimensions
            'height': 1.0,
            'depth': 1.0,
            'description': 'Auto-generated model entry'
        },
        {
            'model_id': 'kitchen',
            'name': 'Kitchen',
            'category': 'furniture',
            'glb_url': '/static/ar_assets/models/kitchen.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/kitchen.jpg',
            'width': 1.0,  # Update with actual dimensions
            'height': 1.0,
            'depth': 1.0,
            'description': 'Auto-generated model entry'
        },
        {
            'model_id': 'mirror',
            'name': 'Mirror',
            'category': 'furniture',
            'glb_url': '/static/ar_assets/models/mirror.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/mirror.jpg',
            'width': 1.0,  # Update with actual dimensions
            'height': 1.0,
            'depth': 1.0,
            'description': 'Auto-generated model entry'
        },
        {
            'model_id': 'modern_desk_lamp',
            'name': 'Modern Desk Lamp',
            'category': 'tables',
            'glb_url': '/static/ar_assets/models/modern_desk_lamp.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/modern_desk_lamp.jpg',
            'width': 1.0,  # Update with actual dimensions
            'height': 1.0,
            'depth': 1.0,
            'description': 'Auto-generated model entry'
        },
        {
            'model_id': 'old_1950s_american_chest_of_drawers',
            'name': 'Old 1950S American Chest Of Drawers',
            'category': 'furniture',
            'glb_url': '/static/ar_assets/models/old_1950s_american_chest_of_drawers.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/old_1950s_american_chest_of_drawers.jpg',
            'width': 1.0,  # Update with actual dimensions
            'height': 1.0,
            'depth': 1.0,
            'description': 'Auto-generated model entry'
        },
        {
            'model_id': 'old_sofa',
            'name': 'Old Sofa',
            'category': 'seating',
            'glb_url': '/static/ar_assets/models/old_sofa.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/old_sofa.jpg',
            'width': 1.0,  # Update with actual dimensions
            'height': 1.0,
            'depth': 1.0,
            'description': 'Auto-generated model entry'
        },
        {
            'model_id': 'sofa_budget_friendly',
            'name': 'Sofa Budget Friendly',
            'category': 'seating',
            'glb_url': '/static/ar_assets/models/sofa_budget_friendly.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/sofa_budget_friendly.jpg',
            'width': 1.0,  # Update with actual dimensions
            'height': 1.0,
            'depth': 1.0,
            'description': 'Auto-generated model entry'
        },
        {
            'model_id': 'sofa_combination',
            'name': 'Sofa Combination',
            'category': 'seating',
            'glb_url': '/static/ar_assets/models/sofa_combination.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/sofa_combination.jpg',
            'width': 1.0,  # Update with actual dimensions
            'height': 1.0,
            'depth': 1.0,
            'description': 'Auto-generated model entry'
        },
        {
            'model_id': 'sofa_morden',
            'name': 'Sofa Morden',
            'category': 'seating',
            'glb_url': '/static/ar_assets/models/sofa_morden.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/sofa_morden.jpg',
            'width': 1.0,  # Update with actual dimensions
            'height': 1.0,
            'depth': 1.0,
            'description': 'Auto-generated model entry'
        },
        {
            'model_id': 'sofa_morden2',
            'name': 'Sofa Morden2',
            'category': 'seating',
            'glb_url': '/static/ar_assets/models/sofa_morden2.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/sofa_morden2.jpg',
            'width': 1.0,  # Update with actual dimensions
            'height': 1.0,
            'depth': 1.0,
            'description': 'Auto-generated model entry'
        },
    ]

    for model_data in models:
        existing = ARModelLibraryItem.query.filter_by(model_id=model_data['model_id']).first()
        if not existing:
            model = ARModelLibraryItem(**model_data)
            db.session.add(model)

    db.session.commit()
    print(f'Populated {len(models)} models')
