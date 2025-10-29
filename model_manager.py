"""
3D Furniture Model Manager for AR Interior Design
Comprehensive system for downloading, converting, and managing 3D models
"""
import os
import requests
import json
from pathlib import Path
from typing import List, Dict
import subprocess

class FurnitureModelManager:
    """Manage 3D furniture models for AR project"""

    def __init__(self, base_path: str = 'static/ar_assets'):
        self.base_path = Path(base_path)
        self.models_path = self.base_path / 'models'
        self.thumbnails_path = self.base_path / 'thumbnails'

        # Create directories
        self.models_path.mkdir(parents=True, exist_ok=True)
        self.thumbnails_path.mkdir(parents=True, exist_ok=True)

        self.model_catalog = []

    def download_from_url(self, url: str, filename: str, model_type: str = 'furniture'):
        """Download a model from direct URL"""
        try:
            print(f"[DOWNLOAD] Downloading {filename}...")

            response = requests.get(url, stream=True)
            response.raise_for_status()

            file_path = self.models_path / filename

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Get file size
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB

            print(f"[SUCCESS] Downloaded {filename} ({file_size:.2f} MB)")

            # Add to catalog
            self.model_catalog.append({
                'filename': filename,
                'type': model_type,
                'size_mb': round(file_size, 2),
                'path': str(file_path)
            })

            return True

        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")
            return False

    def download_sketchfab_models(self):
        """
        Guide for downloading from Sketchfab
        (Manual process since Sketchfab requires authentication)
        """
        print("\n" + "="*60)
        print("SKETCHFAB DOWNLOAD GUIDE")
        print("="*60)

        models = [
            {
                'name': 'Modern Sofa',
                'search': 'modern sofa low poly',
                'filename': 'modern_sofa.glb',
                'category': 'seating'
            },
            {
                'name': 'Accent Chair',
                'search': 'accent chair minimalist',
                'filename': 'accent_chair.glb',
                'category': 'seating'
            },
            {
                'name': 'Coffee Table',
                'search': 'coffee table simple',
                'filename': 'coffee_table.glb',
                'category': 'tables'
            },
            {
                'name': 'Floor Lamp',
                'search': 'floor lamp modern',
                'filename': 'floor_lamp.glb',
                'category': 'lighting'
            },
            {
                'name': 'Bookshelf',
                'search': 'bookshelf minimalist',
                'filename': 'bookshelf.glb',
                'category': 'storage'
            }
        ]

        print("\nSTEP-BY-STEP:")
        print("1. Go to https://sketchfab.com/")
        print("2. For each model below:")
        print("   - Search using the provided term")
        print("   - Filter: 'Downloadable' + 'CC License'")
        print("   - Click Download → Select 'glTF' format")
        print(f"   - Save to: {self.models_path}/")
        print("   - Rename to the suggested filename\n")

        for i, model in enumerate(models, 1):
            print(f"{i}. {model['name']}")
            print(f"   Search: '{model['search']}'")
            print(f"   Save as: {model['filename']}")
            print(f"   Category: {model['category']}\n")

        print("="*60)
        print("TIP: Look for models under 10,000 triangles for best AR performance")
        print("="*60 + "\n")

    def create_placeholder_models(self):
        """Create simple placeholder GLB models using Python"""
        print("\nCreating placeholder models...")

        try:
            import trimesh
            import numpy as np

            placeholders = [
                {
                    'name': 'sofa_placeholder.glb',
                    'size': [2.0, 0.85, 0.95],
                    'color': [139, 115, 85, 255]  # Brown
                },
                {
                    'name': 'chair_placeholder.glb',
                    'size': [0.75, 0.90, 0.85],
                    'color': [100, 100, 100, 255]  # Gray
                },
                {
                    'name': 'table_placeholder.glb',
                    'size': [1.2, 0.45, 0.7],
                    'color': [139, 69, 19, 255]  # Dark brown
                }
            ]

            for placeholder in placeholders:
                # Create box mesh
                mesh = trimesh.creation.box(extents=placeholder['size'])

                # Set color
                mesh.visual.vertex_colors = placeholder['color']

                # Export as GLB
                file_path = self.models_path / placeholder['name']
                mesh.export(file_path)

                print(f"[SUCCESS] Created {placeholder['name']}")

            print("[SUCCESS] Placeholder models created successfully!")
            return True

        except ImportError:
            print("[ERROR] trimesh not installed. Install with: pip install trimesh")
            print("TIP: Or download real models from Sketchfab instead")
            return False

    def validate_models(self):
        """Validate all GLB files in models directory"""
        print("\nValidating models...")

        glb_files = list(self.models_path.glob('*.glb'))

        if not glb_files:
            print("[WARNING] No GLB files found!")
            print(f"[INFO] Expected location: {self.models_path}")
            return False

        print(f"Found {len(glb_files)} GLB files:\n")

        valid_count = 0
        for glb_file in glb_files:
            size_mb = os.path.getsize(glb_file) / (1024 * 1024)

            status = "[OK]" if size_mb < 10 else "[WARNING]"
            print(f"{status} {glb_file.name} ({size_mb:.2f} MB)")

            if size_mb < 10:
                valid_count += 1
            else:
                print(f"   [WARNING] Model is large, may affect AR performance")

        print(f"\n[SUCCESS] {valid_count}/{len(glb_files)} models are optimized for AR")
        return True

    def generate_thumbnails(self):
        """Generate thumbnail images for models"""
        print("\nGenerating thumbnails...")
        print("TIP: For now, manually create thumbnails:")
        print(f"   1. Visit https://gltf-viewer.donmccurdy.com/")
        print(f"   2. Upload each model from: {self.models_path}")
        print(f"   3. Take screenshot")
        print(f"   4. Save as [model_name].jpg in: {self.thumbnails_path}")

    def create_model_database_script(self):
        """Generate SQL or Python script to populate database"""
        print("\nGenerating database population script...")

        glb_files = list(self.models_path.glob('*.glb'))

        if not glb_files:
            print("[WARNING] No models found to generate script")
            return

        script = []
        script.append("# Database Population Script")
        script.append("from services.ar_database_models import ARModelLibraryItem, db\n")
        script.append("def populate_model_library():")
        script.append("    models = [")

        for glb_file in glb_files:
            model_id = glb_file.stem
            name = model_id.replace('_', ' ').title()

            # Determine category from filename
            category = 'furniture'
            if any(x in model_id.lower() for x in ['chair', 'sofa', 'couch']):
                category = 'seating'
            elif any(x in model_id.lower() for x in ['table', 'desk']):
                category = 'tables'
            elif any(x in model_id.lower() for x in ['lamp', 'light']):
                category = 'lighting'
            elif any(x in model_id.lower() for x in ['shelf', 'cabinet', 'storage']):
                category = 'storage'
            elif any(x in model_id.lower() for x in ['bed', 'mattress']):
                category = 'beds'

            script.append(f"        {{")
            script.append(f"            'model_id': '{model_id}',")
            script.append(f"            'name': '{name}',")
            script.append(f"            'category': '{category}',")
            script.append(f"            'glb_url': '/static/ar_assets/models/{glb_file.name}',")
            script.append(f"            'thumbnail_url': '/static/ar_assets/thumbnails/{model_id}.jpg',")
            script.append(f"            'width': 1.0,  # Update with actual dimensions")
            script.append(f"            'height': 1.0,")
            script.append(f"            'depth': 1.0,")
            script.append(f"            'description': 'Auto-generated model entry'")
            script.append(f"        }},")

        script.append("    ]")
        script.append("")
        script.append("    for model_data in models:")
        script.append("        existing = ARModelLibraryItem.query.filter_by(model_id=model_data['model_id']).first()")
        script.append("        if not existing:")
        script.append("            model = ARModelLibraryItem(**model_data)")
        script.append("            db.session.add(model)")
        script.append("")
        script.append("    db.session.commit()")
        script.append("    print(f'Populated {len(models)} models')")

        # Save script
        script_path = self.base_path.parent / 'populate_models.py'
        with open(script_path, 'w') as f:
            f.write('\n'.join(script))

        print(f"[SUCCESS] Script saved to: {script_path}")
        print(f"TIP: Run with: python populate_models.py")

    def optimize_models(self, target_size_mb: float = 5.0):
        """Optimize large models"""
        print(f"\nOptimizing models (target: <{target_size_mb}MB)...")

        glb_files = list(self.models_path.glob('*.glb'))
        large_models = []

        for glb_file in glb_files:
            size_mb = os.path.getsize(glb_file) / (1024 * 1024)
            if size_mb > target_size_mb:
                large_models.append((glb_file, size_mb))

        if not large_models:
            print("[SUCCESS] All models are already optimized!")
            return

        print(f"Found {len(large_models)} models that need optimization:\n")

        for glb_file, size_mb in large_models:
            print(f"[WARNING] {glb_file.name} ({size_mb:.2f} MB)")

        print("\nOPTIMIZATION OPTIONS:")
        print("1. Use Blender Decimation:")
        print("   - Open model in Blender")
        print("   - Add Modifier > Decimate")
        print("   - Set Ratio to 0.5")
        print("   - Apply and re-export")
        print("\n2. Use gltf-transform CLI:")
        print("   npm install -g @gltf-transform/cli")
        print("   gltf-transform optimize input.glb output.glb")
        print("\n3. Use online tool:")
        print("   https://gltf.report/")

    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "="*60)
        print("MODEL LIBRARY REPORT")
        print("="*60)

        glb_files = list(self.models_path.glob('*.glb'))
        thumbnails = list(self.thumbnails_path.glob('*.jpg')) + list(self.thumbnails_path.glob('*.png'))

        print(f"\nDirectory: {self.base_path}")
        print(f"GLB Models: {len(glb_files)}")
        print(f"Thumbnails: {len(thumbnails)}")

        if glb_files:
            total_size = sum(os.path.getsize(f) for f in glb_files) / (1024 * 1024)
            print(f"Total Size: {total_size:.2f} MB")

            print("\nModels:")
            for glb_file in glb_files:
                size_mb = os.path.getsize(glb_file) / (1024 * 1024)
                has_thumbnail = any(t.stem == glb_file.stem for t in thumbnails)
                thumb_status = "[OK]" if has_thumbnail else "[MISSING]"

                print(f"  • {glb_file.name} ({size_mb:.2f} MB) Thumbnail: {thumb_status}")

        print("\n" + "="*60)

        # Recommendations
        print("\nRECOMMENDATIONS:")
        if len(glb_files) < 5:
            print("  [WARNING] Add more models (target: 10-20 for MVP)")
        if len(thumbnails) < len(glb_files):
            print("  [WARNING] Generate thumbnails for all models")
        if any(os.path.getsize(f) / (1024 * 1024) > 5 for f in glb_files):
            print("  [WARNING] Optimize large models (<5MB recommended)")
        if len(glb_files) >= 10:
            print("  [SUCCESS] Good model variety!")

        print("\n" + "="*60 + "\n")


