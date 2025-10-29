#!/usr/bin/env python3
"""
AR Database Initialization Script
Sets up AR session persistence tables and seeds initial data
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.ar_models import ARSession, ARPlacedModel, ARModelLibraryItem, init_ar_database, seed_model_library

def initialize_ar_database():
    """Initialize AR database tables and seed data"""
    print("🔧 Initializing AR Database...")

    with app.app_context():
        try:
            # Create all tables
            print("📋 Creating AR database tables...")
            init_ar_database(app)

            # Seed model library
            print("🌱 Seeding AR model library...")
            seed_model_library()

            print("✅ AR Database initialized successfully!")
            print("📊 Available AR models:")
            models = ARModelLibraryItem.query.all()
            for model in models:
                print(f"   • {model.name} ({model.category}) - {model.model_id}")

            return True

        except Exception as e:
            print(f"❌ AR Database initialization failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def check_ar_database():
    """Check AR database status and contents"""
    print("🔍 Checking AR Database Status...")

    with app.app_context():
        try:
            # Check if tables exist
            sessions_count = ARSession.query.count()
            models_count = ARModelLibraryItem.query.count()
            placed_models_count = ARPlacedModel.query.count()

            print("📊 Database Status:")
            print(f"   • AR Sessions: {sessions_count}")
            print(f"   • Model Library Items: {models_count}")
            print(f"   • Placed Models: {placed_models_count}")

            if models_count > 0:
                print("\n📚 Model Library Contents:")
                models = ARModelLibraryItem.query.limit(5).all()
                for model in models:
                    print(f"   • {model.name} - {model.category} ({model.usage_count} uses)")

            return True

        except Exception as e:
            print(f"❌ Database check failed: {str(e)}")
            return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='AR Database Management')
    parser.add_argument('--init', action='store_true', help='Initialize AR database')
    parser.add_argument('--check', action='store_true', help='Check AR database status')
    parser.add_argument('--reset', action='store_true', help='Reset AR database (WARNING: deletes all data)')

    args = parser.parse_args()

    if args.reset:
        print("⚠️ Resetting AR database...")
        with app.app_context():
            ARPlacedModel.query.delete()
            ARSession.query.delete()
            ARModelLibraryItem.query.delete()
            db.session.commit()
        print("✅ AR Database reset complete")

    if args.init or not any([args.init, args.check, args.reset]):
        success = initialize_ar_database()
        if success:
            print("\n🎉 AR Database ready for use!")
        else:
            sys.exit(1)

    if args.check:
        check_ar_database()
