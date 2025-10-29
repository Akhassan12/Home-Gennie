#!/usr/bin/env python3
"""
Enhanced 3D Model Manager for AR Interior Dashboard
Supports both GLB and USDZ formats for optimal AR performance
"""
import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Tuple
import subprocess

class EnhancedModelManager:
    """Enhanced manager for both GLB and USDZ 3D models"""

    def __init__(self, base_path: str = 'static/ar_assets'):
        self.base_path = Path(base_path)
        self.models_path = self.base_path / 'models'
        self.thumbnails_path = self.base_path / 'thumbnails'
        self.optimized_path = self.base_path / 'optimized_models'

        # Create directories
        for path in [self.models_path, self.thumbnails_path, self.optimized_path]:
            path.mkdir(parents=True, exist_ok=True)

        self.model_catalog = []

    def scan_models(self) -> Dict[str, Dict[str, str]]:
        """Scan and catalog all models (both GLB and USDZ)"""
        print("🔍 Scanning for 3D models...")

        models = {}
        glb_files = list(self.models_path.glob('*.glb'))
        usdz_files = list(self.models_path.glob('*.usdz'))

        # Process GLB files
        for glb_file in glb_files:
            base_name = glb_file.stem.lower()
            models[base_name] = {
                'glb': str(glb_file),
                'usdz': None,
                'name': glb_file.stem.replace('_', ' ').title(),
                'size_glb': os.path.getsize(glb_file),
                'size_usdz': 0
            }

        # Process USDZ files and match with GLB
        for usdz_file in usdz_files:
            base_name = usdz_file.stem.lower()
            size_usdz = os.path.getsize(usdz_file)

            if base_name in models:
                # Match found - update existing entry
                models[base_name]['usdz'] = str(usdz_file)
                models[base_name]['size_usdz'] = size_usdz
            else:
                # USDZ file without matching GLB
                models[base_name] = {
                    'glb': None,
                    'usdz': str(usdz_file),
                    'name': usdz_file.stem.replace('_', ' ').title(),
                    'size_glb': 0,
                    'size_usdz': size_usdz
                }

        return models

    def analyze_model_collection(self) -> Dict:
        """Analyze the entire model collection"""
        print("\n📊 MODEL COLLECTION ANALYSIS")
        print("=" * 50)

        models = self.scan_models()
        total_models = len(models)

        if total_models == 0:
            print("❌ No models found!")
            return {'total_models': 0}

        # Analyze formats
        glb_only = sum(1 for m in models.values() if m['glb'] and not m['usdz'])
        usdz_only = sum(1 for m in models.values() if m['usdz'] and not m['glb'])
        both_formats = sum(1 for m in models.values() if m['glb'] and m['usdz'])
        total_glb = glb_only + both_formats
        total_usdz = usdz_only + both_formats

        # Size analysis
        total_size_glb = sum(m['size_glb'] for m in models.values()) / (1024 * 1024)
        total_size_usdz = sum(m['size_usdz'] for m in models.values()) / (1024 * 1024)

        print(f"📁 Total Models: {total_models}")
        print(f"📦 GLB Files: {total_glb} ({total_size_glb:.2f} MB)")
        print(f"📱 USDZ Files: {total_usdz} ({total_size_usdz:.2f} MB)")
        print(f"✅ Both Formats: {both_formats}")
        print(f"⚠️  GLB Only: {glb_only}")
        print(f"⚠️  USDZ Only: {usdz_only}")

        # Categorization
        categories = {}
        for model in models.values():
            # Simple categorization based on filename
            name_lower = model['name'].lower()
            if any(word in name_lower for word in ['sofa', 'chair', 'seat', 'couch']):
                category = 'seating'
            elif any(word in name_lower for word in ['table', 'desk']):
                category = 'tables'
            elif any(word in name_lower for word in ['lamp', 'light']):
                category = 'lighting'
            elif any(word in name_lower for word in ['drawer', 'cabinet', 'storage']):
                category = 'storage'
            elif any(word in name_lower for word in ['mirror', 'decor']):
                category = 'decor'
            elif any(word in name_lower for word in ['kitchen']):
                category = 'kitchen'
            elif any(word in name_lower for word in ['bed']):
                category = 'beds'
            else:
                category = 'misc'

            if category not in categories:
                categories[category] = []
            categories[category].append(model)

        print("🏷️  CATEGORIES:"        for category, items in categories.items():
            print(f"   {category.title()}: {len(items)} models")

        # Recommendations
        print("💡 RECOMMENDATIONS:"        if both_formats < total_models * 0.7:
            print("   📱 Consider converting more models to USDZ for better iOS AR support")
        if glb_only > 0:
            print(f"   🔄 Convert {glb_only} GLB-only models to USDZ for Apple AR compatibility")
        if usdz_only > 0:
            print(f"   🔄 Convert {usdz_only} USDZ-only models to GLB for cross-platform support")

        return {
            'total_models': total_models,
            'glb_only': glb_only,
            'usdz_only': usdz_only,
            'both_formats': both_formats,
            'categories': categories,
            'models': models
        }

    def generate_enhanced_database_script(self):
        """Generate enhanced database script with both GLB and USDZ support"""
        print("\n📝 Generating enhanced database script...")

        models = self.scan_models()
        script = []

        script.append("# Enhanced Database Population Script")
        script.append("# Supports both GLB and USDZ formats for optimal AR performance")
        script.append("import sys")
        script.append("import os")
        script.append("sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))")
        script.append("from models.ar_models import ARModelLibraryItem, db")
        script.append("import json")
        script.append("")
        script.append("def populate_enhanced_model_library():")
        script.append("    models = [")

        for base_name, model in models.items():
            # Determine category
            name_lower = model['name'].lower()
            if any(word in name_lower for word in ['sofa', 'chair', 'seat', 'couch']):
                category = 'seating'
            elif any(word in name_lower for word in ['table', 'desk']):
                category = 'tables'
            elif any(word in name_lower for word in ['lamp', 'light']):
                category = 'lighting'
            elif any(word in name_lower for word in ['drawer', 'cabinet', 'storage']):
                category = 'storage'
            elif any(word in name_lower for word in ['mirror', 'decor']):
                category = 'decor'
            elif any(word in name_lower for word in ['kitchen']):
                category = 'kitchen'
            elif any(word in name_lower for word in ['bed']):
                category = 'beds'
            else:
                category = 'misc'

            # Determine best format for AR (prefer USDZ for iOS, GLB for others)
            if model['usdz']:
                primary_url = f"/static/ar_assets/models/{Path(model['usdz']).name}"
                secondary_url = f"/static/ar_assets/models/{Path(model['glb']).name}" if model['glb'] else None
                ar_optimized = "USDZ (iOS Optimized)"
            elif model['glb']:
                primary_url = f"/static/ar_assets/models/{Path(model['glb']).name}"
                secondary_url = None
                ar_optimized = "GLB (Cross-platform)"
            else:
                continue

            script.append(f"        {{")

            # Model identification
            script.append(f"            'model_id': '{base_name}',")
            script.append(f"            'name': '{model['name']}',")
            script.append(f"            'category': '{category}',")

            # File URLs
            script.append(f"            'glb_url': '{secondary_url}' if '{secondary_url}' != 'None' else None,")
            script.append(f"            'usdz_url': '{primary_url}' if '{primary_url}' != '/static/ar_assets/models/None' else None,")
            script.append(f"            'thumbnail_url': '/static/ar_assets/thumbnails/{base_name}.jpg',")

            # Dimensions (estimated)
            script.append(f"            'width': 1.0,")
            script.append(f"            'height': 1.0,")
            script.append(f"            'depth': 1.0,")

            # Enhanced metadata
            script.append(f"            'description': '3D model with {ar_optimized} support',")
            script.append(f"            'tags': {json.dumps([category, '3d-model', 'ar-ready']) },")
            script.append(f"            'style': 'modern',")
            script.append(f"            'is_premium': False,")
            script.append(f"            'ar_optimized_format': '{ar_optimized}'")
            script.append(f"        }},")

        script.append("    ]")
        script.append("")
        script.append("    for model_data in models:")
        script.append("        existing = ARModelLibraryItem.query.filter_by(model_id=model_data['model_id']).first()")
        script.append("        if not existing:")
        script.append("            model = ARModelLibraryItem(**model_data)")
        script.append("            db.session.add(model)")
        script.append("            print(f\"Added: {model_data['name']} ({model_data.get('ar_optimized_format', 'Unknown')})\")")
        script.append("")
        script.append("    db.session.commit()")
        script.append("    print(f'\\n✅ Populated {len(models)} enhanced models with multi-format support')")

        # Save script
        script_path = self.base_path.parent / 'populate_enhanced_models.py'
        with open(script_path, 'w') as f:
            f.write('\n'.join(script))

        print(f"✅ Enhanced script saved to: {script_path}")
        print("💡 Run with: python populate_enhanced_models.py")
        return script_path

    def create_format_conversion_guide(self):
        """Create guide for converting between GLB and USDZ"""
        print("\n🔄 FORMAT CONVERSION GUIDE")
        print("=" * 50)

        guide = """
# Converting between GLB and USDZ formats

## Option 1: Blender (Free, Recommended)
1. Open Blender
2. File > Import > glTF 2.0 (.glb/.gltf)
3. Select and import your model
4. File > Export > USD (.usd)
5. In export settings:
   - Check "Export USDZ" option
   - Set texture format to "PNG" or "JPEG"
   - Enable "Compress Textures"
6. Save with .usdz extension

## Option 2: Online Converters
- https://convertio.co/glb-usdz/
- https://www.aconvert.com/format/3d-model/
- https://www.freeconvert.com/glb-to-usdz

## Option 3: Command Line (Advanced)
# Install USD tools
pip install usd-core

# Convert GLB to USDZ
usdcat input.glb --out output.usdz

## Option 4: Python Script
from pxr import Usd, UsdGeom
import sys

# Add conversion logic here
# This requires Pixar USD library

## Best Practices:
✅ Use USDZ for iOS AR (SceneKit/ARKit)
✅ Use GLB for Web AR (WebXR/Three.js)
✅ Keep both formats for maximum compatibility
✅ USDZ files are generally smaller for AR use
✅ Test both formats on target devices

## File Size Optimization:
- Target <5MB for mobile AR
- Use texture compression
- Reduce polygon count if needed
- Remove unnecessary materials
"""
        guide_path = self.base_path.parent / 'format_conversion_guide.md'
        with open(guide_path, 'w') as f:
            f.write(guide)

        print(f"✅ Conversion guide saved to: {guide_path}")

    def generate_ar_compatibility_report(self):
        """Generate AR compatibility report"""
        print("\n📱 AR COMPATIBILITY REPORT")
        print("=" * 50)

        models = self.scan_models()

        # Platform compatibility analysis
        ios_optimized = sum(1 for m in models.values() if m['usdz'])
        web_optimized = sum(1 for m in models.values() if m['glb'])
        cross_platform = sum(1 for m in models.values() if m['glb'] and m['usdz'])

        print(f"🍎 iOS AR Support (USDZ): {ios_optimized} models")
        print(f"🌐 Web AR Support (GLB): {web_optimized} models")
        print(f"🔄 Cross-Platform: {cross_platform} models")

        # Recommendations
        print("📋 PLATFORM RECOMMENDATIONS:"        if ios_optimized == 0:
            print("   ⚠️  No USDZ files found - iOS AR will use GLB fallback")
        if web_optimized == 0:
            print("   ⚠️  No GLB files found - Web AR compatibility limited")
        if cross_platform > 0:
            print(f"   ✅ {cross_platform} models support all platforms")

        # File size comparison
        total_glb_size = sum(m['size_glb'] for m in models.values()) / (1024 * 1024)
        total_usdz_size = sum(m['size_usdz'] for m in models.values()) / (1024 * 1024)

        if total_usdz_size > 0:
            avg_compression = (1 - total_usdz_size / total_glb_size) * 100 if total_glb_size > 0 else 0
            print("💾 FILE SIZE ANALYSIS:"            print(f"   GLB Total: {total_glb_size:.".2f"B")
            print(f"   USDZ Total: {total_usdz_size:.".2f"B")
            print(f"   Average Compression: {avg_compression:.1f}%")

        return {
            'ios_optimized': ios_optimized,
            'web_optimized': web_optimized,
            'cross_platform': cross_platform,
            'total_glb_size': total_glb_size,
            'total_usdz_size': total_usdz_size
        }

    def create_model_showcase_script(self):
        """Create script to showcase models in furniture catalog"""
        print("\n🎨 Creating model showcase script...")

        models = self.scan_models()

        # Generate JavaScript data for furniture catalog
        catalog_data = []
        for base_name, model in models.items():
            # Determine category and create display data
            name_lower = model['name'].lower()
            if any(word in name_lower for word in ['sofa', 'chair', 'seat', 'couch']):
                category = 'seating'
                icon = 'fas fa-chair'
            elif any(word in name_lower for word in ['table', 'desk']):
                category = 'tables'
                icon = 'fas fa-table'
            elif any(word in name_lower for word in ['lamp', 'light']):
                category = 'lighting'
                icon = 'fas fa-lightbulb'
            elif any(word in name_lower for word in ['drawer', 'cabinet', 'storage']):
                category = 'storage'
                icon = 'fas fa-box'
            else:
                category = 'decor'
                icon = 'fas fa-home'

            # Determine best AR format
            if model['usdz']:
                ar_format = 'usdz'
                ar_label = 'iOS Optimized'
            elif model['glb']:
                ar_format = 'glb'
                ar_label = 'Cross-platform'
            else:
                ar_format = None
                ar_label = 'No AR format'

            catalog_data.append({
                'id': base_name,
                'name': model['name'],
                'category': category,
                'icon': icon,
                'ar_format': ar_format,
                'ar_label': ar_label,
                'has_glb': model['glb'] is not None,
                'has_usdz': model['usdz'] is not None
            })

        # Generate JavaScript file for furniture catalog
        js_content = []
        js_content.append("// Auto-generated model catalog data")
        js_content.append("window.MODEL_CATALOG = " + json.dumps(catalog_data, indent=4) + ";")
        js_content.append("")
        js_content.append("// Model format preference for AR")
        js_content.append("function getOptimalARFormat(modelId) {")
        js_content.append("    const model = window.MODEL_CATALOG.find(m => m.id === modelId);")
        js_content.append("    if (!model) return null;")
        js_content.append("    ")
        js_content.append("    // Prefer USDZ for iOS, GLB for others")
        js_content.append("    if (model.has_usdz) return 'usdz';")
        js_content.append("    if (model.has_glb) return 'glb';")
        js_content.append("    return null;")
        js_content.append("}")
        js_content.append("")
        js_content.append("// Get model URL by format")
        js_content.append("function getModelUrl(modelId, format = null) {")
        js_content.append("    const model = window.MODEL_CATALOG.find(m => m.id === modelId);")
        js_content.append("    if (!model) return null;")
        js_content.append("    ")
        js_content.append("    if (format === null) {")
        js_content.append("        format = getOptimalARFormat(modelId);")
        js_content.append("    }")
        js_content.append("    ")
        js_content.append("    if (format === 'usdz' && model.has_usdz) {")
        js_content.append(f"        return '/static/ar_assets/models/{modelId}.usdz';")
        js_content.append("    }")
        js_content.append("    if (format === 'glb' && model.has_glb) {")
        js_content.append(f"        return '/static/ar_assets/models/{modelId}.glb';")
        js_content.append("    }")
        js_content.append("    return null;")
        js_content.append("}")

        # Save JavaScript file
        js_path = self.base_path.parent / 'static' / 'js' / 'model_catalog.js'
        with open(js_path, 'w') as f:
            f.write('\n'.join(js_content))

        print(f"✅ Model catalog JavaScript saved to: {js_path}")
        print("💡 Include this file in your furniture catalog template")

        return js_path

    def run_full_analysis(self):
        """Run complete analysis and generate all outputs"""
        print("🚀 ENHANCED 3D MODEL MANAGER")
        print("=" * 60)

        # Run all analyses
        collection_analysis = self.analyze_model_collection()
        compatibility_report = self.generate_ar_compatibility_report()

        # Generate outputs
        enhanced_script = self.generate_enhanced_database_script()
        conversion_guide = self.create_format_conversion_guide()
        catalog_js = self.create_model_showcase_script()

        print("📋 SUMMARY:"        print(f"   📁 Models Analyzed: {collection_analysis['total_models']}")
        print(f"   🍎 iOS AR Ready: {compatibility_report['ios_optimized']}")
        print(f"   🌐 Web AR Ready: {compatibility_report['web_optimized']}")
        print(f"   🔄 Cross-Platform: {compatibility_report['cross_platform']}")
        print("📁 Generated Files:"        print(f"   • {enhanced_script}")
        print(f"   • {conversion_guide}")
        print(f"   • {catalog_js}")

        print("✅ Enhanced model management complete!"
        return {
            'analysis': collection_analysis,
            'compatibility': compatibility_report,
            'outputs': {
                'enhanced_script': enhanced_script,
                'conversion_guide': conversion_guide,
                'catalog_js': catalog_js
            }
        }


def main():
    """Main execution"""
    manager = EnhancedModelManager()
    manager.run_full_analysis()


if __name__ == '__main__':
    main()
