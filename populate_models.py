#!/usr/bin/env python3
"""
Populate AR Model Library in PostgreSQL
"""
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

def populate_model_library():
    """Add 3D models to the PostgreSQL database"""
    
    print("="*60)
    print("POPULATING AR MODEL LIBRARY")
    print("="*60)
    
    # Get password from args or env
    pg_password = os.environ.get('PG_PASSWORD', '')
    if not pg_password and len(sys.argv) > 1:
        pg_password = sys.argv[1]
    if not pg_password:
        pg_password = "postgres"
    
    # Connection string
    postgres_uri = f"postgresql://postgres:{pg_password}@localhost:5432/ar_interior_db"
    
    # Create engine
    postgres_engine = create_engine(postgres_uri)
    postgres_conn = postgres_engine.connect()
    
    # Models to add
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
            'tags': '["modern", "sofa", "seating", "living room"]',
            'style': 'modern'
        },
        {
            'model_id': 'antique_table_01',
            'name': 'Antique Table',
            'category': 'tables',
            'glb_url': '/static/ar_assets/models/antique_table.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/antique_table.jpg',
            'width': 1.5,
            'height': 0.75,
            'depth': 1.0,
            'description': 'Vintage wooden dining table',
            'tags': '["antique", "table", "dining", "wooden"]',
            'style': 'antique'
        },
        {
            'model_id': 'folding_table_01',
            'name': 'Folding Table',
            'category': 'tables',
            'glb_url': '/static/ar_assets/models/folding_table.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/folding_table.jpg',
            'width': 1.2,
            'height': 0.75,
            'depth': 0.6,
            'description': 'Space-saving folding table',
            'tags': '["folding", "table", "space-saving", "portable"]',
            'style': 'modern'
        },
        {
            'model_id': 'mirror_01',
            'name': 'Wall Mirror',
            'category': 'decor',
            'glb_url': '/static/ar_assets/models/mirror.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/mirror.jpg',
            'width': 0.8,
            'height': 1.2,
            'depth': 0.05,
            'description': 'Elegant wall mirror',
            'tags': '["mirror", "wall", "decor", "bathroom"]',
            'style': 'modern'
        },
        {
            'model_id': 'modern_desk_lamp_01',
            'name': 'Modern Desk Lamp',
            'category': 'lighting',
            'glb_url': '/static/ar_assets/models/modern_desk_lamp.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/modern_desk_lamp.jpg',
            'width': 0.3,
            'height': 0.5,
            'depth': 0.3,
            'description': 'Contemporary desk lamp with adjustable arm',
            'tags': '["lamp", "desk lamp", "lighting", "modern"]',
            'style': 'modern'
        },
        {
            'model_id': 'old_sofa_01',
            'name': 'Classic Sofa',
            'category': 'seating',
            'glb_url': '/static/ar_assets/models/old_sofa.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/old_sofa.jpg',
            'width': 2.2,
            'height': 0.9,
            'depth': 1.0,
            'description': 'Timeless classic sofa design',
            'tags': '["sofa", "classic", "seating", "living room"]',
            'style': 'classic'
        },
        {
            'model_id': 'sofa_combination_01',
            'name': 'Sectional Sofa',
            'category': 'seating',
            'glb_url': '/static/ar_assets/models/sofa_combination.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/sofa_combination.jpg',
            'width': 3.0,
            'height': 0.85,
            'depth': 1.5,
            'description': 'L-shaped sectional sofa',
            'tags': '["sofa", "sectional", "L-shape", "seating"]',
            'style': 'modern'
        },
        {
            'model_id': 'kitchen_01',
            'name': 'Kitchen Set',
            'category': 'kitchen',
            'glb_url': '/static/ar_assets/models/kitchen.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/kitchen.jpg',
            'width': 3.0,
            'height': 2.4,
            'depth': 0.6,
            'description': 'Complete kitchen cabinet set',
            'tags': '["kitchen", "cabinets", "storage", "cooking"]',
            'style': 'modern'
        },
        {
            'model_id': 'chest_of_drawers_01',
            'name': 'Chest of Drawers',
            'category': 'storage',
            'glb_url': '/static/ar_assets/models/old_1950s_american_chest_of_drawers.glb',
            'thumbnail_url': '/static/ar_assets/thumbnails/chest_of_drawers.jpg',
            'width': 0.9,
            'height': 1.2,
            'depth': 0.5,
            'description': 'Vintage 1950s American chest of drawers',
            'tags': '["drawers", "storage", "bedroom", "vintage"]',
            'style': 'vintage'
        }
    ]
    
    try:
        added = 0
        skipped = 0
        
        for model in models:
            # Check if model exists
            result = postgres_conn.execute(
                text('SELECT id FROM ar_model_library WHERE model_id = :model_id'),
                {'model_id': model['model_id']}
            )
            
            if result.fetchone():
                print(f"   Skipped: {model['name']} (already exists)")
                skipped += 1
                continue
            
            # Insert model
            postgres_conn.execute(
                text('''
                    INSERT INTO ar_model_library 
                    (model_id, name, category, glb_url, thumbnail_url, width, height, depth, 
                     description, tags, style, usage_count, rating, is_active, is_premium, created_at)
                    VALUES 
                    (:model_id, :name, :category, :glb_url, :thumbnail_url, :width, :height, :depth,
                     :description, :tags, :style, 0, 0.0, TRUE, FALSE, CURRENT_TIMESTAMP)
                '''),
                model
            )
            
            print(f"   Added: {model['name']}")
            added += 1
        
        postgres_conn.commit()
        
        print("\n" + "="*60)
        print(f"COMPLETE! Added: {added}, Skipped: {skipped}")
        print("="*60)
        
        # Show all models
        result = postgres_conn.execute(text('SELECT model_id, name, category FROM ar_model_library ORDER BY category'))
        print("\nAll models in library:")
        for row in result:
            print(f"   - {row.name} ({row.category})")
        
        return True
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        postgres_conn.close()

if __name__ == '__main__':
    success = populate_model_library()
    sys.exit(0 if success else 1)
