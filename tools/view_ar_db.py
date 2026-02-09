#!/usr/bin/env python3https://saoudrizwan.gallerycdn.vsassets.io/extensions/saoudrizwan/claude-dev/3.57.1/1770328164021/Microsoft.VisualStudio.Services.Icons.Default
"""
Quick AR Database Viewer
Simple script to view AR database contents
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app instance
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import app, db
except ImportError:
    print("❌ Could not import app. Make sure you're running from the project root.")
    sys.exit(1)
from models.ar_models import ARSession, ARPlacedModel, ARModelLibraryItem
import json

def view_database():
    """View database contents"""
    print("🔍 AR Database Contents")
    print("=" * 50)

    with app.app_context():
        try:
            # View model library
            models = ARModelLibraryItem.query.all()
            print(f"\n📚 Model Library ({len(models)} models):")
            if models:
                print("-" * 80)
                print(f"{'ID'"<4"} {'Model ID'"<18"} {'Name'"<20"} {'Category'"<12"} {'Uses'"<6"}")
                print("-" * 80)
                for model in models:
                    print(f"{model.id:<4} {model.model_id[:17]:<18} {model.name[:19]:<20} {model.category:<12} {model.usage_count:<6}")
            else:
                print("No models found in library.")

            # View AR sessions
            sessions = ARSession.query.all()
            print(f"\n📊 AR Sessions ({len(sessions)} sessions):")
            if sessions:
                print("-" * 70)
                print(f"{'ID'"<4"} {'Session ID'"<20"} {'Room Type'"<15"} {'Models'"<8"}")
                print("-" * 70)
                for session in sessions:
                    model_count = session.models.count()
                    print(f"{session.id:<4} {session.session_id[:19]:<20} {session.room_type:<15} {model_count:<8}")
            else:
                print("No AR sessions found.")

            # View placed models
            placed = ARPlacedModel.query.all()
            print(f"\n📍 Placed Models ({len(placed)} models):")
            if placed:
                print("-" * 90)
                print(f"{'ID'"<4"} {'Instance ID'"<15"} {'Model Name'"<20"} {'Session'"<15"}")
                print("-" * 90)
                for model in placed:
                    print(f"{model.id:<4} {model.instance_id[:14]:<15} {model.model_name[:19]:<20} {model.session_id[:14]:<15}")
            else:
                print("No placed models found.")

        except Exception as e:
            print(f"❌ Error viewing database: {str(e)}")
            import traceback
            traceback.print_exc()

def show_statistics():
    """Show database statistics"""
    print("\n📊 Database Statistics:")
    print("-" * 30)

    with app.app_context():
        try:
            sessions_count = ARSession.query.count()
            models_count = ARModelLibraryItem.query.count()
            placed_count = ARPlacedModel.query.count()

            print(f"AR Sessions: {sessions_count}")
            print(f"Model Library Items: {models_count}")
            print(f"Placed Models: {placed_count}")

            if models_count > 0:
                categories = db.session.query(ARModelLibraryItem.category, db.func.count(ARModelLibraryItem.id)).group_by(ARModelLibraryItem.category).all()
                print("\nModels by Category:")
                for category, count in categories:
                    print(f"  {category}: {count}")

        except Exception as e:
            print(f"❌ Error getting statistics: {str(e)}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='AR Database Viewer')
    parser.add_argument('--stats', action='store_true', help='Show only statistics')

    args = parser.parse_args()

    if args.stats:
        show_statistics()
    else:
        view_database()
        show_statistics()
