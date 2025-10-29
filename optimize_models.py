#!/usr/bin/env python3
"""
3D Model Optimization Script for AR Interior Dashboard
Reduces model file sizes for better AR performance
"""
import os
import subprocess
from pathlib import Path
import trimesh
import json

class ModelOptimizer:
    """Optimize 3D models for AR performance"""

    def __init__(self, models_path='static/ar_assets/models'):
        self.models_path = Path(models_path)
        self.optimized_path = self.models_path.parent / 'optimized_models'
        self.optimized_path.mkdir(exist_ok=True)

    def get_model_info(self, file_path):
        """Get detailed information about a 3D model"""
        try:
            mesh = trimesh.load(file_path)
            return {
                'file_size': os.path.getsize(file_path),
                'vertices': len(mesh.vertices) if hasattr(mesh, 'vertices') else 0,
                'faces': len(mesh.faces) if hasattr(mesh, 'faces') else 0,
                'is_valid': True
            }
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return {
                'file_size': os.path.getsize(file_path),
                'is_valid': False,
                'error': str(e)
            }

    def optimize_with_trimesh(self, input_path, output_path, target_reduction=0.5):
        """Optimize model using trimesh"""
        try:
            print(f"Optimizing {input_path.name}...")

            # Load mesh
            mesh = trimesh.load(input_path)

            if hasattr(mesh, 'vertices') and len(mesh.vertices) > 1000:
                # Simplify mesh
                target_faces = int(len(mesh.faces) * target_reduction) if hasattr(mesh, 'faces') else 1000
                simplified = mesh.simplify_quadratic_decimation(target_faces)

                # Export optimized model
                simplified.export(output_path)
                print(f"✅ Optimized: {input_path.name} -> {output_path.name}")
                return True
            else:
                # Just copy if already small
                import shutil
                shutil.copy2(input_path, output_path)
                print(f"✅ Copied (already small): {input_path.name}")
                return True

        except Exception as e:
            print(f"❌ Failed to optimize {input_path.name}: {e}")
            return False

    def optimize_with_gltf_transform(self, input_path, output_path):
        """Optimize using gltf-transform CLI if available"""
        try:
            # Check if gltf-transform is installed
            result = subprocess.run(['npx', '@gltf-transform/cli', '--help'],
                                capture_output=True, text=True)

            if result.returncode == 0:
                # Use gltf-transform for optimization
                cmd = [
                    'npx', '@gltf-transform/cli', 'optimize',
                    str(input_path),
                    str(output_path),
                    '--compress', 'draco',
                    '--texture-compress', 'webp'
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    print(f"✅ CLI Optimized: {input_path.name}")
                    return True
                else:
                    print(f"⚠️ CLI optimization failed, using fallback: {result.stderr}")
                    return self.optimize_with_trimesh(input_path, output_path)
            else:
                print("⚠️ gltf-transform not available, using trimesh fallback")
                return self.optimize_with_trimesh(input_path, output_path)

        except Exception as e:
            print(f"❌ CLI optimization error: {e}")
            return self.optimize_with_trimesh(input_path, output_path)

    def process_large_models(self, target_size_mb=5.0):
        """Process all models that are too large"""
        print(f"🔍 Scanning for models > {target_size_mb}MB...")

        large_models = []
        glb_files = list(self.models_path.glob('*.glb'))

        for glb_file in glb_files:
            size_mb = os.path.getsize(glb_file) / (1024 * 1024)
            if size_mb > target_size_mb:
                large_models.append((glb_file, size_mb))

        if not large_models:
            print(f"✅ All models are under {target_size_mb}MB!")
            return

        print(f"Found {len(large_models)} large models:")
        for file_path, size_mb in large_models:
            print(f"  📦 {file_path.name} ({size_mb:.2f} MB)")

        print("\n🚀 Starting optimization...")
        print("   Target: Reduce file size while maintaining quality")
        for file_path, original_size in large_models:
            # Create output path
            output_path = self.optimized_path / f"optimized_{file_path.name}"

            # Try CLI optimization first, fallback to trimesh
            success = self.optimize_with_gltf_transform(file_path, output_path)

            if success and output_path.exists():
                new_size = os.path.getsize(output_path) / (1024 * 1024)
                reduction = (1 - new_size / original_size) * 100
                print(f"   📊 Size reduction: {reduction:.1f}% from {original_size:.2f}MB to {new_size:.2f}MB")

                # If still too large, try more aggressive optimization
                if new_size > target_size_mb:
                    print(f" 🔄 Applying aggressive optimization...")
                    aggressive_output = self.optimized_path / f"aggressive_{file_path.name}"
                    self.optimize_with_trimesh(file_path, aggressive_output, target_reduction=0.3)

                    if aggressive_output.exists():
                        final_size = os.path.getsize(aggressive_output) / (1024 * 1024)
                        if final_size < new_size:
                            output_path = aggressive_output
                            new_size = final_size
                            print(f"   ✅ Better result: {final_size:.2f}MB")

        print("\n📋 Optimization Summary:")
        print(f"   Original location: {self.models_path}")
        print(f"   Optimized location: {self.optimized_path}")
        print("   💡 Replace original models with optimized versions for better AR performance")
    def generate_optimization_report(self):
        """Generate a report of optimization results"""
        print("\n📊 OPTIMIZATION REPORT")
        print("=" * 50)

        # Original models
        original_models = list(self.models_path.glob('*.glb'))
        original_total = sum(os.path.getsize(f) for f in original_models) / (1024 * 1024)

        # Optimized models
        optimized_models = list(self.optimized_path.glob('*.glb'))
        optimized_total = sum(os.path.getsize(f) for f in optimized_models) / (1024 * 1024)

        print(f"Original models: {len(original_models)} files ({original_total:.2f} MB)")
        print(f"Optimized models: {len(optimized_models)} files ({optimized_total:.2f} MB)")

        if optimized_models:
            reduction = (1 - optimized_total / original_total) * 100
            print(f"Total size reduction: {reduction:.1f}%")

            print("\n📁 Optimized models location:")
            for model in optimized_models:
                size_mb = os.path.getsize(model) / (1024 * 1024)
                print(f"   • {model.name} ({size_mb:.2f} MB)")

        print("\n💡 NEXT STEPS:")
        print("   1. Review optimized models in glTF viewer")
        print("   2. Test optimized models in AR environment")
        print("   3. Replace original models if quality is acceptable")
        print("   4. Generate thumbnails for all models")
def main():
    """Main execution"""
    print("🚀 3D Model Optimizer for AR Interior Dashboard")
    print("=" * 60)

    optimizer = ModelOptimizer()

    # Process large models
    optimizer.process_large_models(target_size_mb=5.0)

    # Generate report
    optimizer.generate_optimization_report()

    print("\n✅ Model optimization complete!")
if __name__ == '__main__':
    main()