def main():
    """Main execution"""
    print("3D Furniture Model Manager for AR Interior Design")
    print("="*60 + "\n")

    manager = FurnitureModelManager()

    # Menu
    print("Choose an option:")
    print("1. Download guide (Sketchfab)")
    print("2. Create placeholder models")
    print("3. Validate existing models")
    print("4. Generate thumbnails guide")
    print("5. Create database population script")
    print("6. Optimize large models")
    print("7. Generate full report")
    print("8. Do everything (recommended)")

    choice = input("\nEnter choice (1-8): ").strip()

    if choice == '1':
        manager.download_sketchfab_models()
    elif choice == '2':
        manager.create_placeholder_models()
    elif choice == '3':
        manager.validate_models()
    elif choice == '4':
        manager.generate_thumbnails()
    elif choice == '5':
        manager.create_model_database_script()
    elif choice == '6':
        manager.optimize_models()
    elif choice == '7':
        manager.generate_report()
    elif choice == '8':
        print("\nRunning full setup...\n")
        manager.download_sketchfab_models()
        input("\nPress Enter after downloading models from Sketchfab...")
        manager.validate_models()
        manager.generate_thumbnails()
        manager.create_model_database_script()
        manager.optimize_models()
        manager.generate_report()
    else:
        print("Invalid choice")

    print("\n✅ Done!")


if __name__ == '__main__':
    main()
