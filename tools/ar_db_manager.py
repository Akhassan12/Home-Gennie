#!/usr/bin/env python3
"""
AR Database Manager
Interactive tool for managing AR sessions and model library
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import app, db
except ImportError:
    print("❌ Could not import app. Make sure you're running from the project root.")
    sys.exit(1)
from models.ar_models import ARSession, ARPlacedModel, ARModelLibraryItem
import json
from datetime import datetime

class ARDatabaseManager:
    """Interactive AR Database Manager"""

    def __init__(self):
        self.app = app

    def run(self):
        """Run the interactive database manager"""
        print("🗄️ AR Database Manager")
        print("=" * 50)

        while True:
            print("\n📋 Available Operations:")
            print("1. View AR Sessions")
            print("2. View Model Library")
            print("3. View Placed Models")
            print("4. Add Model to Library")
            print("5. Update Model")
            print("6. Delete Model")
            print("7. Create Test Session")
            print("8. Delete Session")
            print("9. Reset Database")
            print("10. Database Statistics")
            print("0. Exit")

            choice = input("\nSelect operation (0-10): ").strip()

            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                self.view_sessions()
            elif choice == '2':
                self.view_model_library()
            elif choice == '3':
                self.view_placed_models()
            elif choice == '4':
                self.add_model()
            elif choice == '5':
                self.update_model()
            elif choice == '6':
                self.delete_model()
            elif choice == '7':
                self.create_test_session()
            elif choice == '8':
                self.delete_session()
            elif choice == '9':
                self.reset_database()
            elif choice == '10':
                self.show_statistics()
            else:
                print("❌ Invalid choice. Please try again.")

    def view_sessions(self):
        """View all AR sessions"""
        with self.app.app_context():
            try:
                sessions = ARSession.query.all()

                if not sessions:
                    print("📭 No AR sessions found.")
                    return

                print(f"\n📊 Found {len(sessions)} AR Sessions:")
                print("-" * 80)
                print(f"{'ID'"<5"} {'Session ID'"<20"} {'Room Type'"<15"} {'User ID'"<8"} {'Created'"<12"} {'Saved'"<6"}")
                print("-" * 80)

                for session in sessions:
                    created_date = session.created_at.strftime('%Y-%m-%d') if session.created_at else 'N/A'
                    print(f"{session.id:<5} {session.session_id[:18]:<20} {session.room_type:<15} {str(session.user_id or 'N/A'):<8} {created_date:<12} {str(session.is_saved):<6}")
            except Exception as e:
                print(f"❌ Error viewing sessions: {str(e)}")

    def view_model_library(self):
        """View model library"""
        with self.app.app_context():
            models = ARModelLibraryItem.query.all()

            if not models:
                print("📭 No models found in library.")
                return

            print(f"\n📚 Model Library ({len(models)} models):")
            print("-" * 100)
            print(f"{'ID'"<4"} {'Model ID'"<18"} {'Name'"<20"} {'Category'"<10"} {'Style'"<10"} {'Uses'"<6"} {'Active'"<6"}")
            print("-" * 100)

            for model in models:
                print(f"{model.id:<4} {model.model_id[:17]:<18} {model.name[:19]:<20} {model.category:<10} {model.style or 'N/A'[:9]:<10} {model.usage_count:<6} {str(model.is_active):<6}")

    def view_placed_models(self):
        """View placed models"""
        with self.app.app_context():
            placed_models = ARPlacedModel.query.all()

            if not placed_models:
                print("📭 No placed models found.")
                return

            print(f"\n📍 Placed Models ({len(placed_models)} models):")
            print("-" * 120)
            print(f"{'ID'"<4"} {'Instance ID'"<15"} {'Session ID'"<15"} {'Model Name'"<20"} {'Position'"<20"} {'Scale'"<15"}")
            print("-" * 120)

            for model in placed_models:
                pos = f"({model.position_x:.1f},{model.position_y:.1f},{model.position_z:.1f})"
                scale = f"({model.scale_x:.1f},{model.scale_y:.1f},{model.scale_z:.1f})"
                print(f"{model.id:<4} {model.instance_id[:14]:<15} {model.session_id[:14]:<15} {model.model_name[:19]:<20} {pos:<20} {scale:<15}")

    def add_model(self):
        """Add new model to library"""
        print("\n➕ Add New Model to Library")
        print("-" * 30)

        model_id = input("Model ID: ").strip()
        if not model_id:
            print("❌ Model ID is required.")
            return

        # Check if model already exists
        with self.app.app_context():
            existing = ARModelLibraryItem.query.filter_by(model_id=model_id).first()
            if existing:
                print(f"❌ Model with ID '{model_id}' already exists.")
                return

        name = input("Name: ").strip()
        category = input("Category (seating/tables/storage/lighting/beds/decor): ").strip()
        glb_url = input("GLB URL: ").strip()
        thumbnail_url = input("Thumbnail URL (optional): ").strip() or None

        width = float(input("Width: ").strip() or 1.0)
        height = float(input("Height: ").strip() or 1.0)
        depth = float(input("Depth: ").strip() or 1.0)

        description = input("Description (optional): ").strip() or None
        style = input("Style (optional): ").strip() or None

        with self.app.app_context():
            try:
                model = ARModelLibraryItem(
                    model_id=model_id,
                    name=name,
                    category=category,
                    glb_url=glb_url,
                    thumbnail_url=thumbnail_url,
                    width=width,
                    height=height,
                    depth=depth,
                    description=description,
                    style=style,
                    tags=json.dumps([]),
                    is_active=True
                )

                db.session.add(model)
                db.session.commit()

                print(f"✅ Model '{name}' added successfully!")

            except Exception as e:
                print(f"❌ Failed to add model: {str(e)}")

    def update_model(self):
        """Update existing model"""
        model_id = input("Enter Model ID to update: ").strip()

        with self.app.app_context():
            model = ARModelLibraryItem.query.filter_by(model_id=model_id).first()
            if not model:
                print(f"❌ Model '{model_id}' not found.")
                return

            print(f"\n📝 Updating Model: {model.name}")
            print(f"Current values: Name='{model.name}', Category='{model.category}'")

            new_name = input(f"New Name (current: {model.name}): ").strip()
            if new_name:
                model.name = new_name

            new_category = input(f"New Category (current: {model.category}): ").strip()
            if new_category:
                model.category = new_category

            new_glb_url = input(f"New GLB URL (current: {model.glb_url}): ").strip()
            if new_glb_url:
                model.glb_url = new_glb_url

            try:
                db.session.commit()
                print("✅ Model updated successfully!")
            except Exception as e:
                print(f"❌ Failed to update model: {str(e)}")

    def delete_model(self):
        """Delete model from library"""
        model_id = input("Enter Model ID to delete: ").strip()

        with self.app.app_context():
            model = ARModelLibraryItem.query.filter_by(model_id=model_id).first()
            if not model:
                print(f"❌ Model '{model_id}' not found.")
                return

            confirm = input(f"Are you sure you want to delete '{model.name}'? (yes/no): ").strip().lower()
            if confirm == 'yes':
                try:
                    db.session.delete(model)
                    db.session.commit()
                    print(f"✅ Model '{model.name}' deleted successfully!")
                except Exception as e:
                    print(f"❌ Failed to delete model: {str(e)}")
            else:
                print("❌ Operation cancelled.")

    def create_test_session(self):
        """Create a test AR session"""
        room_type = input("Room Type (Living Room/Bedroom/Office): ").strip() or "Living Room"
        user_id = input("User ID (optional, press Enter for none): ").strip()
        user_id = int(user_id) if user_id else None

        with self.app.app_context():
            try:
                session = ARSession(
                    session_id=f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    room_type=room_type,
                    user_id=user_id,
                    lighting_config=json.dumps({
                        'ambient': {'color': '#FFFFFF', 'intensity': 0.6},
                        'directional': {'color': '#FFFFFF', 'intensity': 0.8}
                    }),
                    environment_config=json.dumps({
                        'background_color': '#E5E5E5',
                        'floor_grid': True
                    })
                )

                db.session.add(session)
                db.session.commit()

                print(f"✅ Test session created: {session.session_id}")

            except Exception as e:
                print(f"❌ Failed to create test session: {str(e)}")

    def delete_session(self):
        """Delete AR session"""
        session_id = input("Enter Session ID to delete: ").strip()

        with self.app.app_context():
            session = ARSession.query.filter_by(session_id=session_id).first()
            if not session:
                print(f"❌ Session '{session_id}' not found.")
                return

            confirm = input(f"Are you sure you want to delete session '{session_id}'? (yes/no): ").strip().lower()
            if confirm == 'yes':
                try:
                    db.session.delete(session)
                    db.session.commit()
                    print(f"✅ Session '{session_id}' deleted successfully!")
                except Exception as e:
                    print(f"❌ Failed to delete session: {str(e)}")
            else:
                print("❌ Operation cancelled.")

    def reset_database(self):
        """Reset AR database (WARNING: deletes all data)"""
        print("⚠️ WARNING: This will delete ALL AR data!")
        confirm = input("Are you sure you want to reset the AR database? (type 'RESET' to confirm): ").strip()

        if confirm == 'RESET':
            with self.app.app_context():
                try:
                    ARPlacedModel.query.delete()
                    ARSession.query.delete()
                    ARModelLibraryItem.query.delete()
                    db.session.commit()
                    print("✅ AR Database reset successfully!")
                except Exception as e:
                    print(f"❌ Failed to reset database: {str(e)}")
        else:
            print("❌ Reset cancelled.")

    def show_statistics(self):
        """Show database statistics"""
        with self.app.app_context():
            try:
                sessions_count = ARSession.query.count()
                models_count = ARModelLibraryItem.query.count()
                placed_models_count = ARPlacedModel.query.count()

                active_sessions = ARSession.query.filter_by(is_active=True).count()
                saved_sessions = ARSession.query.filter_by(is_saved=True).count()

                print("\n📊 AR Database Statistics:")
                print("-" * 40)
                print(f"Total AR Sessions: {sessions_count}")
                print(f"Active Sessions: {active_sessions}")
                print(f"Saved Sessions: {saved_sessions}")
                print(f"Model Library Items: {models_count}")
                print(f"Placed Models: {placed_models_count}")

                if models_count > 0:
                    categories = db.session.query(ARModelLibraryItem.category, db.func.count(ARModelLibraryItem.id)).group_by(ARModelLibraryItem.category).all()
                    print("\n📂 Models by Category:")
                    for category, count in categories:
                        print(f"  {category}: {count}")
            except Exception as e:
                print(f"❌ Error getting statistics: {str(e)}")

def main():
    """Main entry point"""
    manager = ARDatabaseManager()
    manager.run()

if __name__ == "__main__":
    main()
