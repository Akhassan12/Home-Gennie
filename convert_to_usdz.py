#!/usr/bin/env python3
"""
3D Furniture Model Manager for AR Interior Design
Downloads, converts, and manages 3D models for AR furniture visualization
"""

import os
import subprocess
import requests
from pathlib import Path

class USDZConverter:
    """Convert GLB files to USDZ for iOS AR"""

    def __init__(self):
        self.models_path = Path('static/ar_assets/models')
        self.usdz_path = Path('static/ar_assets/models')

    def convert_with_blender(self, glb_file):
        """Convert using Blender (if available)"""
        try:
            blender_script = f'''
import bpy
import sys

# Get input file from command line
input_file = "{glb_file}"

# Clear scene
bpy.ops.wm.read_homefile(use_empty=True)

# Import GLB
bpy.ops.import_scene.gltf(filepath=input_file)

# Export as USDZ
output_file = "{glb_file.with_suffix('.usdz')}"
bpy.ops.wm.usd_export(filepath=str(output_file))

print("Conversion completed:", output_file)
'''

            # Write temporary script
            script_path = Path('temp_blender_script.py')
            with open(script_path, 'w') as f:
                f.write(blender_script)

            # Run Blender in background
            result = subprocess.run([
                'blender', '--background', '--python', str(script_path)
            ], capture_output=True, text=True)

            # Clean up
            if script_path.exists():
                script_path.unlink()

            if result.returncode == 0:
                print(f"[SUCCESS] Converted {glb_file.name} to USDZ using Blender")
                return True
            else:
                print(f"[ERROR] Blender conversion failed: {result.stderr}")
                return False

        except FileNotFoundError:
            print("[WARNING] Blender not found. Install Blender or use online converter.")
            return False

    def convert_online(self, glb_file):
        """Convert using online service"""
        print(f"\n[INFO] Please convert {glb_file.name} manually:")
        print("1. Go to: https://products.aspose.app/3d/conversion/glb-to-usdz")
        print(f"2. Upload: {glb_file}")
        print(f"3. Download USDZ version")
        print(f"4. Save as: {glb_file.stem}.usdz")
        print(f"5. Place in: {self.usdz_path}")
        return False

    def check_ios_support(self):
        """Check which models have iOS support"""
        glb_files = list(self.models_path.glob('*.glb'))
        usdz_files = list(self.usdz_path.glob('*.usdz'))

        print("\n" + "="*60)
        print("iOS AR SUPPORT CHECK")
        print("="*60)

        usdz_stems = {f.stem for f in usdz_files}

        for glb_file in glb_files:
            has_usdz = glb_file.stem in usdz_stems
            status = "[OK]" if has_usdz else "[MISSING]"
            print(f"{status} {glb_file.name} → USDZ: {'✅' if has_usdz else '❌'}")

        missing_count = len(glb_files) - len(usdz_files)
        if missing_count > 0:
            print(f"\n[WARNING] {missing_count} models need USDZ conversion for iOS")
            print("\nTo convert manually:")
            print("1. Visit: https://products.aspose.app/3d/conversion/glb-to-usdz")
            print("2. Upload GLB files one by one")
            print("3. Download USDZ versions")
            print(f"4. Save in: {self.usdz_path}")
        else:
            print("\n[SUCCESS] All models have iOS support!")

        return missing_count == 0

    def create_ios_ar_links(self):
        """Generate iOS AR Quick Look HTML"""
        glb_files = list(self.models_path.glob('*.glb'))
        usdz_files = list(self.usdz_path.glob('*.usdz'))

        html_content = []
        html_content.append('''<!DOCTYPE html>
<html>
<head>
    <title>iOS AR Quick Look Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .model-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .model-card { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }
        .ar-link { display: block; padding: 15px; background: #007aff; color: white; text-decoration: none; border-radius: 8px; text-align: center; }
        .ar-link:hover { background: #0056cc; }
        img { width: 100%; height: 200px; object-fit: cover; border-radius: 8px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <h1>iOS AR Quick Look Test Page</h1>
    <p>Open this page on an iOS device to test AR Quick Look.</p>

    <div class="model-grid">''')

        usdz_stems = {f.stem for f in usdz_files}

        for glb_file in glb_files:
            model_name = glb_file.stem.replace('_', ' ').title()
            has_usdz = glb_file.stem in usdz_stems

            html_content.append(f'''
        <div class="model-card">
            <img src="https://via.placeholder.com/300x200/667eea/white?text={model_name}" alt="{model_name}">
            <h3>{model_name}</h3>''')

            if has_usdz:
                usdz_file = next(f for f in usdz_files if f.stem == glb_file.stem)
                html_content.append(f'''
            <a class="ar-link" rel="ar" href="/static/ar_assets/models/{usdz_file.name}">
                📱 View in AR (iOS)
            </a>''')
            else:
                html_content.append('''
            <p style="color: #666; font-size: 14px;">USDZ conversion needed for iOS</p>''')

            html_content.append('        </div>')

        html_content.append('''
    </div>
</body>
</html>''')

        # Save HTML file
        html_path = Path('ios_ar_test.html')
        with open(html_path, 'w') as f:
            f.write('\n'.join(html_content))

        print(f"\n[SUCCESS] iOS AR test page created: {html_path}")
        print("Open this file on an iOS device to test AR Quick Look")

def main():
    """Main execution"""
    print("GLB to USDZ Converter for iOS AR")
    print("="*50)

    converter = USDZConverter()

    # Check current status
    converter.check_ios_support()

    # Ask user what to do
    print("\nChoose an option:")
    print("1. Convert with Blender (if installed)")
    print("2. Generate online conversion guide")
    print("3. Create iOS AR test page")
    print("4. Skip USDZ conversion for now")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == '1':
        print("\nAttempting Blender conversion...")
        glb_files = list(converter.models_path.glob('*.glb'))
        for glb_file in glb_files:
            converter.convert_with_blender(glb_file)
        converter.check_ios_support()

    elif choice == '2':
        print("\n" + "="*60)
        print("ONLINE CONVERSION GUIDE")
        print("="*60)
        glb_files = list(converter.models_path.glob('*.glb'))
        for glb_file in glb_files:
            print(f"\n📁 {glb_file.name}:")
            print(f"   Upload to: https://products.aspose.app/3d/conversion/glb-to-usdz")
            print(f"   Download as: {glb_file.stem}.usdz")
            print(f"   Save to: static/ar_assets/models/")

    elif choice == '3':
        converter.create_ios_ar_links()

    elif choice == '4':
        print("\n[SUCCESS] Skipping USDZ conversion")
        print("Note: iOS users will see fallback AR experience")
        print("Android users will get full AR experience")

    print("\n✅ Done!")

if __name__ == '__main__':
    main()
